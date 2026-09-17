@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title ibility 依赖修复工具 (Windows 原生版)

echo ==============================================
echo    ibility-platform 依赖修复工具
echo    Windows 原生版（无需 Python）
echo ==============================================
echo.

REM ---------- 1. 定位源码根目录 ----------
set "ROOT=%~1"
if "%ROOT%"=="" set "ROOT=%CD%"

REM 向上查找 backend\pom.xml
set "SRC="
set "SEARCH=%ROOT%"
:findroot
if exist "%SEARCH%\backend\pom.xml" (
    set "SRC=%SEARCH%"
    goto rootfound
)
for %%i in ("%SEARCH%") do set "PARENT=%%~dpi"
set "SEARCH=%PARENT%"
if not "%SEARCH%"=="" goto findroot
set "SRC="
:rootfound

if "%SRC%"=="" (
    echo [FAIL] 未找到源码根目录（缺少 backend\pom.xml）
    echo        用法: fix_repo.bat ^<源码目录^>   或  将本工具放在platform-source目录下双击
    pause
    exit /b 1
)
echo [1/5] 源码根目录: %SRC%
cd /d "%SRC%"

REM ---------- 2. 检查环境 ----------
echo.
echo [2/5] 检查运行环境...
set "MVN="
where mvn >nul 2>nul && set "MVN=mvn"
if "%MVN%"=="" (
    if exist "C:\Program Files\apache-maven\bin\mvn.cmd" set "MVN=C:\Program Files\apache-maven\bin\mvn.cmd"
    if exist "D:\tools\apache-maven\bin\mvn.cmd" set "MVN=D:\tools\apache-maven\bin\mvn.cmd"
)
if "%MVN%"=="" (
    echo [FAIL] 未找到 mvn，请先安装 Maven 3.6+ 并加入 PATH
    pause
    exit /b 1
)
set "JAVA="
where java >nul 2>nul && set "JAVA=java"
if "%JAVA%"=="" (
    echo [FAIL] 未找到 java，请先安装 JDK 1.8 并加入 PATH
    pause
    exit /b 1
)
echo   [OK] mvn : %MVN%
for /f "delims=" %%v in ('"%MVN%" --version 2^>nul') do echo   %%v
echo   [OK] java: %JAVA%

REM ---------- 2.5 修复 .gitignore ----------
echo.
echo [2.5/5] 检查 .gitignore 中 *.jar 过滤...
if exist "%SRC%\.gitignore" (
    findstr /i /c:"*.jar" "%SRC%\.gitignore" >nul 2>nul
    if %errorlevel%==0 (
        REM 删除含 *.jar 的行
        powershell -NoProfile -Command "(Get-Content -Encoding UTF8 '%SRC%\.gitignore') | Where-Object { $_ -notmatch '\.jar' } | Set-Content -Encoding UTF8 '%SRC%\.gitignore'"
        echo   [OK] 已移除 .gitignore 中的 *.jar 过滤（否则 repo\ 依赖无法提交）
    ) else (
        echo   [SKIP] .gitignore 已无 *.jar 过滤
    )
) else (
    echo   [SKIP] 未发现 .gitignore
)

REM ---------- 3. 清理 _remote.repositories（离线构建前置） ----------
echo.
echo [3/6] 清理 repo\ 离线构建元数据...
if exist "%SRC%\repo" (
    powershell -NoProfile -Command "Get-ChildItem -Path '%SRC%\repo' -Recurse -Force -Include '_remote.repositories','*.lastUpdated' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue | Out-Null; $c=(Get-ChildItem -Path '%SRC%\repo' -Recurse -Force -Include '_remote.repositories','*.lastUpdated' -ErrorAction SilentlyContinue).Count; Write-Host ('清理完成, 剩余数: ' + $c)"
    echo   [OK] 已清理 _remote.repositories（离线构建必备，否则报 not downloaded before）
) else (
    echo   [SKIP] 未发现 repo\，跳过
)

