@echo off

set VER=1.0.1
rem 需要选择应用和版本
set "WEB_APPS=linglong wukong dex evaluation bigdata fac sg baseservice all"
rem TODO:此处版本为web的版本，版本号不采用日期
set "WEB_VERS=1.0.1"

set "default_domain=http://dl.egova.com.cn:8080"
set "fast_domain=http://oneops.egova.com.cn:8093"
set "internal_domain=http://172.16.4.100:82"


call:download

rem 下载索引文件
:download_fileslist
	set "web_select_app=%1"
	if "%web_select_app%" == "" (
		set "web_select_app=%WEB_APPS[0]%"
	)
	set "web_select_version=%2"
	set "os_select=%3"
    set "down_flag=0"

	rem echo "web_select_app=!web_select_app!"
	rem echo "web_select_version=!web_select_version!"

	if !web_select_app! == "linglong" (
		set "down_flag=1"
	)
	if !web_select_app! == "wukong" (
		set "down_flag=1"
	)
	if !web_select_app! == "dex" (
		set "down_flag=1"
	)
	if !web_select_app! == "evaluation" (
		set "down_flag=1"
	)
	if !web_select_app! == "bigdata" (
		set "down_flag=1"
	)
	if !web_select_app! == "fac" (
		set "down_flag=1"
	)
	if !web_select_app! == "sg" (
		set "down_flag=1"
	)
	if !web_select_app! == "baseservice" (
		set "down_flag=1"
	)
	if !web_select_app! == "all" (
		set "down_flag=1"
	)

	if "!down_flag!" == "1" (
	    del oneinstall_v2-files-*.ini /Q >nul 2>nul
	    if !web_select_app! NEQ "all" (
	        wget -c %domain%/one/v2/%os_select%/oneinstall_v2-files-web-%web_select_app%.ini --http-user=%user% --http-passwd=%password%
	    ) else (
	        wget -c %domain%/one/v2/%os_select%/oneinstall_v2-files-web-all.ini --http-user=%user% --http-passwd=%password%
	    )
	    if "!download_type!" == "1" (
	        wget -c %domain%/one/v2/%os_select%/oneinstall_v2-files-base.ini --http-user=%user% --http-passwd=%password%
	    )
	    if "!download_type!" == "2" (
	        wget -c %domain%/one/v2/%os_select%/oneinstall_v2-files-base.ini --http-user=%user% --http-passwd=%password%
	        wget -c %domain%/one/v2/%os_select%/oneinstall_v2-files-env-base.ini --http-user=%user% --http-passwd=%password%
	    )
	)

	if "!down_flag!" == "0" (
		echo "请选择正确的脚本类型！"
		exit
	)
goto:EOF


rem 根据files文件下载
:download_by_fileslist
	setlocal EnableDelayedExpansion
	for /f %%i in ('dir oneinstall_v2-files*.ini /b') do (
			rem echo %%i
			del %%i.temp >nul 2>nul
			for /f "delims=" %%f in ('type %%i') do (
				rem call set "file=%%f:e=1"
				set "file=%%f"
				if not "!file:~0,1!" == "[" (
					set "file=!file:${VER}=%VER%!"
					rem echo !file!
					wget -c !domain!/one/v2/!file! --http-user=%user% --http-passwd=%password%
				)
				echo !file! >> %%i.temp
			)
			copy "%%i" "%%i.bak" >nul 2>nul
			move "%%i.temp" "%%i"
		)
	endlocal
goto:EOF

:display_os_select
		echo "请选择操作系统的版本, 目前只支持centos7.x"
        echo "1 : centos7.x"
		choice /c:1 "/m:请选择:   "
		set "os_select=el7"
		set "os_select_info=centos7.x"
goto:EOF

:display_web_app_select
	echo "请选择待下载的web应用"
	set idx=0
	set "keys="
	setlocal enabledelayedexpansion
	for %%d in (%WEB_APPS%) do (
		set "WEB_APPS[!idx!]=%d"
		set /a idx+=1
		echo "!idx! : %%d"
		set "keys=!keys!!idx!"
	)
	endlocal & set "keys=%keys%"& set "idx=%idx%"

	choice /c:%keys% "/m:请选择: "
	if %errorlevel% gtr %idx% (
		echo "选择错误！"
		exit
	) else (
		set /a i=%errorlevel%-1
		rem set "web_app_select=%WEB_APPS[!i!]%"
		call set "web_app_select=%%WEB_APPS[!i!]%%"
	)
goto:EOF


:display_download_type_select
        echo "请选择需要下载的软件包（首次部署选2）"
        echo "1 : 一键部署最小化安装包(仅包含微服务一键部署脚本及配置)"
        echo "2 : 一键部署标准安装包(包含微服务一键部署脚本及配置，以及依赖的数据库及中间件安装包)"
        echo "0 : 无需下载"
		choice /c:120 "/m:请选择:  "

		if %errorlevel% == 1 (
			set "download_type=1"
			set "download_type_info=一键部署最小化安装包"
		)

		if %errorlevel% == 2 (
			set "download_type=2"
			set "download_type_info=一键部署标准安装包"
		)

		if %errorlevel% == 0 (
			set "download_type=0"
			set "download_type_info=无需下载"
		)

goto:EOF

:display_domain_select
		echo "请选择下载服务器"
        echo "1 : 阿里云(限速4Mbps)"
        echo "2 : 武汉服务器"
		choice /c:12 "/m:请选择:  "

		if %errorlevel% == 1 (
			set "domain=%default_domain%"
		) else (
			set "domain=%fast_domain%"
		)
goto:EOF

:Init_Array_Var <StringVar> <ArrayName>
	set index=0
	for %%d in (%~1) do (
		set %~2[!index!]=%%d
		set /a index+=1
	)
goto:eof

:auth
	echo "一键部署下载需要根据【项目管理平台】账号和密码来验证身份，验证不通过时，下载将提示【401 Unauthorized】"
	set /p user=请输入账号:
    set "psCommand=powershell -Command "$pword = read-host '请输入密码' -AsSecureString ; ^$BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword); ^[System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)""
    for /f "usebackq delims=" %%p in (`%psCommand%`) do set password=%%p
    echo user=%user%
    rem echo password=%password%
goto:EOF

:download
	setlocal enabledelayedexpansion
	call:Init_Array_Var "%WEB_APPS%" WEB_APPS
	call:Init_Array_Var "%WEB_VERS%" WEB_VERS
	call:display_os_select
	call:display_download_type_select
	call:display_web_app_select
	rem call:display_web_version_select
	call:display_domain_select

	echo "选择的操作系统版本为:  %os_select_info%"
	echo "选择要下载类型为: %download_type_info%"
	echo "选择要下载的web应用为: %web_app_select%"
	rem echo "选择要下载的web应用版本为: %web_version_select%"
	echo "选择的下载服务器为:     %domain%/one 可先测试是否可访问"
	choice /c:y "/m:输入y继续:   "
	call:auth
	call:download_fileslist "!web_app_select!" "!web_version_select!" "!os_select!"
	call:download_by_fileslist

	endlocal
goto:EOF
