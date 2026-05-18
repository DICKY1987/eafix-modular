/*
   MT4_CommTest.mq4
   ─────────────────────────────────────────────────────────────────────────
   EAFIX-Modular — MT4 ↔ Python Communication Test (MT4 side)

   Run this as a SCRIPT (not an EA) by dragging it onto any chart.
   It runs once and exits. Results appear in the Experts tab journal.

   This script tests three channels:

     Test A — HTTP WebRequest (MT4 → Python)
       Sends GET http://127.0.0.1:5001/comms-test/ping
       Expects JSON with {"status":"ok","test_id":"..."}

     Test B — Signal file read (Python → MT4)
       Reads the JSONL written by the Python script from the
       MT4 common files directory (Terminal\Common\Files\eafix_test\signal.jsonl)

     Test C — Feedback file write (MT4 → Python)
       Writes a CSV feedback file to the same common directory so
       the Python script can detect and confirm receipt.

   Prerequisites
   ─────────────
   1. Python script is already running (python python_comms_test.py)
   2. MT4: Tools → Options → Expert Advisors →
          "Allow WebRequest for listed URL" → http://127.0.0.1:5001
   3. Compile this file (F7) and drag onto any chart as a Script.

   Configuration
   ─────────────
   Adjust the inputs below if you changed defaults in the Python script.
*/

#property strict
#property show_inputs

// ── Inputs ──────────────────────────────────────────────────────────────────
extern string PythonBaseURL   = "http://192.168.1.63:5003";   // Python HTTP server (comms test)
extern string SignalSubDir    = "eafix_test";                // Sub-folder in Common\Files
extern int    HttpTimeoutMs   = 10000;                       // WebRequest timeout (ms)

// ── Constants ────────────────────────────────────────────────────────────────
#define SIGNAL_FILENAME   "signal.jsonl"
#define FEEDBACK_FILENAME "feedback.csv"

// ── Helpers ──────────────────────────────────────────────────────────────────
void Log(string prefix, string msg)
{
   string line = "[CommTest] " + prefix + " " + msg;
   Print(line);
   Comment(line);   // show on chart briefly
}

void Pass(string test, string detail = "") { Log("✅ PASS", test + (detail == "" ? "" : " | " + detail)); }
void Fail(string test, string detail = "") { Log("❌ FAIL", test + (detail == "" ? "" : " | " + detail)); }
void Info(string msg)                      { Log("ℹ ", msg); }


// ── Test A — HTTP WebRequest (MT4 → Python) ──────────────────────────────────
bool TestA_HTTP()
{
   string url     = PythonBaseURL + "/comms-test/ping";
   string headers = "Accept: application/json\r\n";
   char   postData[];  // empty (GET)
   char   response[];
   string responseHeaders;

   Info("Test A: Sending GET " + url);

   int result = WebRequest("GET", url, headers, HttpTimeoutMs, postData, response, responseHeaders);

   if(result == 200)
   {
      string body = CharArrayToString(response, 0, WHOLE_ARRAY, CP_UTF8);
      Pass("Test A — HTTP WebRequest", "HTTP 200. Body: " + StringSubstr(body, 0, 120));
      return true;
   }
   else if(result == -1)
   {
      int err = GetLastError();
      Fail("Test A — HTTP WebRequest",
           "WebRequest returned -1. GetLastError=" + IntegerToString(err) +
           " | URL=" + url +
           " | (4032=not whitelisted, 5=network err, 4060=connect failed)");
      return false;
   }
   else
   {
      Fail("Test A — HTTP WebRequest", "HTTP " + IntegerToString(result));
      return false;
   }
}


