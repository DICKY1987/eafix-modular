Yes, I can create the files for the complete socket communication system, including the MQL4 Expert Advisor, the C++ DLL project, and the Python server components. I will wrap them in the **PowerShell Universal Dropper Standard** format, as per the mandatory project rules.

This will ensure all necessary files are created with the correct directory structure and UTF-8 encoding, along with clear instructions for deployment.

Given the comprehensive nature of this system, I will provide the files in several logical blocks to ensure clarity and avoid excessively long output for a single response.

Here's the plan:

**Part 1: MT4 Files (EA and Includes)**

* 10ParameterEA.mq4 (Main EA)  
* CommunicationManager.mqh (Manages communication hierarchy)  
* NamedPipeManager.mqh (Named Pipe abstraction)  
* FileManager.mqh (Enhanced CSV handling)  
* TradingCore.mqh (Core trading logic \- placeholder for now)

**Part 2: C++ DLL Bridge Files**

* SocketBridge.cpp (DLL implementation)  
* SocketBridge.h (DLL header)  
* SocketBridge.def (Module definition file)  
* build\_dll.bat (Simple build script)

**Part 3: Python Server Files**

* trading\_server.py (Main Python server)  
* signal\_generator.py (Signal generation placeholder)  
* message\_broker.py (Message routing placeholder)  
* database\_manager.py (Database ops placeholder)  
* config\_manager.py (Config management)  
* logger\_setup.py (Centralized logging)  
* monitoring.py (System health monitoring placeholder)  
* requirements.txt (Python dependencies)

**Part 4: Configuration and Database Files**

* all\_10\_parameter\_sets.csv (EA Parameter Sets)  
* signal\_id\_mapping.csv (Signal to Parameter Set mapping)  
* reentry\_close\_result\_mapping.csv (Close Result to Reentry Parameter Set mapping)  
* current\_signal.csv (Simulated incoming signal)  
* server\_config.yaml (Python server config)  
* logging\_config.yaml (Python logging config)  
* system\_config.yaml (Global system config)  
* trading\_schema.sql (Database schema)  
* initial\_data.sql (Initial database data)  
* EURUSD.yaml (Example per-pair config)

**Part 5: Deployment & Utility Scripts**

* deploy\_system.ps1 (Main deployment script)  
* start\_python\_server.bat (Python server launcher)  
* compile\_ea.ps1 (Helper to compile EAs)

---

Let's start with **Part 1: MT4 Files (EA and Includes)**. Please copy and paste the following into your PowerShell terminal.

PowerShell

$ErrorActionPreference \= "Stop"  
Write-Host "CREATING MT4 EXPERT ADVISOR AND INCLUDE FILES..." \-ForegroundColor Green

\# Define project base path relative to MT4 terminal data folder  
\# This assumes the dropper is run where the user wants the MT4 components for deployment.  
\# For Richard Wilks' setup, this would typically be within the TradingSystem project root  
\# located at C:\\Users\\Richard Wilks\\TradingSystem.  
\# We'll put MQ4 files in a 'Source\\MQL4' subfolder for compilation  
\# And then the MQL4\\Files for CSVs are relative to the MT4 data folder.

\# IMPORTANT: Adjust $mt4TerminalPath to your actual MT4 terminal's data folder ID.  
\# As per mt4\_paths\_reference.md, for Richard Wilks, this is F2262CFAFF47C27887389DAB2852351A  
$mt4TerminalID \= "F2262CFAFF47C27887389DAB2852351A"  
$mt4TerminalPath \= Join-Path $env:APPDATA "MetaQuotes\\Terminal\\$mt4TerminalID"  
$mql4Path \= Join-Path $mt4TerminalPath "MQL4"  
$mql4ExpertsPath \= Join-Path $mql4Path "Experts"  
$mql4IncludePath \= Join-Path $mql4Path "Include"  
$mql4LibrariesPath \= Join-Path $mql4Path "Libraries" \# For DLL  
$mql4FilesPath \= Join-Path $mql4Path "Files" \# For CSVs

\# Define source code paths for organization before deployment  
$projectSourceRoot \= "C:\\Users\\Richard Wilks\\TradingSystem\\Source" \# The development root for MQ4 files  
$eaSourcePath \= Join-Path $projectSourceRoot "MQL4\\Experts"  
$includeSourcePath \= Join-Path $projectSourceRoot "MQL4\\Include"

\# Create directory structure within the user's TradingSystem project  
$projectDirectories \= @(  
    $projectSourceRoot,  
    $eaSourcePath,  
    $includeSourcePath,  
    Join-Path $projectSourceRoot "MQL4\\Libraries",  
    Join-Path $projectSourceRoot "MQL4\\Files" \# for initial CSVs during dev  
)

foreach ($dir in $projectDirectories) {  
    New-Item \-ItemType Directory \-Path $dir \-Force | Out-Null  
    Write-Host "📁 Created project source dir: $dir" \-ForegroundColor Cyan  
}

\# Create necessary MT4 data folder directories if they don't exist  
$mt4DeployDirectories \= @(  
    $mql4ExpertsPath,  
    $mql4IncludePath,  
    $mql4LibrariesPath,  
    $mql4FilesPath  
)

foreach ($dir in $mt4DeployDirectories) {  
    New-Item \-ItemType Directory \-Path $dir \-Force | Out-Null  
    Write-Host "📁 Ensured MT4 deploy dir: $dir" \-ForegroundColor DarkCyan  
}

Write-Host "NOTE: MQL4 files will be created in the project source path for development." \-ForegroundColor Yellow  
Write-Host "You will need to manually compile them in MetaEditor or use a separate build script." \-ForegroundColor Yellow  
Write-Host "The CSV files will be placed directly into the MT4 data folder's MQL4\\Files directory." \-ForegroundColor Yellow

\# \--- File Contents \---

\# 10ParameterEA.mq4 \- Main Expert Advisor  
$eaContent \= @'  
//+------------------------------------------------------------------+  
//|                                                10ParameterEA.mq4 |  
//|                                                     Richard Wilks|  
//|                                     https://www.linkedin.com/in/richard-wilks/|  
//+------------------------------------------------------------------+  
\#property copyright "Richard Wilks"  
\#property link      "https://www.linkedin.com/in/richard-wilks/"  
\#property version   "1.00"  
\#property strict

// \--- Includes \---  
\#include \<CommunicationManager.mqh\> // Manages communication hierarchy  
\#include \<TradingCore.mqh\>          // Placeholder for core trading logic

// \--- Global Variables and Constants \---  
\#define MT4\_FILES\_PATH "" // Base path for FileOpen in MQL4 is MQL4/Files. No need for full path here.

// Enumeration for trade close results  
enum ENUM\_CLOSE\_RESULT  
{  
    CLOSE\_RESULT\_SL\_HIT \= 1,  
    CLOSE\_RESULT\_PARTIAL\_LOSS \= 2,  
    CLOSE\_RESULT\_BREAKEVEN \= 3,  
    CLOSE\_RESULT\_PARTIAL\_PROFIT \= 4,  
    CLOSE\_RESULT\_TP\_HIT \= 5,  
    CLOSE\_RESULT\_BEYOND\_TP \= 6  
};

// \--- Structures for Parameters \---  
// Structure for individual parameter sets  
struct t\_ParameterSet  
{  
    string  set\_id;  
    double  risk\_percent;  
    double  lot\_size;  
    int     stop\_loss;    // in points  
    int     take\_profit;  // in points  
    int     slippage;  
    int     magic\_base;  
};

// Structure for Signal ID mapping  
struct t\_SignalMapping  
{  
    string  signal\_id;  
    string  parameter\_set\_id;  
    string  description;  
    int     trade\_direction; // OP\_BUY or OP\_SELL, will be determined from signal  
};

// Structure for Close Result mapping  
struct t\_CloseResultMapping  
{  
    int     close\_result\_code; // Corresponds to ENUM\_CLOSE\_RESULT  
    string  parameter\_set\_id;  
    string  description;  
};

// Structure for incoming signals (from Python/CSV)  
struct SignalData {  
    string id;  
    string symbol;  
    string direction; // "BUY" or "SELL"  
    double confidence;  
    datetime timestamp;  
    string strategy\_id;  
    string metadata; // JSON string  
    string parameter\_set\_override; // Optional: parameter\_set from socket message  
};

// \--- Global Arrays to store loaded configurations \---  
t\_ParameterSet      ParameterSets\[10\];  
t\_SignalMapping     SignalMappings\[4\];  
t\_CloseResultMapping CloseResultMappings\[6\];

// \--- Global EA State Variables \---  
bool                initialTradeOpen \= false;  
bool                reentryTradeOpen \= false;  
long                currentInitialTicket \= 0;  
long                currentReentryTicket \= 0;  
string              currentSignalID \= ""; // Stores the signal ID for the current cycle  
int                 tradeResult \= 0;    // Stores the result of the initial trade  
datetime            g\_last\_csv\_check \= 0; // For CSV monitoring optimization

// \--- External Variables (Inputs) \---  
// These inputs specify the CSV files for fallback communication and parameter loading.  
// They are defined as external so they can be changed from the MT4 EA properties window.  
extern string   ParameterSetFile \= "all\_10\_parameter\_sets.csv";  
extern string   SignalMappingFile \= "signal\_id\_mapping.csv";  
extern string   CloseResultMappingFile \= "reentry\_close\_result\_mapping.csv";  
extern string   InputSignalFile \= "current\_signal.csv"; // File to simulate incoming signals  
extern string   ResponseFile \= "EURUSD\_responses.csv"; // File for EA to write responses  
extern int      CheckSignalIntervalSeconds \= 1; // How often to check for a new signal (increased for socket polling)