REM ---------- 4. 扫描 repo/ 缺失 ----------
echo.
echo [4/6] 扫描 repo\ 缺失依赖...
if not exist "%SRC%\repo" (
    echo   repo\ 目录不存在，将新建
    mkdir "%SRC%\repo"
) else (
    set "JARCOUNT=0"
    for /r "%SRC%\repo" %%f in (*.jar) do set /a JARCOUNT+=1
    echo   repo\ 当前 jar 数量: !JARCOUNT!
)

REM 扫描"只有 pom 没有 jar"的依赖
set "MISSING_COUNT=0"
for /r "%SRC%\repo" %%f in (*.pom) do (
    set "POMFILE=%%f"
    set "IS_POMTYPE="
    findstr /i "<packaging>pom</packaging>" "%%f" >nul 2>nul && set "IS_POMTYPE=1"
    if not defined IS_POMTYPE (
        set "JARCHECK=%%~dpn0.jar"
        if not exist "!JARCHECK!" (
            set /a MISSING_COUNT+=1
            if !MISSING_COUNT! LEQ 20 (
                echo   [缺] %%~nx0  ... 缺 jar
            )
        )
    )
)
if %MISSING_COUNT% GTR 0 (
    echo   共扫描到 !MISSING_COUNT! 个缺 jar 的依赖（首次可能需要下载全部）
) else (
    echo   repo\ 现有依赖 jar 齐全
)

REM ---------- 5. 网络检测 + VPN 提示 ----------
echo.
echo [5/6] 检查内网 Nexus 连通性...
echo   ping npm.egova.com.cn ...
ping -n 1 -w 3000 npm.egova.com.cn >nul 2>nul
if %errorlevel%==0 (
    echo   [OK] 内网可达: npm.egova.com.cn:18081
    goto netok
)
REM ping 可能被禁，再试 TCP 端口
powershell -NoProfile -Command "Test-NetConnection -ComputerName npm.egova.com.cn -Port 18081 -InformationLevel Quiet -WarningAction SilentlyContinue" >"%TEMP%\ibility_net.tmp" 2>nul
set /p NETOK=<"%TEMP%\ibility_net.tmp"
if "%NETOK%"=="True" (
    echo   [OK] 内网可达: npm.egova.com.cn:18081 (TCP)
    goto netok
)

echo.
echo   [!!] 无法连接内网 Nexus: npm.egova.com.cn:18081
echo.
echo   *** 请先连接公司 VPN，再重新运行本工具! ***
echo.
echo   常见 VPN: EasyConnect / ZTNA / 客户端输入公司网关地址
pause
exit /b 1

:netok
REM ---------- 6. 执行 go-offline 下载 ----------
echo.
echo [6/6] 下载项目全部依赖到 repo\ ...
echo   此步骤将解析全部依赖（含传递依赖），首次下载耗时较长...
echo.
call "%MVN%" -f "%SRC%\backend\pom.xml" dependency:go-offline -Dmaven.repo.local="%SRC%\repo" -Dmaven.source.skip=true -DskipTests
if %errorlevel% NEQ 0 (
    echo.
    echo   [FAIL] 依赖下载未完全成功，请查看上方报错。
    echo     1) 部分私有依赖在 Nexus 上不存在，需联系平台维护者上传
    echo     2) VPN 不稳定，请重连后重新运行
    pause
    exit /b 1
)

set "JARCOUNT2=0"
for /r "%SRC%\repo" %%f in (*.jar) do set /a JARCOUNT2+=1
echo.
echo   [SUCCESS] 依赖下载完成！repo\ 中 jar 数量: %JARCOUNT2%
echo.
echo   --------------------------------------------
echo   下一步构建命令:
echo     mvn -f backend\pom.xml clean install -U -Dmaven.test.skip=true -Dmaven.repo.local=repo -Dmaven.source.skip=true -pl modules\egova-boot-ibility-service -am
echo.
echo   产物: backend\modules\egova-boot-ibility-service\target\egova-boot-ibility-service-1.0.0.jar
echo   --------------------------------------------
pause