// ── Test B — Read signal JSONL (Python → MT4) ────────────────────────────────
bool TestB_ReadSignal()
{
   // FILE_COMMON reads from Terminal\Common\Files\
   string filePath = SignalSubDir + "\\" + SIGNAL_FILENAME;

   Info("Test B: Reading " + filePath + " (FILE_COMMON)");

   int fh = FileOpen(filePath, FILE_READ | FILE_TXT | FILE_COMMON, '\n');
   if(fh == INVALID_HANDLE)
   {
      Fail("Test B — Signal file read",
           "Cannot open " + filePath + " (error " + IntegerToString(GetLastError()) + "). "
           + "Is the Python script running and has it written the signal?");
      return false;
   }

   string line = "";
   while(!FileIsEnding(fh))
   {
      line = FileReadString(fh);
      if(StringLen(line) > 0) break;
   }
   FileClose(fh);

   if(StringLen(line) == 0)
   {
      Fail("Test B — Signal file read", "File exists but is empty.");
      return false;
   }

   // Quick parse: look for test_run_id and message keys
   bool hasId  = StringFind(line, "COMMS-") >= 0;
   bool hasMsg = StringFind(line, "COMMS_TEST") >= 0;

   if(hasId && hasMsg)
   {
      Pass("Test B — Signal file read", "Contents: " + StringSubstr(line, 0, 120));
      return true;
   }
   else
   {
      Fail("Test B — Signal file read", "File found but content unexpected: " + StringSubstr(line, 0, 80));
      return false;
   }
}


// ── Test C — Write feedback CSV (MT4 → Python) ───────────────────────────────
bool TestC_WriteFeedback()
{
   string filePath = SignalSubDir + "\\" + FEEDBACK_FILENAME;
   string ts       = TimeToString(TimeCurrent(), TIME_DATE | TIME_MINUTES | TIME_SECONDS);
   string content  = "status,source,symbol,ts_broker\n"
                   + "ok,MT4_CommTest,EURUSD," + ts + "\n";

   Info("Test C: Writing feedback → " + filePath + " (FILE_COMMON)");

   // Atomic write: write to .tmp then rename
   string tmpPath = SignalSubDir + "\\" + "feedback.tmp";

   // Ensure directory exists (MT4 creates it if needed with FILE_COMMON)
   int fh = FileOpen(tmpPath, FILE_WRITE | FILE_TXT | FILE_COMMON);
   if(fh == INVALID_HANDLE)
   {
      Fail("Test C — Feedback file write",
           "Cannot open tmp file for writing (error " + IntegerToString(GetLastError()) + "). "
           + "Does Terminal\\Common\\Files\\" + SignalSubDir + " exist?");
      return false;
   }

   FileWriteString(fh, content);
   FileClose(fh);

   // Rename tmp → final (atomic)
   if(FileMove(tmpPath, FILE_COMMON, filePath, FILE_COMMON | FILE_REWRITE))
   {
      Pass("Test C — Feedback file write", "feedback.csv written. Python should detect it now.");
      return true;
   }
   else
   {
      // FileMove may not be available in all builds — fall back to direct write
      int fh2 = FileOpen(filePath, FILE_WRITE | FILE_TXT | FILE_COMMON);
      if(fh2 == INVALID_HANDLE)
      {
         Fail("Test C — Feedback file write",
              "Rename failed and fallback write failed (error " + IntegerToString(GetLastError()) + ").");
         return false;
      }
      FileWriteString(fh2, content);
      FileClose(fh2);
      Pass("Test C — Feedback file write (fallback direct write)", filePath);
      return true;
   }
}


// ── Script entry point ───────────────────────────────────────────────────────
void OnStart()
{
   Print("═══════════════════════════════════════════════════════════");
   Print("  EAFIX-Modular — MT4 ↔ Python Communication Test");
   Print("  " + TimeToString(TimeCurrent(), TIME_DATE | TIME_MINUTES | TIME_SECONDS));
   Print("═══════════════════════════════════════════════════════════");

   bool passA = TestA_HTTP();
   bool passB = TestB_ReadSignal();
   bool passC = TestC_WriteFeedback();

   Print("───────────────────────────────────────────────────────────");
   Print("  RESULTS");
   Print("  Test A (HTTP WebRequest) : " + (passA ? "PASS ✅" : "FAIL ❌"));
   Print("  Test B (Signal file read): " + (passB ? "PASS ✅" : "FAIL ❌"));
   Print("  Test C (Feedback write)  : " + (passC ? "PASS ✅" : "FAIL ❌"));
   Print("═══════════════════════════════════════════════════════════");

   if(passA && passB && passC)
      Print("  🎉  ALL TESTS PASSED — MT4 ↔ Python comms confirmed!");
   else
      Print("  ⚠️   Some tests failed. See entries above for details.");

   Print("═══════════════════════════════════════════════════════════");

   Comment("CommTest done. Check Experts tab for results.");
   Sleep(5000);
   Comment("");
}