// \--- Communication Globals (Managed by CommunicationManager.mqh) \---  
int                 g\_socket\_handle \= \-1;  
bool                g\_socket\_connected \= false;  
datetime            g\_last\_heartbeat \= 0;  
datetime            g\_last\_connection\_attempt \= 0;  
int                 g\_connection\_failures \= 0;  
enum CommunicationMode g\_current\_mode \= MODE\_SOCKET; // Primary communication mode  
string              g\_receive\_buffer \= "";  
string              g\_processed\_signals\[\]; // Track processed signal IDs to prevent duplicates

//+------------------------------------------------------------------+  
//| Function to load all 10 parameter sets from CSV                 |  
//+------------------------------------------------------------------+  
void LoadParameterSets()  
{  
    int file\_handle;  
    string file\_path \= MT4\_FILES\_PATH \+ ParameterSetFile;  
    file\_handle \= FileOpen(file\_path, FILE\_CSV | FILE\_READ, ',');

    if (file\_handle \< 0\)  
    {  
        Print("Error opening parameter sets file: ", file\_path, " Error: ", GetLastError());  
        return;  
    }

    Print("Loading parameter sets from: ", file\_path);

    // Skip header row  
    FileReadString(file\_handle);

    int i \= 0;  
    while (\!FileIsEOF(file\_handle) && i \< 10\)  
    {  
        string line \= FileReadString(file\_handle);  
        string parts\[\];  
        StringSplit(line, ',', parts);

        if (ArraySize(parts) \>= 7\)  
        {  
            ParameterSets\[i\].set\_id         \= StringTrim(parts\[0\]);  
            ParameterSets\[i\].risk\_percent   \= StringToDouble(StringTrim(parts\[1\]));  
            ParameterSets\[i\].lot\_size       \= StringToDouble(StringTrim(parts\[2\]));  
            ParameterSets\[i\].stop\_loss      \= StringToInteger(StringTrim(parts\[3\]));  
            ParameterSets\[i\].take\_profit    \= StringToInteger(StringTrim(parts\[4\]));  
            ParameterSets\[i\].slippage       \= StringToInteger(StringTrim(parts\[5\]));  
            ParameterSets\[i\].magic\_base     \= StringToInteger(StringTrim(parts\[6\]));  
            Print("Loaded ParameterSet ", i, ": ", ParameterSets\[i\].set\_id,  
                  ", Risk: ", ParameterSets\[i\].risk\_percent,  
                  ", Lot: ", ParameterSets\[i\].lot\_size,  
                  ", SL: ", ParameterSets\[i\].stop\_loss,  
                  ", TP: ", ParameterSets\[i\].take\_profit,  
                  ", Magic: ", ParameterSets\[i\].magic\_base);  
            i++;  
        } else {  
            Print("Warning: Malformed line in parameter sets CSV: ", line);  
        }  
    }  
    FileClose(file\_handle);  
    if (i \< 10\) Print("Warning: Only ", i, " parameter sets loaded. Expected 10.");  
}

//+------------------------------------------------------------------+  
//| Function to load signal ID mappings from CSV                    |  
//+------------------------------------------------------------------+  
void LoadSignalMappings()  
{  
    int file\_handle;  
    string file\_path \= MT4\_FILES\_PATH \+ SignalMappingFile;  
    file\_handle \= FileOpen(file\_path, FILE\_CSV | FILE\_READ, ',');

    if (file\_handle \< 0\)  
    {  
        Print("Error opening signal mappings file: ", file\_path, " Error: ", GetLastError());  
        return;  
    }

    Print("Loading signal mappings from: ", file\_path);

    // Skip header row  
    FileReadString(file\_handle);

    int i \= 0;  
    while (\!FileIsEOF(file\_handle) && i \< 4\)  
    {  
        string line \= FileReadString(file\_handle);  
        string parts\[\];  
        StringSplit(line, ',', parts);

        if (ArraySize(parts) \>= 3\)  
        {  
            SignalMappings\[i\].signal\_id         \= StringTrim(parts\[0\]);  
            SignalMappings\[i\].parameter\_set\_id  \= StringTrim(parts\[1\]);  
            SignalMappings\[i\].description       \= StringTrim(parts\[2\]);  
            SignalMappings\[i\].trade\_direction   \= 0; // Placeholder, to be determined from signal message  
            Print("Loaded SignalMapping ", i, ": ", SignalMappings\[i\].signal\_id,  
                  " \-\> Set: ", SignalMappings\[i\].parameter\_set\_id);  
            i++;  
        } else {  
            Print("Warning: Malformed line in signal mappings CSV: ", line);  
        }  
    }  
    FileClose(file\_handle);  
    if (i \< 4\) Print("Warning: Only ", i, " signal mappings loaded. Expected 4.");  
}

//+------------------------------------------------------------------+  
//| Function to load close result mappings from CSV                 |  
//+------------------------------------------------------------------+  
void LoadCloseResultMappings()  
{  
    int file\_handle;  
    string file\_path \= MT4\_FILES\_PATH \+ CloseResultMappingFile;  
    file\_handle \= FileOpen(file\_path, FILE\_CSV | FILE\_READ, ',');

    if (file\_handle \< 0\)  
    {  
        Print("Error opening close result mappings file: ", file\_path, " Error: ", GetLastError());  
        return;  
    }

    Print("Loading close result mappings from: ", file\_path);

    // Skip header row  
    FileReadString(file\_handle);

    int i \= 0;  
    while (\!FileIsEOF(file\_handle) && i \< 6\)  
    {  
        string line \= FileReadString(file\_handle);  
        string parts\[\];  
        StringSplit(line, ',', parts);

        if (ArraySize(parts) \>= 3\)  
        {  
            CloseResultMappings\[i\].close\_result\_code    \= StringToInteger(StringTrim(parts\[0\]));  
            CloseResultMappings\[i\].parameter\_set\_id     \= StringTrim(parts\[1\]);  
            CloseResultMappings\[i\].description          \= StringTrim(parts\[2\]);  
            Print("Loaded CloseResultMapping ", i, ": Result: ", CloseResultMappings\[i\].close\_result\_code,  
                  " \-\> Set: ", CloseResultMappings\[i\].parameter\_set\_id);  
            i++;  
        } else {  
            Print("Warning: Malformed line in close result mappings CSV: ", line);  
        }  
    }  
    FileClose(file\_handle);  
    if (i \< 6\) Print("Warning: Only ", i, " close result mappings loaded. Expected 6.");  
}

//+------------------------------------------------------------------+  
//| Expert initialization function                                   |  
//+------------------------------------------------------------------+  
int OnInit()  
{  
    // Load all configurations at EA startup  
    LoadParameterSets();  
    LoadSignalMappings();  
    LoadCloseResultMappings();

    // Initialize communication bridge (Socket \-\> Pipe \-\> CSV fallback)  
    if (\!InitializeCommunicationManager()) { // This function is in CommunicationManager.mqh  
        Print("CRITICAL: All communication initialization failed. EA will run in CSV-only mode.");  
        g\_current\_mode \= MODE\_FILE;  
    }

    // Register EA with Python server (done via CommunicationManager if socket/pipe successful)

    Print("EA Initialized. Current Communication Mode: ", EnumToString(g\_current\_mode));

    return(INIT\_SUCCEEDED);  
}

//+------------------------------------------------------------------+  
//| Expert deinitialization function                                 |  
//+------------------------------------------------------------------+  
void OnDeinit(const int reason)  
{  
    // Clean up communication manager connections  
    DeinitializeCommunicationManager();  
    Print("EA Deinitialized.");  
}

//+------------------------------------------------------------------+  
//| Expert tick function                                             |  
//+------------------------------------------------------------------+  
void OnTick()  
{  
    static datetime lastSignalCheckTime \= 0;

    // Maintain communication connection heartbeat and try recovery  
    MaintainCommunicationManager();  
      
    // Check for new signals based on interval  
    if (TimeCurrent() \- lastSignalCheckTime \>= CheckSignalIntervalSeconds)  
    {  
        CheckForSignalsHierarchical(); // This function is in CommunicationManager.mqh  
        lastSignalCheckTime \= TimeCurrent();  
    }

    // Monitor existing positions (placeholder \- will be in TradingCore.mqh)  
    // MonitorExistingPositions();  
}

