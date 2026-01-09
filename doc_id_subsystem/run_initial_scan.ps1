# Initial repository scan for doc IDs
Write-Host "Starting Doc ID initial scan..." -ForegroundColor Cyan
cd core
python doc_id_scanner.py --repo-root "..\..\"
Write-Host "`nScan complete. Check registry/docs_inventory.jsonl" -ForegroundColor Green
