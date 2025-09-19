\
//+------------------------------------------------------------------+
//| ReentryHelpers.mq4                                               |
//| Compose/parse/validate Reentry reentry_key on the EA side.       |
//| Format: SIG~TB~OB~PB~G                                           |
//| NOTE: For EA comment suffix, prefer using the suffix provided     |
//| from Python in CSV. This file includes a lightweight fallback     |
//| FNV32->Base32 for local suffix if needed (not identical to SHA1). |
//+------------------------------------------------------------------+
#property strict

// Allowed tokens (must match Python vocab)
string DURATION_TOKENS[] = {"FLASH","QUICK","LONG","EXTENDED"};
string PROXIMITY_TOKENS[] = {"PRE_1H","AT_EVENT","POST_30M"};
string OUTCOME_TOKENS[]   = {"W2","W1","BE","L1","L2"};

//--------------------------------------------------------------------
bool InArray(const string token, const string &arr[]) {
   for (int i=0; i<ArraySize(arr); i++) if (arr[i] == token) return true;
   return false;
}

string ComposeReentryKey(const string sig, const string tb, const string ob, const string pb, const int gen) {
   return sig + "~" + tb + "~" + ob + "~" + pb + "~" + IntegerToString(gen);
}

bool ParseReentryKey(const string key, string &sig, string &tb, string &ob, string &pb, int &gen) {
   string parts[];
   int n = StringSplit(key, "~", parts);
   if (n != 5) return false;
   sig = parts[0]; tb = parts[1]; ob = parts[2]; pb = parts[3];
   gen = (int) StringToInteger(parts[4]);
   return true;
}

int ValidateReentryKey(const string key, string &errmsg) {
   string sig,tb,ob,pb; int gen;
   if (!ParseReentryKey(key, sig, tb, ob, pb, gen)) {
      errmsg = "Key must have 5 parts SIG~TB~OB~PB~G";
      return -1;
   }
   if (StringLen(sig) < 3 || StringLen(sig) > 64) { errmsg="signal_id length 3..64"; return -2; }
   // signal_id pattern A-Z0-9_
   for (int i=0;i<StringLen(sig);i++) {
      int ch = sig[i];
      bool ok = (ch>='A' && ch<='Z') || (ch>='0' && ch<='9') || (ch=='_');
      if (!ok) { errmsg="signal_id must be A-Z0-9_"; return -3; }
   }
   if (!InArray(tb, DURATION_TOKENS)) { errmsg="time_bucket not allowed"; return -4; }
   if (!InArray(ob, OUTCOME_TOKENS))  { errmsg="outcome_bucket not allowed"; return -5; }
   if (!InArray(pb, PROXIMITY_TOKENS)){ errmsg="proximity_bucket not allowed"; return -6; }
   if (gen < 1 || gen > 3) { errmsg="generation must be in [1,3]"; return -7; }
   errmsg = "";
   return 0;
}

// Optional: local comment suffix (FNV32 -> Base32). Prefer using suffix from CSV.
uint fnv1a32(const string s) {
   uint hash = 0x811C9DC5;
   for (int i=0;i<StringLen(s);i++) {
      uchar c = (uchar) s[i];
      hash ^= c;
      hash *= 0x01000193;
   }
   return hash;
}

string base32_from_uint(uint value, int length) {
   string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
   string out = "";
   for (int i=0;i<length;i++) {
      int idx = (int)(value & 31);
      out = StringSubstr(alphabet, idx, 1) + out;
      value >>= 5;
   }
   return out;
}

string CommentSuffixLocal(const string key, const int len=6) {
   return base32_from_uint(fnv1a32(key), len);
}

string CommentWithSuffix(const string prefix, const string key, const string supplied_suffix="") {
   string suffix = supplied_suffix;
   if (StringLen(suffix) == 0)
      suffix = CommentSuffixLocal(key); // fallback
   return prefix + "_" + suffix;
}