//+------------------------------------------------------------------+  
//| CUSTOMIZABLE FUNCTION \- This is where trading logic goes         |  
//| Called from CommunicationManager after a signal is received      |  
//+------------------------------------------------------------------+  
// This function needs to be declared here but its actual implementation  
// (like trade execution, etc.) will be handled in TradingCore.mqh or a  
// dedicated trading logic function.  
void ProcessSignal(SignalData& signal)  
{  
    Print("Processing signal: ID=", signal.id, ", Symbol=", signal.symbol,  
          ", Direction=", signal.direction, ", Confidence=", signal.confidence,  
          ", Strategy=", signal.strategy\_id, ", SetOverride=", signal.parameter\_set\_override);

    // \--- Signal Validation (as per signal\_format\_examples.md) \---  
    // Check 1: Correct symbol?  
    if (signal.symbol \!= Symbol())  
    {  
        Print("⚠️ Ignoring signal for different pair: ", signal.symbol, " (Current chart: ", Symbol(), ")");  
        // Write a response back indicating it was ignored  
        SendResponseToPython(signal.id, "IGNORED", 0.0, "Wrong symbol", 0.0, 0, 0, 0);  
        return; // IGNORED  
    }

    // Check 2: Fresh signal? (within 5 minutes)  
    if (TimeCurrent() \- signal.timestamp \> 300\) // 300 seconds \= 5 minutes  
    {  
        Print("⏰ Ignoring stale signal: ", signal.id, " (Age: ", (TimeCurrent() \- signal.timestamp), " seconds)");  
        SendResponseToPython(signal.id, "IGNORED", 0.0, "Stale signal", 0.0, 0, 0, 0);  
        return; // IGNORED \- TOO OLD  
    }

    // Check 3: High enough confidence?  
    if (signal.confidence \< 0.6) // 0.6 threshold  
    {  
        Print("📉 Rejecting signal due to low confidence: ", signal.id, " (Confidence: ", signal.confidence, ")");  
        SendResponseToPython(signal.id, "REJECTED", 0.0, "Low confidence", 0.0, 0, 0, 0);  
        return; // REJECTED  
    }

    // Check 4: Valid direction  
    int tradeDirection;  
    if (StringUpper(signal.direction) \== "BUY") {  
        tradeDirection \= OP\_BUY;  
    } else if (StringUpper(signal.direction) \== "SELL") {  
        tradeDirection \= OP\_SELL;  
    } else {  
        Print("❌ Invalid trade direction in signal: ", signal.id, " (Direction: ", signal.direction, ")");  
        SendResponseToPython(signal.id, "REJECTED", 0.0, "Invalid direction", 0.0, 0, 0, 0);  
        return; // REJECTED  
    }

    // Check 5: Duplicate Signal Prevention  
    if (IsSignalAlreadyProcessed(signal.id)) {  
        Print("🚫 Duplicate signal received, ignoring: ", signal.id);  
        return; // IGNORED \- DUPLICATE  
    }  
    // Add signal ID to processed list  
    ArrayAdd(g\_processed\_signals, signal.id);  
      
    // All checks passed \- proceed to trade execution logic  
    // Now, determine which parameter set to use for initial trade  
    string parameterSetToUse \= "";  
    if (StringLen(signal.parameter\_set\_override) \> 0\) { // If parameter\_set is provided in socket message  
        parameterSetToUse \= signal.parameter\_set\_override;  
        Print("Using overridden parameter set: ", parameterSetToUse);  
    } else { // Fallback to CSV mapping  
        for (int i \= 0; i \< ArraySize(SignalMappings); i++) {  
            if (SignalMappings\[i\].signal\_id \== signal.strategy\_id) { // Use strategy\_id for mapping  
                parameterSetToUse \= SignalMappings\[i\].parameter\_set\_id;  
                Print("Using mapped parameter set: ", parameterSetToUse, " for strategy: ", signal.strategy\_id);  
                break;  
            }  
        }  
    }

    if (StringLen(parameterSetToUse) \== 0\) {  
        Print("Error: No parameter set found for strategy ID or override: ", signal.strategy\_id, ". Rejecting trade.");  
        SendResponseToPython(signal.id, "REJECTED", 0.0, "No parameter set found", 0.0, 0, 0, 0);  
        return;  
    }

    t\_ParameterSet currentParams;  
    bool paramsFound \= false;  
    for (int i \= 0; i \< ArraySize(ParameterSets); i++) {  
        if (ParameterSets\[i\].set\_id \== parameterSetToUse) {  
            currentParams \= ParameterSets\[i\];  
            paramsFound \= true;  
            break;  
        }  
    }

    if (\!paramsFound) {  
        Print("Error: Parameter set '", parameterSetToUse, "' not found in loaded configurations. Rejecting trade.");  
        SendResponseToPython(signal.id, "REJECTED", 0.0, "Parameter set not configured", 0.0, 0, 0, 0);  
        return;  
    }  
      
    // Execute the initial trade using the determined parameters  
    Print("Executing initial trade for ", signal.symbol, " ", signal.direction,  
          " with parameters from set: ", currentParams.set\_id);  
      
    // This function (ExecuteInitialTrade) will be implemented in TradingCore.mqh  
    // For now, it's a placeholder call.  
    currentInitialTicket \= ExecuteTrade(signal.symbol, tradeDirection, currentParams.lot\_size,  
                                       currentParams.stop\_loss, currentParams.take\_profit,  
                                       currentParams.slippage, currentParams.magic\_base);

    if (currentInitialTicket \> 0\) {  
        initialTradeOpen \= true;  
        currentSignalID \= signal.id; // Store signal ID for potential reentry logic  
        Print("Initial trade opened successfully\! Ticket: ", currentInitialTicket);  
        SendResponseToPython(signal.id, "EXECUTED", Ask, "Order ticket: " \+ (string)currentInitialTicket, currentParams.lot\_size, currentParams.magic\_base, currentParams.slippage, 0);  
    } else {  
        Print("Failed to open initial trade. Error: ", GetLastError());  
        SendResponseToPython(signal.id, "FAILED", 0.0, "OrderSend failed: " \+ ErrorDescription(GetLastError()), currentParams.lot\_size, currentParams.magic\_base, currentParams.slippage, GetLastError());  
    }  
}

// \--- Placeholder functions, actual implementation in TradingCore.mqh or CommunicationManager.mqh \---  
// These functions are called in 10ParameterEA.mq4 but defined in other .mqh files.  
// They are just declarations here for the compiler.  
bool InitializeCommunicationManager();  
void DeinitializeCommunicationManager();  
void MaintainCommunicationManager();  
bool CheckSocketForSignals(SignalData& signal);  
bool CheckNamedPipeForSignals(SignalData& signal);  
void CheckCSVForSignals(); // This function will process CSV and call ProcessSignal

// Function to send responses back to Python (via active communication channel)  
void SendResponseToPython(string signal\_id, string status, double execution\_price, string error\_message, double lot\_size, int magic\_number, int slippage, int mt4\_error\_code);

// Trading functions (placeholder for TradingCore.mqh)  
long ExecuteTrade(string symbol, int direction, double lots, int sl\_points, int tp\_points, int slippage, int magic);  
void MonitorExistingPositions(); // To analyze trade close reason for reentry

// CSV Signal Reading specific to 10ParameterEA, called by CheckCSVForSignals()  
bool ReadCSVSignal(SignalData& signal);  
void ClearCSVSignalFile();  
bool IsSignalAlreadyProcessed(string signal\_id); // Declared above, implemented here for conceptual clarity.  
void AddProcessedSignal(string signal\_id); // To add a signal to the processed list

//+------------------------------------------------------------------+  
//| Implementations for CSV specific signal handling here (for now)  |  
//| These will be primarily used when g\_current\_mode \== MODE\_FILE    |  
//+------------------------------------------------------------------+

// This function processes the current\_signal.csv for the CSV fallback mode.  
// It will be called by CheckCSVForSignals() in CommunicationManager.mqh  
bool ReadCSVSignal(SignalData& signal) {  
    int file\_handle \= FileOpen(MT4\_FILES\_PATH \+ InputSignalFile, FILE\_READ|FILE\_CSV, ',');  
    if (file\_handle \< 0\) {  
        Print("Error opening input signal file: ", MT4\_FILES\_PATH \+ InputSignalFile, " Error: ", GetLastError());  
        return false;  
    }

    // Skip header line  
    FileReadString(file\_handle);

    if (\!FileIsEOF(file\_handle)) {  
        string line \= FileReadString(file\_handle);  
        string parts\[\];  
        // Assuming the format: id,symbol,direction,confidence,timestamp,strategy\_id,metadata  
        // For current\_signal.csv, it's simplified to signal\_id,trade\_direction for demo  
        // For full CSV signal format, refer to signal\_format\_examples.md  
        StringSplit(line, ',', parts);

        if (ArraySize(parts) \>= 6\) { // Full signal format from signal\_format\_examples.md  
            signal.id \= StringTrim(parts\[0\]);  
            signal.symbol \= StringTrim(parts\[1\]);  
            signal.direction \= StringTrim(parts\[2\]);  
            signal.confidence \= StringToDouble(StringTrim(parts\[3\]));  
            signal.timestamp \= StrToTime(StringTrim(parts\[4\]));  
            signal.strategy\_id \= StringTrim(parts\[5\]);  
            if (ArraySize(parts) \>= 7\) signal.metadata \= StringTrim(parts\[6\]); // Optional metadata  
            signal.parameter\_set\_override \= ""; // Not available via CSV directly unless added  
            FileClose(file\_handle);  
            return true;  
        } else if (ArraySize(parts) \>= 2\) { // Simplified current\_signal.csv format (for demo)  
            // This is a simplified demo signal. In a real system, current\_signal.csv  
            // would hold the full signal\_format\_examples.md structure.  
            signal.id \= StringTrim(parts\[0\]);  
            signal.direction \= StringTrim(parts\[1\]);  
            signal.symbol \= Symbol(); // Assume current chart symbol for simplified demo  
            signal.confidence \= 1.0; // Assume high confidence for simplified demo  
            signal.timestamp \= TimeCurrent();  
            signal.strategy\_id \= signal.id; // Use signal\_id as strategy\_id for simplified demo  
            signal.metadata \= "{}";  
            signal.parameter\_set\_override \= "";  
            FileClose(file\_handle);  
            return true;  
        }  
    }  
    FileClose(file\_handle);  
    return false;  
}

