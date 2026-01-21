// doc_id: DOC-LEGACY-0100
//+------------------------------------------------------------------+
//| Contract Parsers for EAFIX Trading System                        |
//| Schema-aware parsing and serialization for JSON contracts        |
//| Generated from contracts/events/ schemas - DO NOT EDIT MANUALLY  |
//+------------------------------------------------------------------+

#property strict

//+------------------------------------------------------------------+
//| PriceTick structure for MQL4                                     |
//| Corresponds to PriceTick@1.0 schema                              |
//+------------------------------------------------------------------+
struct PriceTick_v1 {
    datetime timestamp;      // UTC timestamp of the tick
    string   symbol;         // Currency pair symbol (e.g., EURUSD)
    double   bid;            // Bid price
    double   ask;            // Ask price
    int      volume;         // Optional tick volume (-1 if not available)
};

//+------------------------------------------------------------------+
//| Signal structure for MQL4                                        |
//| Corresponds to Signal@1.0 schema                                 |
//+------------------------------------------------------------------+
enum SignalSide {
    SIGNAL_BUY = 0,
    SIGNAL_SELL = 1
};

struct Signal_v1 {
    string      id;                   // UUID as string
    datetime    timestamp;            // UTC timestamp of signal generation
    string      symbol;               // Currency pair symbol
    SignalSide  side;                // Trading direction
    double      confidence;           // Signal confidence score (0-1)
    string      explanation;          // Optional explanation
    string      source_indicators;    // Comma-separated indicator list
    datetime    expiry;              // Signal expiry timestamp (0 if no expiry)
};

//+------------------------------------------------------------------+
//| OrderIntent structure for MQL4                                   |
//| Corresponds to OrderIntent@1.2 schema                            |
//+------------------------------------------------------------------+
enum OrderSide {
    ORDER_LONG = 0,
    ORDER_SHORT = 1
};

struct OrderIntent_v1_2 {
    string      id;              // UUID as string
    string      signal_id;       // Source signal UUID as string
    datetime    timestamp;       // UTC timestamp
    string      symbol;          // Currency pair symbol
    OrderSide   side;           // Order side
    double      quantity;        // Order quantity/lot size
    double      price;          // Optional limit price (0 if market)
    double      stop_loss;      // Stop loss price (0 if none)
    double      take_profit;    // Take profit price (0 if none)
    datetime    expiry;         // Order expiry time (0 if GTC)
    string      reentry_key;    // Re-entry tracking key
};

//+------------------------------------------------------------------+
//| ExecutionReport structure for MQL4                               |
//| Corresponds to ExecutionReport@1.0 schema                        |
//+------------------------------------------------------------------+
enum ExecutionStatus {
    EXEC_PENDING = 0,
    EXEC_SUBMITTED = 1,
    EXEC_FILLED = 2,
    EXEC_PARTIAL_FILL = 3,
    EXEC_REJECTED = 4,
    EXEC_CANCELED = 5,
    EXEC_EXPIRED = 6
};

struct ExecutionReport_v1 {
    string           order_intent_id;    // Source order intent UUID
    string           broker_order_id;    // Broker's order ID
    datetime         timestamp;          // UTC timestamp
    ExecutionStatus  status;            // Execution status
    double           filled_quantity;    // Filled quantity
    double           filled_price;      // Average fill price
    double           commission;        // Commission charged
    string           error_message;     // Error message if rejected
};

