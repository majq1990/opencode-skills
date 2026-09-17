# 悟空补考考后自动化（23:30 触发）
# 1. 重置考生密码为 eGova@123
# 2. 查询无页面无项目账号（无需评分名单）
# 3. 输出结果文件 + 钉钉通知
$ErrorActionPreference = "Continue"

$SSH_KEY = "D:\backup\user\majq\.ssh\mjqegova"
$REMOTE_HOST = "8.130.165.232"
$DB_PASS = "eGovaZT@2023"
$DATE = Get-Date -Format "yyyy-MM-dd"
$OUT_DIR = "D:\opencode\file\$DATE"
$OUT_FILE = "$OUT_DIR\wukong_postexam_$(Get-Date -Format HHmmss).txt"
New-Item -ItemType Directory -Force -Path $OUT_DIR | Out-Null

function Invoke-RemoteSql {
    param([string]$SqlFile, [string]$Db)
    & ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 -i $SSH_KEY root@$REMOTE_HOST "mysql -uroot -p$DB_PASS -A $Db < /tmp/$SqlFile" 2>&1
}

function Copy-ToRemote {
    param([string]$LocalFile, [string]$RemotePath)
    $target = "root@${REMOTE_HOST}:$RemotePath"
    & scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 -i $SSH_KEY $LocalFile $target 2>&1 | Out-Null
}

# --- Step 1: 重置非 admin 密码为 eGova@123（含密码永不过期保护） ---
$resetSql = @"
update wukong.com_user
set password='a2defcd18070f91bc59c113ab499920309dbcbd7156faf3ef8b4086b986daced',
    encryptionType='Sm3WithSalt',
    encryptSalt='GQQiaYnk',
    passwordExpireTime=NULL
where username!='admin' and password!='a2defcd18070f91bc59c113ab499920309dbcbd7156faf3ef8b4086b986daced';
"@
$resetSql | Set-Content -Path "$env:TEMP\reset_pwd.sql" -Encoding UTF8
Copy-ToRemote -LocalFile "$env:TEMP\reset_pwd.sql" -RemotePath "/tmp/reset_pwd.sql"
$r1 = Invoke-RemoteSql -SqlFile "reset_pwd.sql" -Db "wukong"

# --- Step 2: 查询无页面无项目账号 ---
$checkSql = @"
select
    page.name,
    page.username
from
    (
        select a.name, a.username
        from wukong.com_user a
        where not exists (
            select 1 from wukong.wukong_page where creator = a.username
        )
    ) page,
    (
        select a.name, a.username
        from wukong.com_user a
        where not exists (
            select 1 from wukong.wukong_project where creator = a.username
        )
    ) project
where page.name = project.name;
"@
$checkSql | Set-Content -Path "$env:TEMP\check_noans.sql" -Encoding UTF8
Copy-ToRemote -LocalFile "$env:TEMP\check_noans.sql" -RemotePath "/tmp/check_noans.sql"
$r2 = Invoke-RemoteSql -SqlFile "check_noans.sql" -Db "wukong"

# --- Step 3: 输出结果 ---
$lines = @()
$lines += "===== 悟空补考考后结果 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ====="
$lines += ""
$lines += "--- Step1 密码重置输出 ---"
$lines += ($r1 -join "`n")
$lines += ""
$lines += "--- Step2 无页面无项目账号（无需评分） ---"
$lines += ($r2 -join "`n")
$lines | Set-Content -Path $OUT_FILE -Encoding UTF8
Write-Host "结果已保存: $OUT_FILE"
Get-Content $OUT_FILE