// Clears the current\_signal.csv after it's processed.  
// This is crucial for preventing the EA from re-processing the same signal in file mode.  
void ClearCSVSignalFile() {  
    int file\_handle \= FileOpen(MT4\_FILES\_PATH \+ InputSignalFile, FILE\_WRITE, ','); // Open in write mode clears content  
    if (file\_handle \< 0\) {  
        Print("Error clearing input signal file: ", MT4\_FILES\_PATH \+ InputSignalFile, " Error: ", GetLastError());  
    } else {  
        FileClose(file\_handle);  
        Print("Input signal file cleared: ", MT4\_FILES\_PATH \+ InputSignalFile);  
    }  
}

// Global list to store processed signal IDs to prevent duplicates  
string g\_processed\_signals\_list\[\];

// Function to check if a signal has already been processed  
bool IsSignalAlreadyProcessed(string signal\_id) {  
    for (int i \= 0; i \< ArraySize(g\_processed\_signals\_list); i++) {  
        if (g\_processed\_signals\_list\[i\] \== signal\_id) {  
            return true;  
        }  
    }  
    return false;  
}

// Function to add a signal to the processed list  
void AddProcessedSignal(string signal\_id) {  
    if (\!IsSignalAlreadyProcessed(signal\_id)) {  
        ArrayResize(g\_processed\_signals\_list, ArraySize(g\_processed\_signals\_list) \+ 1);  
        g\_processed\_signals\_list\[ArraySize(g\_processed\_signals\_list) \- 1\] \= signal\_id;  
        // Keep the list to a reasonable size to prevent excessive memory usage  
        if (ArraySize(g\_processed\_signals\_list) \> 1000\) { // Limit to last 1000 signals  
            ArrayRemove(g\_processed\_signals\_list, 0, 1);  
        }  
    }  
}

// Function to send response back to Python. This function will use the active communication mode.  
// This is the implementation within the EA, using CommunicationManager's functionality.  
void SendResponseToPython(string signal\_id, string status, double execution\_price, string error\_message, double lot\_size, int magic\_number, int slippage, int mt4\_error\_code) {  
    string timestamp\_str \= TimeToString(TimeCurrent(), TIME\_DATE|TIME\_SECONDS);  
    string trade\_id\_str \= "N/A"; // Placeholder, set when trade is opened  
    string order\_ticket\_str \= "N/A";

    if (status \== "EXECUTED" && currentInitialTicket \> 0\) {  
        trade\_id\_str \= "TRADE\_" \+ (string)TimeCurrent() \+ "\_" \+ (string)currentInitialTicket; // Example ID  
        order\_ticket\_str \= (string)currentInitialTicket;  
    } else if (status \== "REJECTED" || status \== "FAILED" || status \== "IGNORED") {  
        trade\_id\_str \= "N/A";  
        order\_ticket\_str \= "N/A";  
    }

    // This data structure matches the EURUSD\_responses.csv format  
    // signal\_id,trade\_id,status,execution\_price,timestamp,error\_message,lot\_size,magic\_number,slippage  
    string response\_csv\_line \=  
        signal\_id \+ "," \+  
        trade\_id\_str \+ "," \+  
        status \+ "," \+  
        DoubleToString(execution\_price, Digits) \+ "," \+  
        timestamp\_str \+ "," \+  
        error\_message \+ "," \+  
        DoubleToString(lot\_size, \_Digits) \+ "," \+ // \_Digits ensures proper lot size formatting  
        (string)magic\_number \+ "," \+  
        (string)slippage;

    // Use the communication manager to send the response through the active channel  
    CommunicationManagerSendResponse(response\_csv\_line, ResponseFile); // Defined in CommunicationManager.mqh  
}

// Placeholder for EnumToString (common utility function)  
string EnumToString(int enumValue) {  
    switch(enumValue) {  
        case MODE\_SOCKET: return "MODE\_SOCKET";  
        case MODE\_PIPE: return "MODE\_PIPE";  
        case MODE\_FILE: return "MODE\_FILE";  
        default: return "UNKNOWN";  
    }  
}  
'@

\# CommunicationManager.mqh \- Manages hierarchical communication  
$communicationManagerContent \= @'  
//+------------------------------------------------------------------+  
//|                       CommunicationManager.mqh \- Richard Wilks   |  
//|                                     https://www.linkedin.com/in/richard-wilks/|  
//+------------------------------------------------------------------+  
\#property copyright "Richard Wilks"  
\#property link      "https://www.linkedin.com/in/richard-wilks/"  
\#property strict

// \--- DLL Imports (SocketBridge.dll functions) \---  
\#import "SocketBridge.dll"  
    int SocketConnect(string host, int port);  
    bool SocketDisconnect(int handle);  
    bool IsSocketConnected(int handle);  
    int SocketSend(int handle, string data);  
    int SocketReceive(int handle, string& buffer, int max\_length);  
    string GetLastSocketError();  
    void SetSocketTimeout(int handle, int timeout\_ms);

    // Named Pipe functions (from DLL for interprocess communication)  
    int PipeConnect(string pipeName);  
    bool PipeDisconnect(int handle);  
    bool IsPipeConnected(int handle);  
    int PipeWrite(int handle, string data);  
    int PipeRead(int handle, string& buffer, int max\_length);  
    string GetLastPipeError();  
\#import

// \--- Global variables from 10ParameterEA.mq4 (declared as extern in this file) \---  
extern int              g\_socket\_handle;  
extern bool             g\_socket\_connected;  
extern datetime         g\_last\_heartbeat;  
extern datetime         g\_last\_connection\_attempt;  
extern int              g\_connection\_failures;  
extern CommunicationMode g\_current\_mode;  
extern string           g\_receive\_buffer;  
extern string           ResponseFile; // From 10ParameterEA.mq4

// \--- Named Pipe Specific Globals \---  
int                 g\_pipe\_handle \= \-1;  
bool                g\_pipe\_connected \= false;  
string              g\_named\_pipe\_name;  
datetime            g\_last\_pipe\_check \= 0;  
datetime            g\_last\_pipe\_connection\_attempt \= 0;  
int                 g\_pipe\_connection\_failures \= 0;

// \--- Forward Declarations from 10ParameterEA.mq4 (for cross-file calls) \---  
void ProcessSignal(SignalData& signal); // Main EA signal processing logic  
bool ReadCSVSignal(SignalData& signal); // For CSV fallback  
void ClearCSVSignalFile();             // To clear processed CSV signals  
void SendResponseToPython(string signal\_id, string status, double execution\_price, string error\_message, double lot\_size, int magic\_number, int slippage, int mt4\_error\_code); // Response sender  
string EnumToString(int enumValue); // Utility for enum to string conversion

//+------------------------------------------------------------------+  
//| Initialize the primary communication channel (Socket)            |  
//| Attempts to connect to the Python server via TCP socket.         |  
//+------------------------------------------------------------------+  
bool InitializeSocketCommunication() {  
    Print("Attempting to initialize socket communication...");  
    // Host and port should be configurable, or fixed for local setup  
    string host \= "127.0.0.1";  
    int port \= 8888; // Default port for Python server

    g\_socket\_handle \= SocketConnect(host, port);  
    if (g\_socket\_handle \< 0\) {  
        Print("SocketConnect failed for ", host, ":", port, ". Error: ", GetLastSocketError());  
        g\_socket\_connected \= false;  
        return false;  
    }

    g\_socket\_connected \= true;  
    g\_last\_heartbeat \= TimeCurrent();  
    g\_connection\_failures \= 0;  
    Print("Socket communication initialized successfully to ", host, ":", port, ". Handle: ", g\_socket\_handle);  
    return true;  
}

//+------------------------------------------------------------------+  
//| Initialize Named Pipe communication (Fallback)                   |  
//| Attempts to connect to the Python server via Named Pipe.         |  
//+------------------------------------------------------------------+  
bool InitializeNamedPipes() {  
    Print("Attempting to initialize Named Pipe communication...");  
    g\_named\_pipe\_name \= "\\\\\\\\.\\\\pipe\\\\" \+ Symbol() \+ "\_signals"; // Unique pipe per pair

    g\_pipe\_handle \= PipeConnect(g\_named\_pipe\_name);  
    if (g\_pipe\_handle \== INVALID\_HANDLE) { // INVALID\_HANDLE is usually \-1 or 0xFFFFFFFF  
        Print("PipeConnect failed for ", g\_named\_pipe\_name, ". Error: ", GetLastPipeError());  
        g\_pipe\_connected \= false;  
        return false;  
    }

    g\_pipe\_connected \= true;  
    g\_pipe\_connection\_failures \= 0;  
    Print("Named Pipe communication initialized successfully to ", g\_named\_pipe\_name, ". Handle: ", g\_pipe\_handle);  
    return true;  
}

//+------------------------------------------------------------------+  
//| Overall communication manager initialization (called from OnInit)|  
//| Tries Socket, then Named Pipes, sets current mode.               |  
//+------------------------------------------------------------------+  
bool InitializeCommunicationManager() {  
    // Try Socket first  
    if (InitializeSocketCommunication()) {  
        g\_current\_mode \= MODE\_SOCKET;  
        SendEARegistration(); // Register EA with Python server  
        return true;  
    }

    Print("Socket initialization failed, falling back to Named Pipes...");  
    // Try Named Pipes second  
    if (InitializeNamedPipes()) {  
        g\_current\_mode \= MODE\_PIPE;  
        SendEARegistration(); // Register EA with Python server  
        return true;  
    }

    Print("Named Pipe initialization failed, falling back to CSV files...");  
    g\_current\_mode \= MODE\_FILE; // Final fallback  
    return false; // Indicates no real-time connection established  
}