//+------------------------------------------------------------------+
//| Parse PriceTick from JSON string                                 |
//| Returns true on success, false on parsing error                  |
//+------------------------------------------------------------------+
bool ParsePriceTick(string json_str, PriceTick_v1 &tick) {
    // Reset structure
    tick.timestamp = 0;
    tick.symbol = "";
    tick.bid = 0.0;
    tick.ask = 0.0;
    tick.volume = -1;
    
    // Simple JSON parsing - in production, use a proper JSON library
    // This is a minimal implementation for demonstration
    
    // Extract timestamp (ISO 8601 format)
    string timestamp_str = ExtractJsonValue(json_str, "timestamp");
    tick.timestamp = StringToTime(timestamp_str);
    
    // Extract symbol
    tick.symbol = ExtractJsonValue(json_str, "symbol");
    if (StringLen(tick.symbol) != 6) return false;
    
    // Extract prices with numeric safety
    string bid_str = ExtractJsonValue(json_str, "bid");
    string ask_str = ExtractJsonValue(json_str, "ask");
    
    tick.bid = SafeStringToDouble(bid_str);
    tick.ask = SafeStringToDouble(ask_str);
    
    if (tick.bid <= 0 || tick.ask <= 0 || tick.bid >= tick.ask) return false;
    
    // Extract optional volume
    string volume_str = ExtractJsonValue(json_str, "volume");
    if (volume_str != "") {
        tick.volume = (int)StringToInteger(volume_str);
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Serialize PriceTick to JSON string                               |
//| Returns formatted JSON string                                    |
//+------------------------------------------------------------------+
string SerializePriceTick(const PriceTick_v1 &tick) {
    string json = "{";
    json += "\"timestamp\":\"" + TimeToString(tick.timestamp, TIME_DATE|TIME_SECONDS) + "\",";
    json += "\"symbol\":\"" + tick.symbol + "\",";
    json += "\"bid\":" + DoubleToString(tick.bid, 5) + ",";
    json += "\"ask\":" + DoubleToString(tick.ask, 5);
    
    if (tick.volume >= 0) {
        json += ",\"volume\":" + IntegerToString(tick.volume);
    }
    
    json += "}";
    return json;
}

//+------------------------------------------------------------------+
//| Parse Signal from JSON string                                    |
//+------------------------------------------------------------------+
bool ParseSignal(string json_str, Signal_v1 &signal) {
    signal.id = ExtractJsonValue(json_str, "id");
    signal.symbol = ExtractJsonValue(json_str, "symbol");
    signal.explanation = ExtractJsonValue(json_str, "explanation");
    signal.source_indicators = ExtractJsonValue(json_str, "source_indicators");
    
    string timestamp_str = ExtractJsonValue(json_str, "timestamp");
    signal.timestamp = StringToTime(timestamp_str);
    
    string side_str = ExtractJsonValue(json_str, "side");
    signal.side = (side_str == "BUY") ? SIGNAL_BUY : SIGNAL_SELL;
    
    string confidence_str = ExtractJsonValue(json_str, "confidence");
    signal.confidence = SafeStringToDouble(confidence_str);
    
    if (signal.confidence < 0.0 || signal.confidence > 1.0) return false;
    
    string expiry_str = ExtractJsonValue(json_str, "expiry");
    signal.expiry = (expiry_str != "") ? StringToTime(expiry_str) : 0;
    
    return (signal.id != "" && signal.symbol != "" && StringLen(signal.symbol) == 6);
}

//+------------------------------------------------------------------+
//| Serialize OrderIntent to JSON string                             |
//+------------------------------------------------------------------+
string SerializeOrderIntent(const OrderIntent_v1_2 &intent) {
    string json = "{";
    json += "\"id\":\"" + intent.id + "\",";
    json += "\"signal_id\":\"" + intent.signal_id + "\",";
    json += "\"timestamp\":\"" + TimeToString(intent.timestamp, TIME_DATE|TIME_SECONDS) + "\",";
    json += "\"symbol\":\"" + intent.symbol + "\",";
    json += "\"side\":\"" + ((intent.side == ORDER_LONG) ? "LONG" : "SHORT") + "\",";
    json += "\"quantity\":" + DoubleToString(intent.quantity, 2);
    
    if (intent.price > 0) {
        json += ",\"price\":" + DoubleToString(intent.price, 5);
    }
    if (intent.stop_loss > 0) {
        json += ",\"stop_loss\":" + DoubleToString(intent.stop_loss, 5);
    }
    if (intent.take_profit > 0) {
        json += ",\"take_profit\":" + DoubleToString(intent.take_profit, 5);
    }
    if (intent.expiry > 0) {
        json += ",\"expiry\":\"" + TimeToString(intent.expiry, TIME_DATE|TIME_SECONDS) + "\"";
    }
    if (intent.reentry_key != "") {
        json += ",\"reentry_key\":\"" + intent.reentry_key + "\"";
    }
    
    json += "}";
    return json;
}

//+------------------------------------------------------------------+
//| Helper: Extract JSON value (simple implementation)               |
//| In production, use a proper JSON parsing library                 |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key) {
    string search = "\"" + key + "\":";
    int start = StringFind(json, search);
    if (start == -1) return "";
    
    start += StringLen(search);
    
    // Skip whitespace
    while (start < StringLen(json) && (StringGetCharacter(json, start) == ' ' || 
           StringGetCharacter(json, start) == '\t')) {
        start++;
    }
    
    // Handle quoted strings
    if (StringGetCharacter(json, start) == '"') {
        start++; // Skip opening quote
        int end = start;
        while (end < StringLen(json) && StringGetCharacter(json, end) != '"') {
            end++;
        }
        return StringSubstr(json, start, end - start);
    }
    
    // Handle numbers and other values
    int end = start;
    while (end < StringLen(json)) {
        ushort ch = StringGetCharacter(json, end);
        if (ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\n') {
            break;
        }
        end++;
    }
    
    return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
//| Safe string to double conversion with numeric safety             |
//| Handles potential precision issues                               |
//+------------------------------------------------------------------+
double SafeStringToDouble(string str) {
    if (str == "" || str == "null") return 0.0;
    
    double value = StringToDouble(str);
    
    // Validate the conversion worked properly
    if (value == 0.0 && str != "0" && str != "0.0") {
        Print("Warning: Failed to convert string to double: ", str);
        return 0.0;
    }
    
    return NormalizeDouble(value, 5); // Standard forex precision
}

//+------------------------------------------------------------------+
//| Validate currency pair format                                    |
//+------------------------------------------------------------------+
bool IsValidCurrencyPair(string symbol) {
    if (StringLen(symbol) != 6) return false;
    
    for (int i = 0; i < 6; i++) {
        ushort ch = StringGetCharacter(symbol, i);
        if (ch < 'A' || ch > 'Z') return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Round-trip test for data integrity                               |
//| Returns true if serialize->parse produces identical data         |
//+------------------------------------------------------------------+
bool TestPriceTickRoundTrip() {
    PriceTick_v1 original, parsed;
    
    original.timestamp = TimeCurrent();
    original.symbol = "EURUSD";
    original.bid = 1.09435;
    original.ask = 1.09438;
    original.volume = 100;
    
    string json = SerializePriceTick(original);
    bool success = ParsePriceTick(json, parsed);
    
    if (!success) {
        Print("Round-trip test failed: Parse error");
        return false;
    }
    
    if (original.symbol != parsed.symbol ||
        MathAbs(original.bid - parsed.bid) > 0.00001 ||
        MathAbs(original.ask - parsed.ask) > 0.00001 ||
        original.volume != parsed.volume) {
        Print("Round-trip test failed: Data mismatch");
        return false;
    }
    
    Print("PriceTick round-trip test passed");
    return true;
}

//+------------------------------------------------------------------+
//| Initialize contract parsers - call this on EA init               |
//+------------------------------------------------------------------+
bool InitContractParsers() {
    Print("Initializing EAFIX Contract Parsers v1.0");
    
    // Run self-tests
    if (!TestPriceTickRoundTrip()) {
        Print("ERROR: Contract parser self-test failed");
        return false;
    }
    
    Print("Contract parsers initialized successfully");
    return true;
}