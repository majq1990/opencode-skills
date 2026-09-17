param(
    [Parameter(Mandatory, Position=0)]
    [string]$InputFile,

    [Parameter(Mandatory, Position=1)]
    [string]$OutputFile,

    [ValidateSet("L1","L2","L3")]
    [string]$Level = "L1",

    [int]$Lossy = 60,
    [int]$Colors = 128,
    [int]$ResizeWidth = 600
)

if (-not (Test-Path $InputFile)) {
    Write-Error "输入文件不存在: $InputFile"
    exit 1
}

$sizeBefore = (Get-Item $InputFile).Length

switch ($Level) {
    "L1" {
        Write-Host "[L1] 无损优化: gifsicle -O3"
        gifsicle -O3 "$InputFile" -o "$OutputFile"
    }
    "L2" {
        Write-Host "[L2] 有损压缩 --lossy=$Lossy"
        gifsicle -O3 --lossy=$Lossy "$InputFile" -o "$OutputFile"
    }
    "L3" {
        Write-Host "[L3] 激进压缩 --lossy=$Lossy --colors $Colors --resize-width $ResizeWidth"
        gifsicle -O3 --lossy=$Lossy --colors $Colors --resize-width $ResizeWidth "$InputFile" -o "$OutputFile"
    }
}

if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputFile)) {
    $sizeAfter = (Get-Item $OutputFile).Length
    $ratio = [math]::Round(($sizeAfter / $sizeBefore) * 100, 1)
    Write-Host "压缩完成: $("{0:N2}" -f ($sizeBefore/1MB))MB → $("{0:N2}" -f ($sizeAfter/1MB))MB ($ratio%)"
} else {
    Write-Error "压缩失败 (exit code: $LASTEXITCODE)"
    exit 1
}