//+------------------------------------------------------------------+  
//| Sends EA registration message to Python Server via active channel|  
//| Only applicable for Socket/Pipe modes.                           |  
//+------------------------------------------------------------------+  
void SendEARegistration() {  
    string registration\_message \= "{\\"type\\":\\"REGISTER\\",\\"ea\_id\\":\\"" \+ TerminalInfoString(TERMINAL\_NAME) \+ "\_" \+ Symbol() \+ "\_" \+ (string)ExpertMagicNumber() \+ "\\",\\"trading\_pair\\":\\"" \+ Symbol() \+ "\\",\\"magic\_number\\":" \+ (string)ExpertMagicNumber() \+ ",\\"timestamp\\":\\"" \+ TimeToString(TimeCurrent(), TIME\_DATE|TIME\_SECONDS) \+ "\\"}";  
      
    if (g\_current\_mode \== MODE\_SOCKET && g\_socket\_connected) {  
        if (SocketSend(g\_socket\_handle, registration\_message) \<= 0\) {  
            Print("Failed to send EA registration via socket. Error: ", GetLastSocketError());  
        } else {  
            Print("EA registered with Python server via socket.");  
        }  
    } else if (g\_current\_mode \== MODE\_PIPE && g\_pipe\_connected) {  
        if (PipeWrite(g\_pipe\_handle, registration\_message) \<= 0\) {  
            Print("Failed to send EA registration via named pipe. Error: ", GetLastPipeError());  
        } else {  
            Print("EA registered with Python server via named pipe.");  
        }  
    }  
}

//+------------------------------------------------------------------+  
//| Maintains active communication connection                        |  
//| Sends heartbeat, attempts reconnection if disconnected.          |  
//+------------------------------------------------------------------+  
void MaintainCommunicationManager() {  
    // Check and maintain socket connection  
    if (g\_current\_mode \== MODE\_SOCKET) {  
        if (g\_socket\_connected && \!IsSocketConnected(g\_socket\_handle)) {  
            Print("Socket disconnected, attempting reconnection...");  
            g\_socket\_connected \= false;  
            AttemptSocketReconnection();  
        }  
        // Send heartbeat if needed (every 5 seconds)  
        if (g\_socket\_connected && TimeCurrent() \- g\_last\_heartbeat \>= 5\) {  
            SendHeartbeat();  
            g\_last\_heartbeat \= TimeCurrent();  
        }  
    }  
    // Check and maintain named pipe connection  
    else if (g\_current\_mode \== MODE\_PIPE) {  
        if (g\_pipe\_connected && \!IsPipeConnected(g\_pipe\_handle)) {  
            Print("Named Pipe disconnected, attempting reconnection...");  
            g\_pipe\_connected \= false;  
            AttemptPipeReconnection();  
        }  
        // Named pipes generally don't need explicit heartbeats like sockets  
    }  
}

//+------------------------------------------------------------------+  
//| Attempts to reconnect socket after disconnection                 |  
//+------------------------------------------------------------------+  
void AttemptSocketReconnection() {  
    // Avoid rapid reconnection attempts  
    if (TimeCurrent() \- g\_last\_connection\_attempt \< 10\) return;  
        
    g\_last\_connection\_attempt \= TimeCurrent();  
    g\_connection\_failures++;  
        
    // Exponential backoff: wait longer after multiple failures  
    int backoff\_time \= MathMin(300, g\_connection\_failures \* 10);  
    if (TimeCurrent() \- g\_last\_connection\_attempt \< backoff\_time && g\_connection\_failures \> 1\) return; // Only apply backoff after first failure  
        
    Print("Attempting socket reconnect \#", g\_connection\_failures, "...");  
    if (InitializeSocketCommunication()) { // Re-calls InitializeSocketCommunication to reconnect  
        Print("Socket reconnection successful.");  
        g\_connection\_failures \= 0;  
        g\_current\_mode \= MODE\_SOCKET; // Restore primary mode  
        SendEARegistration(); // Re-register with server  
    } else {  
        Print("Socket reconnection failed. Total failures: ", g\_connection\_failures);  
        // If socket continuously fails, consider degrading to Named Pipe  
        if (g\_connection\_failures \>= 5 && g\_current\_mode \== MODE\_SOCKET) { // After 5 failed attempts  
            Print("Too many socket failures, attempting to switch to Named Pipes...");  
            if (InitializeNamedPipes()) {  
                g\_current\_mode \= MODE\_PIPE;  
                SendEARegistration(); // Re-register with server  
                Print("Switched to Named Pipe communication.");  
            } else {  
                Print("Named Pipes also failed, switching to CSV communication.");  
                g\_current\_mode \= MODE\_FILE;  
            }  
        }  
    }  
}

//+------------------------------------------------------------------+  
//| Attempts to reconnect named pipe after disconnection             |  
//+------------------------------------------------------------------+  
void AttemptPipeReconnection() {  
    // Avoid rapid reconnection attempts  
    if (TimeCurrent() \- g\_last\_pipe\_connection\_attempt \< 5\) return; // Shorter backoff for pipes  
        
    g\_last\_pipe\_connection\_attempt \= TimeCurrent();  
    g\_pipe\_connection\_failures++;  
        
    int backoff\_time \= MathMin(60, g\_pipe\_connection\_failures \* 5); // Max 60s backoff  
    if (TimeCurrent() \- g\_last\_pipe\_connection\_attempt \< backoff\_time && g\_pipe\_connection\_failures \> 1\) return;  
        
    Print("Attempting named pipe reconnect \#", g\_pipe\_connection\_failures, "...");  
    if (InitializeNamedPipes()) {  
        Print("Named Pipe reconnection successful.");  
        g\_pipe\_connection\_failures \= 0;  
        g\_current\_mode \= MODE\_PIPE; // Restore pipe mode  
        SendEARegistration(); // Re-register with server  
    } else {  
        Print("Named Pipe reconnection failed. Total failures: ", g\_pipe\_connection\_failures);  
        // If pipe continuously fails, degrade to CSV  
        if (g\_pipe\_connection\_failures \>= 5 && g\_current\_mode \== MODE\_PIPE) { // After 5 failed attempts  
            Print("Too many named pipe failures, switching to CSV communication.");  
            g\_current\_mode \= MODE\_FILE;  
        }  
    }  
}

//+------------------------------------------------------------------+  
//| Sends a heartbeat message to keep the socket connection alive    |  
//+------------------------------------------------------------------+  
void SendHeartbeat() {  
    if (g\_current\_mode \== MODE\_SOCKET && g\_socket\_connected) {  
        string heartbeat\_msg \= "{\\"type\\":\\"HEARTBEAT\\",\\"timestamp\\":\\"" \+ TimeToString(TimeCurrent(), TIME\_DATE|TIME\_SECONDS) \+ "\\",\\"ea\_id\\":\\"" \+ TerminalInfoString(TERMINAL\_NAME) \+ "\_" \+ Symbol() \+ "\\"}";  
        if (SocketSend(g\_socket\_handle, heartbeat\_msg) \<= 0\) {  
            Print("Failed to send heartbeat, socket may be disconnected. Error: ", GetLastSocketError());  
            g\_socket\_connected \= false; // Mark as disconnected for next tick's check  
        }  
    }  
}

//+------------------------------------------------------------------+  
//| Checks for signals using hierarchical approach (Socket \-\> Pipe \-\> CSV) |  
//| Calls ProcessSignal if a valid signal is found.                  |  
//+------------------------------------------------------------------+  
void CheckForSignalsHierarchical() {  
    SignalData receivedSignal; // A temporary struct to hold the received signal

    bool signal\_found \= false;  
        
    // Try socket first  
    if (g\_current\_mode \== MODE\_SOCKET && g\_socket\_connected) {  
        // Assume SocketReceive and JSON parsing happens here to populate receivedSignal  
        if (CheckSocketForSignals(receivedSignal)) { // Function to be implemented below  
            signal\_found \= true;  
        }  
    }  
        
    // Fall back to pipes if socket failed or no signal from socket  
    if (\!signal\_found && (g\_current\_mode \== MODE\_SOCKET || g\_current\_mode \== MODE\_PIPE)) {  
        if (CheckNamedPipeForSignals(receivedSignal)) { // Function to be implemented below  
            signal\_found \= true;  
            if (g\_current\_mode \== MODE\_SOCKET) { // If we degraded from socket  
                Print("Socket failed, degraded to pipe communication.");  
                g\_current\_mode \= MODE\_PIPE;  
            }  
        }  
    }  
        
    // Final fallback to CSV if both socket and pipe failed or no signal from them  
    if (\!signal\_found) {  
        CheckCSVForSignals(); // This function will internally call ReadCSVSignal and ProcessSignal  
        // This is a special case: CheckCSVForSignals is designed to directly handle CSV logic and call ProcessSignal.  
        // It doesn't return a bool like the socket/pipe functions.  
        if (g\_current\_mode \!= MODE\_FILE) {  
            Print("All real-time communication failed, using CSV backup.");  
            g\_current\_mode \= MODE\_FILE;  
        }  
    } else {  
        // If a signal was found via Socket or Pipe, process it directly  
        ProcessSignal(receivedSignal); // Call the main EA's ProcessSignal  
    }

    // Report current communication status in chart comment  
    string status\_text \= "Comm Mode: " \+ EnumToString(g\_current\_mode) \+  
                         " | Socket: " \+ (g\_socket\_connected ? "Connected" : "Disconnected") \+  
                         " | Pipe: " \+ (g\_pipe\_connected ? "Connected" : "Disconnected");  
    Comment(status\_text);  
}

