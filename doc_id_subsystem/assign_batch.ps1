param(
    [int]$BatchSize = 50,
    [string]$Category = "AUTO"
)
Write-Host "Batch assigning doc IDs..." -ForegroundColor Cyan
Write-Host "  Batch size: $BatchSize" -ForegroundColor Yellow
Write-Host "  Category: $Category" -ForegroundColor Yellow
cd core
python batch_assign_docids.py --batch-size $BatchSize --category $Category
