# doc_id: DOC-DOC-0067
# DOC_ID: DOC-SERVICE-0022
"""
Replay a CSV of ticks to EAFIX data-ingestor for performance testing.

CSV columns: ts,symbol,bid,ask,mid,source
Endpoint: http://localhost:8081/ingest/manual (data-ingestor manual ingestion)

Example CSV format:
ts,symbol,bid,ask,mid,source
1634567890.123,EURUSD,1.1545,1.1547,1.1546,MT4
1634567891.456,GBPUSD,1.3721,1.3723,1.3722,MT4
"""
import csv, sys, json, time, urllib.request
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Replay tick data to EAFIX data-ingestor')
    parser.add_argument('csv_file', help='CSV file with tick data')
    parser.add_argument('--url', default='http://localhost:8081/ingest/manual', 
                       help='Data ingestor endpoint (default: http://localhost:8081/ingest/manual)')
    parser.add_argument('--delay', type=float, default=0.01, 
                       help='Delay between ticks in seconds (default: 0.01)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()

    if not args.csv_file:
        print("Usage: python scripts/replay/replay_ticks.py <csv_file>"); sys.exit(1)

    fpath = args.csv_file
    url = args.url
    print(f"Replaying ticks from {fpath} to {url}")
    print(f"Delay between ticks: {args.delay}s")
    
    tick_count = 0
    success_count = 0
    start_time = time.time()
    
    try:
        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tick_count += 1
                
                # Convert timestamp if it's a string
                ts = row.get('ts', '')
                if ts and not ts.replace('.', '').isdigit():
                    # Try to parse datetime string
                    try:
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        ts = dt.timestamp()
                    except:
                        ts = time.time()  # fallback to current time
                
                data = {
                    'timestamp': float(ts) if ts else time.time(),
                    'symbol': row.get('symbol', 'EURUSD'),
                    'bid': float(row.get('bid', 0)),
                    'ask': float(row.get('ask', 0)),
                    'source': row.get('source', 'replay')
                }
                
                req = urllib.request.Request(url, 
                                           data=json.dumps(data).encode(), 
                                           headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=5) as r:
                        if r.status == 200:
                            success_count += 1
                        if args.verbose:
                            print(f"Tick {tick_count}: {data['symbol']} {data['bid']}/{data['ask']} -> {r.status}")
                except Exception as e:
                    if args.verbose:
                        print(f"Tick {tick_count} failed: {e}")
                
                time.sleep(args.delay)
                
                # Progress report every 100 ticks
                if tick_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = tick_count / elapsed if elapsed > 0 else 0
                    print(f"Progress: {tick_count} ticks, {success_count} successful ({rate:.1f} ticks/s)")
    
    except KeyboardInterrupt:
        print("\nReplay interrupted by user")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)
    
    elapsed = time.time() - start_time
    success_rate = (success_count / tick_count * 100) if tick_count > 0 else 0
    avg_rate = tick_count / elapsed if elapsed > 0 else 0
    
    print(f"\nReplay complete:")
    print(f"  Total ticks: {tick_count}")
    print(f"  Successful: {success_count} ({success_rate:.1f}%)")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Average rate: {avg_rate:.1f} ticks/s")

if __name__ == "__main__":
    main()