//+------------------------------------------------------------------+  
//| Checks for signals from the Socket. Populates SignalData struct. |  
//+------------------------------------------------------------------+  
bool CheckSocketForSignals(SignalData& signal) {  
    if (\!g\_socket\_connected) return false;  
        
    string received\_data;  
    // Max buffer length for received data (e.g., 4KB)  
    int bytes\_received \= SocketReceive(g\_socket\_handle, received\_data, 4096);  
        
    if (bytes\_received \<= 0\) {  
        // Print("No data from socket or error: ", GetLastSocketError()); // Too noisy for no data  
        return false;  
    }  
      
    // Parse JSON signal data. This requires a JSON parsing library or manual parsing logic.  
    // For now, this is a placeholder. Real implementation needs robust JSON parsing.  
    if (ParseJSONSignal(received\_data, signal)) { // Function to be implemented (can be simple StringFind/StringSubstr for small JSON)  
        Print("Signal received via Socket: ", signal.id);  
        return true;  
    }  
        
    Print("Failed to parse JSON signal from socket: ", received\_data);  
    return false;  
}

//+------------------------------------------------------------------+  
//| Checks for signals from the Named Pipe. Populates SignalData.    |  
//+------------------------------------------------------------------+  
bool CheckNamedPipeForSignals(SignalData& signal) {  
    if (\!g\_pipe\_connected) return false;

    string received\_data;  
    // Max buffer length for received data (e.g., 4KB)  
    int bytes\_read \= PipeRead(g\_pipe\_handle, received\_data, 4096);

    if (bytes\_read \<= 0\) {  
        // Print("No data from pipe or error: ", GetLastPipeError()); // Too noisy  
        return false;  
    }

    // Parse JSON signal data (assuming same JSON format as socket)  
    if (ParseJSONSignal(received\_data, signal)) {  
        Print("Signal received via Named Pipe: ", signal.id);  
        return true;  
    }

    Print("Failed to parse JSON signal from named pipe: ", received\_data);  
    return false;  
}

//+------------------------------------------------------------------+  
//| Processes signals from the CSV file.                             |  
//| This function is special as it \*directly\* handles CSV logic      |  
//| including reading and then calling ProcessSignal.                |  
//+------------------------------------------------------------------+  
void CheckCSVForSignals() {  
    static datetime lastCSVModTime \= 0;  
    string file\_path \= MT4\_FILES\_PATH \+ InputSignalFile;

    // 1\. Check file modification time to avoid unnecessary reads  
    datetime current\_mod\_time \= FileGetTime(file\_path, MODE\_TIME\_LASTMODIFIED);  
    if (current\_mod\_time \<= lastCSVModTime) {  
        return; // No new signal  
    }  
    lastCSVModTime \= current\_mod\_time; // Update last check time

    SignalData csvSignal;  
    if (ReadCSVSignal(csvSignal)) { // This function reads the actual CSV file  
        Print("Signal received via CSV: ", csvSignal.id);  
        ProcessSignal(csvSignal); // Call the main EA's ProcessSignal  
        ClearCSVSignalFile();     // Clear the CSV file after processing  
    }  
}

//+------------------------------------------------------------------+  
//| Sends a trade response back to Python via the active channel.    |  
//| Handles fallback to CSV if primary channel fails.                |  
//+------------------------------------------------------------------+  
void CommunicationManagerSendResponse(string response\_csv\_line, string filename) {  
    string response\_json \= ConvertCSVToJSONResponse(response\_csv\_line); // Convert to JSON for socket/pipe

    bool sent \= false;  
    // Try Socket first  
    if (g\_current\_mode \== MODE\_SOCKET && g\_socket\_connected) {  
        if (SocketSend(g\_socket\_handle, response\_json) \> 0\) {  
            Print("Sent response via Socket.");  
            sent \= true;  
        } else {  
            Print("Failed to send response via Socket. Error: ", GetLastSocketError());  
            g\_socket\_connected \= false; // Mark disconnected  
            AttemptSocketReconnection(); // Try to reconnect or degrade  
        }  
    }

    // Try Named Pipe if Socket failed or not active  
    if (\!sent && (g\_current\_mode \== MODE\_PIPE || g\_current\_mode \== MODE\_SOCKET)) { // Also try if degraded from socket  
        if (g\_pipe\_connected) {  
            if (PipeWrite(g\_pipe\_handle, response\_json) \> 0\) {  
                Print("Sent response via Named Pipe.");  
                sent \= true;  
                if (g\_current\_mode \== MODE\_SOCKET) g\_current\_mode \= MODE\_PIPE; // Degrade confirmed  
            } else {  
                Print("Failed to send response via Named Pipe. Error: ", GetLastPipeError());  
                g\_pipe\_connected \= false; // Mark disconnected  
                AttemptPipeReconnection(); // Try to reconnect or degrade  
            }  
        }  
    }

    // Fallback to CSV if both real-time channels failed or not active  
    if (\!sent || g\_current\_mode \== MODE\_FILE) {  
        Print("Sending response via CSV fallback.");  
        WriteCSVResponse(response\_csv\_line, filename); // This function will be in FileManager.mqh  
        if (\!sent && g\_current\_mode \!= MODE\_FILE) { // If it failed real-time and wasn't already file mode  
             Print("All real-time response methods failed. Switched to CSV for responses.");  
             g\_current\_mode \= MODE\_FILE;  
        }  
    }  
}

//+------------------------------------------------------------------+  
//| Helper to convert CSV response string to JSON for socket/pipe    |  
//| This is a simplified example. A real JSON library would be better|  
//+------------------------------------------------------------------+  
string ConvertCSVToJSONResponse(string csv\_line) {  
    string parts\[\];  
    StringSplit(csv\_line, ',', parts);  
      
    string json \= "{";  
    json \+= "\\"signal\_id\\":\\"" \+ parts\[0\] \+ "\\",";  
    json \+= "\\"trade\_id\\":\\"" \+ parts\[1\] \+ "\\",";  
    json \+= "\\"status\\":\\"" \+ parts\[2\] \+ "\\",";  
    json \+= "\\"execution\_price\\":" \+ parts\[3\] \+ ",";  
    json \+= "\\"timestamp\\":\\"" \+ parts\[4\] \+ "\\",";  
    json \+= "\\"error\_message\\":\\"" \+ parts\[5\] \+ "\\",";  
    json \+= "\\"lot\_size\\":" \+ parts\[6\] \+ ",";  
    json \+= "\\"magic\_number\\":" \+ parts\[7\] \+ ",";  
    json \+= "\\"slippage\\":" \+ parts\[8\];  
    json \+= "}";  
    return json;  
}

