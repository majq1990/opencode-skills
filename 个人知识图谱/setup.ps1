# knowledge-graph skill - Windows 一键部署
# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
$SkillDir = $PSScriptRoot
$EnvFile  = Join-Path $SkillDir ".env"
$DataDir  = "$env:USERPROFILE\kg-data"
$LogOut   = Join-Path $DataDir "lightrag-server.out.log"
$LogErr   = Join-Path $DataDir "lightrag-server.err.log"
$PidFile  = Join-Path $DataDir "lightrag-server.pid"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; exit 1 }

# ---------- 0. 前置检查 ----------
Info "检查前置依赖..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker 未安装" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Fail "Python 未安装" }
if (-not (Test-Path $EnvFile)) { Fail ".env 不存在: $EnvFile" }

# ---------- 1. 加载 .env 到当前进程 ----------
Info "加载 .env -> 进程环境变量"
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $idx = $line.IndexOf("=")
        $k = $line.Substring(0, $idx).Trim()
        $v = $line.Substring($idx + 1).Trim()
        [Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
}

# LightRAG 1.x 用 WORKING_DIR 而不是 RAG_STORAGE_DIR
[Environment]::SetEnvironmentVariable("WORKING_DIR", $env:RAG_STORAGE_DIR, "Process")
[Environment]::SetEnvironmentVariable("INPUT_DIR",   $env:RAG_STORAGE_DIR, "Process")

# LightRAG splash screen 含 emoji，强制 Python 用 UTF-8 输出，否则 GBK 报 UnicodeEncodeError
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "Process")
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "Process")

New-Item -ItemType Directory -Force $DataDir | Out-Null

# LightRAG 1.4.x 要求启动目录含 .env，否则交互式问 yes/NO 卡住
Copy-Item $EnvFile (Join-Path $DataDir ".env") -Force

# ---------- 2. 检查 Neo4j ----------
Info "检查 Neo4j 容器..."
$neoName = (docker ps --filter "name=neo4j" --format "{{.Names}}") -split "`n" | Where-Object { $_ -match "neo4j" } | Select-Object -First 1
if ($neoName) {
    Ok "Neo4j 容器在跑: $neoName"
} else {
    Info "未发现运行中的 Neo4j，尝试 docker compose up -d"
    docker compose -f (Join-Path $SkillDir "docker-compose.yml") up -d
    if ($LASTEXITCODE -ne 0) { Fail "Neo4j 启动失败" }
}

# ---------- 3. 安装 LightRAG ----------
$pkg = pip show lightrag-hku 2>$null
if (-not $pkg) {
    Info "安装 lightrag-hku[api]（首次需几分钟）..."
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "lightrag-hku[api]" neo4j
    if ($LASTEXITCODE -ne 0) { Fail "lightrag-hku 安装失败" }
} else {
    Ok "lightrag-hku 已安装"
}

# ---------- 4. 启动 LightRAG Server ----------
# 如已在跑同端口则跳过
$port = $env:LIGHTRAG_PORT
if (-not $port) { $port = "9621" }
$listening = (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
if ($listening) {
    Warn "端口 $port 已被占用，可能 LightRAG Server 已在跑（跳过启动）"
} else {
    Info "启动 LightRAG Server -> :$port"
    # 用 python -m 而不是裸 lightrag-server，避免 PATH 问题
    $proc = Start-Process -FilePath "python" `
        -ArgumentList "-m","lightrag.api.lightrag_server","--host","0.0.0.0","--port",$port,"--working-dir",$DataDir,"--input-dir",$DataDir `
        -WorkingDirectory $DataDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $LogOut `
        -RedirectStandardError  $LogErr `
        -PassThru
    $proc.Id | Out-File $PidFile
    Info "PID = $($proc.Id), 日志: $LogOut / $LogErr"

    # 健康检查
    Info "等待健康检查..."
    $ok = $false
    for ($i = 1; $i -le 30; $i++) {
        try {
            Invoke-WebRequest "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 3 | Out-Null
            $ok = $true; break
        } catch {
            Start-Sleep 2
        }
    }
    if ($ok) { Ok "LightRAG Server 启动成功" } else { Warn "30 秒未通过健康检查，请查日志: $LogErr" }
}

# ---------- 5. 汇总 ----------
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " 知识图谱 Skill 部署完成" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host " LightRAG Web UI : http://localhost:$port"
Write-Host " LightRAG API doc: http://localhost:$port/docs"
Write-Host " Neo4j Browser   : http://localhost:7474  (neo4j / neo4j123)"
Write-Host " 数据目录        : $DataDir"
Write-Host " 配置文件        : $EnvFile"
Write-Host ""
Write-Host " 测试:"
Write-Host "   python `"$SkillDir\kg_tool.py`" status"
Write-Host "   python `"$SkillDir\kg_tool.py`" ingest --text 'Python 是 Guido van Rossum 在 1991 年发布的高级编程语言'"
Write-Host "   python `"$SkillDir\kg_tool.py`" query '谁创建了 Python？'"
Write-Host ""
