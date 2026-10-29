# 把 <workdir> 下所有 .doc 转成 .docx (Word COM, wdFormatXMLDocument=16)
# 用法: pwsh doc2docx.ps1 <workdir>
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = $args[0]
if (-not $root) { Write-Host "Usage: pwsh doc2docx.ps1 <workdir>"; exit 1 }

$docs = Get-ChildItem -Path $root -Recurse -Filter '*.doc' | Where-Object { -not $_.Name.EndsWith('.docx') }
if ($docs.Count -eq 0) { Write-Host "无 .doc 文件需要转换"; exit 0 }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
foreach ($f in $docs) {
  $target = $f.FullName -replace '\.doc$', '.docx'
  Write-Host "convert $($f.FullName)"
  $doc = $word.Documents.Open($f.FullName)
  $doc.SaveAs([ref]$target, [ref]16)
  $doc.Close()
  Remove-Item $f.FullName  # 删除原 .doc
  Write-Host "  -> $target"
}
$word.Quit()
