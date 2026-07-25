param(
    [Parameter(Mandatory)]
    [string]$InputDir,

    [string]$OutputDir = "",

    [ValidateSet("L1","L2","L3")]
    [string]$Level = "L1",

    [string]$Pattern = "*.gif",

    [int]$Lossy = 60
)

if (-not (Test-Path $InputDir)) {
    Write-Error "输入目录不存在: $InputDir"
    exit 1
}

if ($OutputDir -eq "") { $OutputDir = $InputDir }
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

$files = Get-ChildItem -Path $InputDir -Filter $Pattern
if ($files.Count -eq 0) {
    Write-Host "目录中没有匹配 $Pattern 的文件"
    exit 0
}

$totalBefore = 0
$totalAfter = 0

foreach ($f in $files) {
    $outFile = Join-Path $OutputDir "$($f.BaseName)_$Level$($f.Extension)"
    $sizeBefore = $f.Length
    $totalBefore += $sizeBefore

    Write-Host ("处理: {0} (Level: {1}, lossy: {2})" -f $f.Name, $Level, $Lossy)

    switch ($Level) {
        "L1" { gifsicle -O3 $f.FullName -o $outFile }
        "L2" { gifsicle -O3 --lossy=$Lossy $f.FullName -o $outFile }
        "L3" { gifsicle -O3 --lossy=$Lossy --colors 128 --resize-width 600 $f.FullName -o $outFile }
    }

    if ($LASTEXITCODE -eq 0) {
        $sizeAfter = (Get-Item $outFile).Length
        $totalAfter += $sizeAfter
        $ratio = [math]::Round(($sizeAfter / $sizeBefore) * 100, 1)
        Write-Host ("  → {0:N2}MB ({1}%)" -f ($sizeAfter/1MB), $ratio)
    } else {
        Write-Warning "  ✗ 失败 (exit code: $LASTEXITCODE)"
    }
}

Write-Host ("`n批量处理完成: {0} 个文件" -f $files.Count)
Write-Host ("总计: {0:N2}MB → {1:N2}MB" -f ($totalBefore/1MB), ($totalAfter/1MB))
