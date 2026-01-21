// doc_id: DOC-LEGACY-0098

//+------------------------------------------------------------------+
//|                                                  ExpiryZones.mq4 |
//| Draws FX option expiry strike lines/zones from a local HTTP API  |
//| Requires: MT4 → Tools → Options → Expert Advisors →              |
//|   Allow WebRequest for listed URL: http://127.0.0.1:5001         |
//+------------------------------------------------------------------+
#property strict
#property indicator_chart_window

input string InpBaseUrl        = "http://127.0.0.1:5001";
input int    InpRefreshSeconds = 30;
input int    InpZonePips       = 10;   // half-width zone around strike
input color  InpPreColor       = clrDodgerBlue;
input color  InpPostColor      = clrDimGray;
input int    InpWidthS         = 1;
input int    InpWidthM         = 1;
input int    InpWidthL         = 2;
input int    InpWidthXL        = 3;
input bool   InpUseCSV         = true; // fetch /expiries.csv for easy parsing

datetime g_last_update = 0;
string   g_prefix      = "EXPZ_";

//--- helpers
double PipInPrice()
{
   if(Digits==3 || Digits==5) return (10*Point);
   return Point;
}

int SizeRankWidth(string rank)
{
   if(rank=="XL") return InpWidthXL;
   if(rank=="L")  return InpWidthL;
   if(rank=="M")  return InpWidthM;
   return InpWidthS;
}

color StateColor(string pre_post)
{
   if(pre_post=="PRE")  return InpPreColor;
   if(pre_post=="POST") return InpPostColor;
   return clrSilver;
}

void DeleteAllObjects()
{
   int total=ObjectsTotal(0,0,-1);
   for(int i=total-1;i>=0;i--)
   {
      string name = ObjectName(0,i,0,-1);
      if(StringFind(name,g_prefix,0)==0)
         ObjectDelete(0,name);
   }
}

bool HttpGet(const string url, string &result)
{
   char data[];
   string headers;
   char res[];
   ResetLastError();
   int status = WebRequest("GET", url, headers, 5000, data, 0, res, headers);
   if(status==200)
   {
      result = CharArrayToString(res,0,ArraySize(res));
      return true;
   }
   Print("WebRequest failed: status=",status," err=",GetLastError()," url=",url);
   return false;
}

void DrawLineAndZone(const string sym, double strike, const string rank, const string pre_post, const string labelText)
{
   string base = g_prefix+sym+"_"+DoubleToString(strike,Digits)+"_"+pre_post;
   string hname = base+"_HL";
   string zname = base+"_Z";
   string tname = base+"_TX";

   color col = StateColor(pre_post);
   int   w   = SizeRankWidth(rank);

   // HLINE
   if(!ObjectFind(0,hname))
   {
      ObjectCreate(0,hname,OBJ_HLINE,0,0, strike);
      ObjectSetInteger(0,hname,OBJPROP_COLOR,col);
      ObjectSetInteger(0,hname,OBJPROP_WIDTH,w);
      ObjectSetInteger(0,hname,OBJPROP_STYLE,STYLE_SOLID);
   }
   else
   {
      ObjectSetDouble(0,hname,OBJPROP_PRICE,strike);
      ObjectSetInteger(0,hname,OBJPROP_COLOR,col);
      ObjectSetInteger(0,hname,OBJPROP_WIDTH,w);
   }

   // Zone rectangle (optional)
   double zone = InpZonePips * PipInPrice();
   datetime t0 = TimeCurrent();
   datetime t1 = t0 + (PeriodSeconds() * 20); // extend a few bars to the right
   if(!ObjectFind(0,zname))
   {
      ObjectCreate(0,zname,OBJ_RECTANGLE,0,t0,strike-zone, t1, strike+zone);
      ObjectSetInteger(0,zname,OBJPROP_BACK,true);
      ObjectSetInteger(0,zname,OBJPROP_COLOR,col);
      ObjectSetInteger(0,zname,OBJPROP_STYLE,STYLE_DOT);
      ObjectSetInteger(0,zname,OBJPROP_WIDTH,1);
      ObjectSetInteger(0,zname,OBJPROP_FILL,false);
   }
   else
   {
      ObjectSetInteger(0,zname,OBJPROP_TIME,0,t0);
      ObjectSetInteger(0,zname,OBJPROP_TIME,1,t1);
      ObjectSetDouble(0,zname,OBJPROP_PRICE,0,strike-zone);
      ObjectSetDouble(0,zname,OBJPROP_PRICE,1,strike+zone);
      ObjectSetInteger(0,zname,OBJPROP_COLOR,col);
   }

   // Text label at the right edge near strike
   if(!ObjectFind(0,tname))
   {
      ObjectCreate(0,tname,OBJ_TEXT,0,t1, strike + zone);
      ObjectSetString(0,tname,OBJPROP_TEXT,labelText);
      ObjectSetInteger(0,tname,OBJPROP_COLOR,col);
      ObjectSetInteger(0,tname,OBJPROP_FONTSIZE,8);
   }
   else
   {
      ObjectSetInteger(0,tname,OBJPROP_TIME,0,t1);
      ObjectSetDouble(0,tname,OBJPROP_PRICE,0,strike + zone);
      ObjectSetString(0,tname,OBJPROP_TEXT,labelText);
      ObjectSetInteger(0,tname,OBJPROP_COLOR,col);
   }
}