//+------------------------------------------------------------------+  
//| Placeholder for JSON parsing logic (to be expanded)              |  
//| Very basic parsing, not robust for complex JSON.                 |  
//| A dedicated MQL4 JSON library would be ideal.                    |  
//+------------------------------------------------------------------+  
bool ParseJSONSignal(string json\_data, SignalData& signal) {  
    // This is a highly simplified JSON parser. For production, consider an MQL4 JSON library.  
    // This assumes specific key order and simple string/number values.

    string value;

    // id  
    if (StringFind(json\_data, "\\"signal\_id\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"signal\_id\\":\\"") \+ StringLen("\\"signal\_id\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\","));  
        signal.id \= value;  
    } else return false;

    // symbol  
    if (StringFind(json\_data, "\\"symbol\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"symbol\\":\\"") \+ StringLen("\\"symbol\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\","));  
        signal.symbol \= value;  
    } else return false;  
      
    // direction  
    if (StringFind(json\_data, "\\"direction\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"direction\\":\\"") \+ StringLen("\\"direction\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\","));  
        signal.direction \= value;  
    } else return false;

    // confidence  
    if (StringFind(json\_data, "\\"confidence\\":") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"confidence\\":") \+ StringLen("\\"confidence\\":"));  
        value \= StringSubstr(value, 0, StringFind(value, ","));  
        signal.confidence \= StringToDouble(value);  
    } else return false;  
      
    // timestamp  
    if (StringFind(json\_data, "\\"timestamp\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"timestamp\\":\\"") \+ StringLen("\\"timestamp\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\","));  
        signal.timestamp \= StrToTime(value);  
    } else return false;  
      
    // strategy\_id  
    if (StringFind(json\_data, "\\"strategy\_id\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"strategy\_id\\":\\"") \+ StringLen("\\"strategy\_id\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\","));  
        signal.strategy\_id \= value;  
    } else return false;

    // metadata (optional, can be empty or complex JSON)  
    if (StringFind(json\_data, "\\"metadata\\":") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"metadata\\":") \+ StringLen("\\"metadata\\":"));  
        int end\_pos \= StringFind(value, "}"); // Find end of metadata object  
        if (end\_pos \== \-1) end\_pos \= StringLen(value); // If it's the last element  
        value \= StringSubstr(value, 0, end\_pos \+ 1); // Include the closing brace  
        signal.metadata \= value;  
    } else {  
        signal.metadata \= "{}"; // Default empty JSON  
    }

    // parameter\_set\_override (optional, from "parameters": {"parameter\_set": "SET\_XX"})  
    if (StringFind(json\_data, "\\"parameter\_set\\":\\"") \>= 0\) {  
        value \= StringSubstr(json\_data, StringFind(json\_data, "\\"parameter\_set\\":\\"") \+ StringLen("\\"parameter\_set\\":\\""));  
        value \= StringSubstr(value, 0, StringFind(value, "\\""));  
        signal.parameter\_set\_override \= value;  
    } else {  
        signal.parameter\_set\_override \= ""; // Default empty  
    }

    return true; // Assume parsing was successful if all main parts found  
}

//+------------------------------------------------------------------+  
//| Deinitialization of communication manager                        |  
//+------------------------------------------------------------------+  
void DeinitializeCommunicationManager() {  
    if (g\_socket\_handle \>= 0\) {  
        SocketDisconnect(g\_socket\_handle);  
        Print("Socket disconnected. Handle: ", g\_socket\_handle);  
    }  
    if (g\_pipe\_handle \!= INVALID\_HANDLE) {  
        PipeDisconnect(g\_pipe\_handle);  
        Print("Named Pipe disconnected. Handle: ", g\_pipe\_handle);  
    }  
    g\_socket\_connected \= false;  
    g\_pipe\_connected \= false;  
    g\_current\_mode \= MODE\_FILE; // Ensure mode is reset  
}

'@

\# NamedPipeManager.mqh \- Named pipe abstraction  
$namedPipeManagerContent \= @'  
//+------------------------------------------------------------------+  
//|                         NamedPipeManager.mqh \- Richard Wilks     |  
//|                                     https://www.linkedin.com/in/richard-wilks/|  
//+------------------------------------------------------------------+  
\#property copyright "Richard Wilks"  
\#property link      "https://www.linkedin.com/in/richard-wilks/"  
\#property strict

// \--- DLL Imports from SocketBridge.dll for Named Pipes \---  
// Defined in CommunicationManager.mqh  
// \#import "SocketBridge.dll"  
//     int PipeConnect(string pipeName);  
//     bool PipeDisconnect(int handle);  
//     bool IsPipeConnected(int handle);  
//     int PipeWrite(int handle, string data);  
//     int PipeRead(int handle, string& buffer, int max\_length);  
//     string GetLastPipeError();  
// \#import

// No direct MQL4 code here, as Named Pipe functions are entirely wrapped in the DLL  
// and called via CommunicationManager.mqh.  
// This file serves as a logical placeholder for potential future native MQL4 pipe features  
// or more complex pipe-specific MQL4 logic, should the DLL become more granular.  
// For now, it mainly clarifies the DLL dependency and architecture.

'@

\# FileManager.mqh \- Enhanced CSV handling  
$fileManagerContent \= @'  
//+------------------------------------------------------------------+  
//|                           FileManager.mqh \- Richard Wilks        |  
//|                                     https://www.linkedin.com/in/richard-wilks/|  
//+------------------------------------------------------------------+  
\#property copyright "Richard Wilks"  
\#property link      "https://www.linkedin.com/in/richard-wilks/"  
\#property strict

// \--- Global variables from 10ParameterEA.mq4 (declared as extern in this file) \---  
extern string   InputSignalFile; // File to simulate incoming signals  
extern string   ResponseFile;    // File for EA to write responses

\#define MT4\_FILES\_PATH "" // Base path for FileOpen in MQL4 is MQL4/Files. No need for full path here.

// \--- Forward Declarations from 10ParameterEA.mq4 \---  
// (Needed if this file were to directly call EA functions for processing)  
// For now, FileManager handles basic read/write, and CommunicationManager orchestrates.

//+------------------------------------------------------------------+  
//| Writes a trade response to a CSV file.                           |  
//| Used as the final fallback communication method.                 |  
//|                        |  
//+------------------------------------------------------------------+  
void WriteCSVResponse(string response\_line, string filename) {  
    int file\_handle \= FileOpen(MT4\_FILES\_PATH \+ filename, FILE\_WRITE | FILE\_CSV | FILE\_ADD, ',');  
    if (file\_handle \< 0\) {  
        Print("Error opening response file for writing: ", MT4\_FILES\_PATH \+ filename, " Error: ", GetLastError());  
        return;  
    }

    if (FileIsEnding(file\_handle)) { // Check if file is empty or just created  
        // Write header only if file is new or empty  
        FileWriteString(file\_handle, "signal\_id,trade\_id,status,execution\_price,timestamp,error\_message,lot\_size,magic\_number,slippage\\n");  
    }

    FileWriteString(file\_handle, response\_line \+ "\\n"); // Add newline for next entry  
    FileClose(file\_handle);  
    Print("Response written to CSV file: ", MT4\_FILES\_PATH \+ filename);  
}

//+------------------------------------------------------------------+  
//| Utility function to get file modification time                   |  
//| Used by CommunicationManager to optimize CSV checks.             |  
//|                                  |  
//+------------------------------------------------------------------+  
datetime GetFileModTime(string filename) {  
    return FileGetTime(MT4\_FILES\_PATH \+ filename, MODE\_TIME\_LASTMODIFIED);  
}

// Additional utility functions can be added here, e.g., for:  
// \- Atomic file operations (using FileRename for temp files)  
// \- More robust CSV parsing/writing (handling commas in data, quotes etc.)  
// \- Deleting processed signal entries from CSV (instead of just clearing)

'@

\# TradingCore.mqh \- Core trading logic (placeholder for now)  
$tradingCoreContent \= @'  
//+------------------------------------------------------------------+  
//|                            TradingCore.mqh \- Richard Wilks       |  
//|                                     https://www.linkedin.com/in/richard-wilks/|  
//+------------------------------------------------------------------+  
\#property copyright "Richard Wilks"  
\#property link      "https://www.linkedin.com/in/richard-wilks/"  
\#property strict

// \--- Forward Declarations from 10ParameterEA.mq4 \---  
// (Needed for accessing global variables or structures defined in the main EA)  
extern double           LOT\_SIZE; // Example external input from EA  
extern int              MAGIC\_NUMBER\_BASE; // Example external input from EA  
extern int              SLIPPAGE; // Example external input from EA  
extern bool             initialTradeOpen;  
extern bool             reentryTradeOpen;  
extern long             currentInitialTicket;  
extern long             currentReentryTicket;  
extern int              tradeResult;  
extern t\_ParameterSet   ParameterSets\[\]; // For accessing parameter sets  
extern t\_CloseResultMapping CloseResultMappings\[\]; // For reentry logic

// Structure for incoming signals (from main EA)  
struct SignalData; // Forward declaration as it's defined in 10ParameterEA.mq4

// \--- Placeholder for MonitorExistingPositions() \---  
// This function will be expanded to analyze closed trades and determine reentry.  
void MonitorExistingPositions() {  
    if (initialTradeOpen) {  
        // Check if the initial trade is still open  
        if (\!OrderSelect(currentInitialTicket, SELECT\_BY\_TICKET)) {  
            Print("Initial trade with ticket ", currentInitialTicket, " has closed.");  
            initialTradeOpen \= false;  
            // Determine trade result (SL, TP, partial, breakeven, etc.)  
            // For now, a placeholder. This is where Step 2 (Trade Monitoring & Close Analysis) happens  
              
            // Assume for simplicity it hit TP for demo purposes  
            tradeResult \= CLOSE\_RESULT\_TP\_HIT;   
            Print("Initial trade result: ", tradeResult);  
              
            // Execute Reentry Trade based on result  
            ExecuteReentryTrade(tradeResult);  
        }  
    }  
    // Similar logic for reentryTradeOpen if you allow multi-level reentry or need to track it  
}

//+------------------------------------------------------------------+  
//| Executes a trade (OrderSend wrapper).                            |  
//| This function is called by ProcessSignal in 10ParameterEA.mq4.   |  
//+------------------------------------------------------------------+  
long ExecuteTrade(string symbol, int direction, double lots, int sl\_points, int tp\_points, int slippage, int magic) {  
    if (\!IsTradeAllowed()) {  
        Print("Trading not allowed by EA properties or market conditions.");  
        return \-1;  
    }

    double entry\_price \= (direction \== OP\_BUY) ? Ask : Bid;  
    double stop\_loss\_price \= 0;  
    double take\_profit\_price \= 0;

    // Calculate SL and TP prices  
    if (sl\_points \> 0\) {  
        stop\_loss\_price \= (direction \== OP\_BUY) ? entry\_price \- sl\_points \* Point : entry\_price \+ sl\_points \* Point;  
    }  
    if (tp\_points \> 0\) {  
        take\_profit\_price \= (direction \== OP\_BUY) ? entry\_price \+ tp\_points \* Point : entry\_price \- tp\_points \* Point;  
    }

    // Normalize prices to symbol's digits  
    entry\_price \= NormalizeDouble(entry\_price, Digits);  
    stop\_loss\_price \= NormalizeDouble(stop\_loss\_price, Digits);  
    take\_profit\_price \= NormalizeDouble(take\_profit\_price, Digits);  
      
    // Ensure lot size is valid  
    lots \= NormalizeDouble(lots, 2); // Typically 2 decimal places for lots  
    if (lots \<= 0 || lots \> AccountFreeMargin() / 1000\) { // Basic sanity check  
        Print("Invalid lot size or insufficient margin: ", lots);  
        return \-1;  
    }

    long ticket \= OrderSend(symbol, direction, lots, entry\_price, slippage, stop\_loss\_price, take\_profit\_price,  
                            "Signal Trade", magic, 0, (direction \== OP\_BUY) ? Green : Red);

    if (ticket \< 0\) {  
        Print("OrderSend failed\! Error: ", GetLastError(), " (", ErrorDescription(GetLastError()), ")");  
    } else {  
        Print("OrderSend successful\! Ticket: ", ticket, ", Symbol: ", symbol, ", Direction: ", (direction \== OP\_BUY ? "BUY" : "SELL"),  
              ", Lots: ", lots, ", Entry: ", entry\_price, ", SL: ", stop\_loss\_price, ", TP: ", take\_profit\_price, ", Magic: ", magic);  
    }  
    return ticket;  
}

//+------------------------------------------------------------------+  
//| Executes a reentry trade based on the initial trade's result.    |  
//|                                |  
//+------------------------------------------------------------------+  
void ExecuteReentryTrade(int previousTradeResult) {  
    Print("Attempting to execute reentry trade for result code: ", previousTradeResult);  
    string parameterSetToUse \= "";  
    bool paramsFound \= false;

    // Find the reentry parameter set based on the previous trade result  
    for (int i \= 0; i \< ArraySize(CloseResultMappings); i++) {  
        if (CloseResultMappings\[i\].close\_result\_code \== previousTradeResult) {  
            parameterSetToUse \= CloseResultMappings\[i\].parameter\_set\_id;  
            Print("Mapped reentry result ", previousTradeResult, " to parameter set: ", parameterSetToUse);  
            paramsFound \= true;  
            break;  
        }  
    }

    if (\!paramsFound) {  
        Print("Error: No reentry parameter set found for result code: ", previousTradeResult);  
        return;  
    }

    t\_ParameterSet reentryParams;  
    paramsFound \= false; // Reset for lookup in ParameterSets  
    for (int i \= 0; i \< ArraySize(ParameterSets); i++) {  
        if (ParameterSets\[i\].set\_id \== parameterSetToUse) {  
            reentryParams \= ParameterSets\[i\];  
            paramsFound \= true;  
            break;  
        }  
    }

    if (\!paramsFound) {  
        Print("Error: Reentry parameter set '", parameterSetToUse, "' not found in loaded configurations.");  
        return;  
    }

    // Determine reentry direction (e.g., usually inverse of initial trade for "recovery" or same for "continuation")  
    // This logic is simplified. In a real system, the reentry logic might have its own signal or be based on previous direction.  
    // For now, let's assume if initial was BUY, reentry is SELL, and vice-versa.  
    int reentryDirection \= 0;  
    if (OrderSelect(currentInitialTicket, SELECT\_BY\_TICKET)) {  
        if (OrderType() \== OP\_BUY) reentryDirection \= OP\_SELL;  
        else if (OrderType() \== OP\_SELL) reentryDirection \= OP\_BUY;  
    } else {  
        Print("Could not determine initial trade direction for reentry. Skipping reentry.");  
        return;  
    }

    Print("Executing reentry trade for ", Symbol(), " ", (reentryDirection \== OP\_BUY ? "BUY" : "SELL"),  
          " with parameters from set: ", reentryParams.set\_id);  
      
    currentReentryTicket \= ExecuteTrade(Symbol(), reentryDirection, reentryParams.lot\_size,  
                                       reentryParams.stop\_loss, reentryParams.take\_profit,  
                                       reentryParams.slippage, reentryParams.magic\_base);

    if (currentReentryTicket \> 0\) {  
        reentryTradeOpen \= true;  
        Print("Reentry trade opened successfully\! Ticket: ", currentReentryTicket);  
    } else {  
        Print("Failed to open reentry trade. Error: ", GetLastError());  
    }

    // After reentry, the cycle is complete. Wait for next CSV signal.  
    initialTradeOpen \= false; // Reset for next initial trade  
    currentInitialTicket \= 0;  
    currentSignalID \= "";  
    tradeResult \= 0;  
    // We would clear processed signals list or manage it for next cycle.  
}

//+------------------------------------------------------------------+  
//| Check if trading is allowed by EA properties                     |  
//+------------------------------------------------------------------+  
bool IsTradeAllowed() {  
    if (IsStopped() || IsDllsAllowed() \== false || IsExpertEnabled() \== false) {  
        return false;  
    }  
    return true;  
}  
'@

\# \--- File Writing \---  
$files \= @{  
    (Join-Path $eaSourcePath "10ParameterEA.mq4")         \= $eaContent;  
    (Join-Path $includeSourcePath "CommunicationManager.mqh") \= $communicationManagerContent;  
    (Join-Path $includeSourcePath "NamedPipeManager.mqh") \= $namedPipeManagerContent;  
    (Join-Path $includeSourcePath "FileManager.mqh")      \= $fileManagerContent;  
    (Join-Path $includeSourcePath "TradingCore.mqh")      \= $tradingCoreContent;  
}

foreach ($filePath in $files.Keys) {  
    $files\[$filePath\] | Out-File \-FilePath $filePath \-Encoding UTF8  
    $fileName \= Split-Path $filePath \-Leaf  
    Write-Host "✅ Created: $fileName" \-ForegroundColor Green  
}

\# \--- CSV Files (for MQL4\\Files directory directly) \---  
Write-Host "\`nCreating initial CSV configuration files in MT4 MQL4\\Files directory..." \-ForegroundColor Green

\# all\_10\_parameter\_sets.csv  
$paramSetsCsvContent \= @'  
set\_id,risk\_percent,lot\_size,stop\_loss,take\_profit,slippage,magic\_base  
SET\_01,1.5,0.01,8,15,2,10001  
SET\_02,3.0,0.02,12,25,3,10002  
SET\_03,2.5,0.015,15,30,2,10003  
SET\_04,2.0,0.01,10,20,3,10004  
SET\_05,1.0,0.005,5,10,2,10005  
SET\_06,2.0,0.01,8,15,2,10006  
SET\_07,1.5,0.01,10,20,3,10007  
SET\_08,3.5,0.025,15,35,2,10008  
SET\_09,1.0,0.005,5,8,2,10009  
SET\_10,4.0,0.03,20,50,3,10010  
'@

\# signal\_id\_mapping.csv  
$signalMappingCsvContent \= @'  
signal\_id,parameter\_set,description  
SCALP\_SIGNAL,SET\_01,Scalping parameters  
BREAKOUT\_SIGNAL,SET\_02,Breakout parameters  
TREND\_SIGNAL,SET\_03,Trend following parameters  
REVERSAL\_SIGNAL,SET\_04,Reversal parameters  
'@

\# reentry\_close\_result\_mapping.csv  
$reentryMappingCsvContent \= @'  
close\_result,parameter\_set,description  
1,SET\_05,Stop loss reentry  
2,SET\_06,Partial loss reentry  
3,SET\_07,Breakeven reentry  
4,SET\_08,Partial profit reentry  
5,SET\_09,Take profit reentry  
6,SET\_10,Beyond TP reentry  
'@

\# current\_signal.csv (Initial placeholder)  
$currentSignalCsvContent \= @'  
id,symbol,direction,confidence,timestamp,strategy\_id,metadata  
initial\_test\_signal,EURUSD,BUY,0.85,2024-06-18 20:00:00,BREAKOUT\_SIGNAL,{"source":"manual\_test"}  
'@

\# Write CSV files directly to MT4 MQL4\\Files  
$csvFiles \= @{  
    (Join-Path $mql4FilesPath "all\_10\_parameter\_sets.csv")       \= $paramSetsCsvContent;  
    (Join-Path $mql4FilesPath "signal\_id\_mapping.csv")           \= $signalMappingCsvContent;  
    (Join-Path $mql4FilesPath "reentry\_close\_result\_mapping.csv")= $reentryMappingCsvContent;  
    (Join-Path $mql4FilesPath "current\_signal.csv")              \= $currentSignalCsvContent;  
}

foreach ($filePath in $csvFiles.Keys) {  
    $csvFiles\[$filePath\] | Out-File \-FilePath $filePath \-Encoding UTF8  
    $fileName \= Split-Path $filePath \-Leaf  
    Write-Host "✅ Created CSV: $fileName" \-ForegroundColor Green  
}

\# \--- Success message and next steps \---  
Write-Host "\`n🎉 MT4 EXPERT ADVISOR AND INCLUDE FILES CREATED SUCCESSFULLY\!" \-ForegroundColor Green  
Write-Host "📂 MQL4 Source Location: $projectSourceRoot\\MQL4" \-ForegroundColor Cyan  
Write-Host "📂 MT4 Data Files Location: $mql4FilesPath" \-ForegroundColor Cyan  
Write-Host "\`n🚀 Next steps for MT4:" \-ForegroundColor Yellow  
Write-Host "1. Open MetaEditor (F4 in MT4)." \-ForegroundColor White  
Write-Host "2. Navigate to 'C:\\Users\\Richard Wilks\\TradingSystem\\Source\\MQL4\\Experts' and open '10ParameterEA.mq4'." \-ForegroundColor White  
Write-Host "3. Navigate to 'C:\\Users\\Richard Wilks\\TradingSystem\\Source\\MQL4\\Include' and verify the .mqh files are there." \-ForegroundColor White  
Write-Host "4. Press F7 to compile '10ParameterEA.mq4'. Ensure 'Allow DLL imports' is checked in EA properties on chart." \-ForegroundColor White  
Write-Host "5. The CSV files are already placed in your MT4 terminal's MQL4\\Files directory." \-ForegroundColor White  
Write-Host "6. \*\*Crucial:\*\* You must now proceed to \*\*Part 2: C++ DLL Bridge Files\*\* to create the 'SocketBridge.dll' which is essential for communication." \-ForegroundColor Red

