param(
    [Parameter(Mandatory, Position=0)]
    [string]$InputFile,

    [Parameter(Mandatory, Position=1)]
    [string]$OutputFile,

    [ValidateSet("palette","gifski")]
    [string]$Method = "palette",

    [int]$Fps = 15,
    [int]$Width = 800,
    [int]$Quality = 90,

    [string]$StartTime = "",
    [string]$EndTime = "",

    [string]$Crop = "",

    [string]$Subtitle = "",

    [int]$MaxColors = 256
)

if (-not (Test-Path $InputFile)) {
    Write-Error "输入文件不存在: $InputFile"
    exit 1
}

$filter = "fps=$Fps,scale=$($Width):-1:flags=lanczos"
if ($Crop -ne "") { $filter = "crop=$Crop,$filter" }
if ($Subtitle -ne "") {
    $escapedPath = $Subtitle -replace '\\', '/' -replace ':', '\\:'
    $filter = "subtitles=$escapedPath:force_style='FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=20',$filter"
}

$trim = ""
if ($StartTime -ne "") { $trim += " -ss $StartTime" }
if ($EndTime -ne "")   { $trim += " -to $EndTime" }

$tempDir = ""
try {
    if ($Method -eq "palette") {
        Write-Host "[palette] ffmpeg 调色板法: ${Fps}fps x ${Width}w"
        ffmpeg $trim -i "$InputFile" -vf "$filter,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" -y "$OutputFile"
        if ($LASTEXITCODE -ne 0) { throw "ffmpeg palette 编码失败" }
    } else {
        Write-Host "[gifski] 高质量编码: ${Fps}fps x ${Width}w quality=$Quality"
        $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "gifski_$PID"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        $framePattern = Join-Path $tempDir "frame_%04d.png"
        ffmpeg $trim -i "$InputFile" -vf "$filter" "$framePattern"
        if ($LASTEXITCODE -ne 0) { throw "ffmpeg 抽帧失败" }
        gifski -o "$OutputFile" --fps $Fps --quality $Quality --width $Width "$(Join-Path $tempDir 'frame_*.png')"
        if ($LASTEXITCODE -ne 0) { throw "gifski 编码失败" }
    }

    $size = (Get-Item $OutputFile).Length
    Write-Host "GIF 生成完成: $("{0:N2}" -f ($size/1MB))MB → $OutputFile"
} catch {
    Write-Error $_.Exception.Message
    exit 1
} finally {
    if ($tempDir -and (Test-Path $tempDir)) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