int OnInit()
{
   IndicatorShortName("ExpiryZones");
   EventSetTimer(InpRefreshSeconds);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   DeleteAllObjects();
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   // drawing is timer-driven; nothing to do here
   return(rates_total);
}

void OnTimer()
{
   string route = InpUseCSV ? "/expiries.csv?symbol=" : "/expiries?symbol=";
   string url   = InpBaseUrl + route + Symbol();
   string body;
   if(!HttpGet(url, body)) return;

   // Remove old before redrawing
   DeleteAllObjects();

   if(InpUseCSV)
   {
      // Parse CSV
      string lines[]; int n = StringSplit(body, '\n', lines);
      if(n<=1) return;
      // columns: symbol,strike,ccy,notional,size_rank,expiry_ts_utc,spot,distance_pips,pin_score,pre_post
      for(int i=1;i<n;i++)
      {
         string line = StringTrim(lines[i]);
         if(line=="") continue;
         string cols[]; int c = StringSplit(line, ',', cols);
         if(c<10) continue;
         string sym = cols[0];
         double strike = StrToDouble(cols[1]);
         string rank = cols[4];
         string prepost = cols[9];
         string label = StringFormat("%s %.5f | %s | %s", sym, strike, rank, prepost);
         DrawLineAndZone(sym, strike, rank, prepost, label);
      }
   }
   else
   {
      // Minimal JSON parse (quick & dirty): look for "strike": and "size_rank":
      // For production, prefer CSV or a JSON library.
      string recs[];
      int pos=0;
      while(true)
      {
         int i = StringFind(body, "\"strike\":", pos);
         if(i<0) break;
         int j = StringFind(body, ",", i+9);
         double strike = StrToDouble(StringSubstr(body, i+9, j-(i+9)));
         int k = StringFind(body, "\"size_rank\":", j);
         int q1 = StringFind(body, "\"", k+12);
         int q2 = StringFind(body, "\"", q1+1);
         string rank = StringSubstr(body, q1+1, q2-(q1+1));
         int m = StringFind(body, "\"pre_post\":", q2);
         int p1 = StringFind(body, "\"", m+11);
         int p2 = StringFind(body, "\"", p1+1);
         string prepost = StringSubstr(body, p1+1, p2-(p1+1));
         string label = StringFormat("%s %.5f | %s | %s", Symbol(), strike, rank, prepost);
         DrawLineAndZone(Symbol(), strike, rank, prepost, label);
         pos = p2+1;
      }
   }
   g_last_update = TimeCurrent();
}
