#!/bin/bash --login

shopt -s expand_aliases

# egova用户默认密码
EGOVA_PASSWORD=Z@Tpwd@2024

##获取系统版本信息
function get_distribution_info() {
    ##缓存版本信息
    if [ -n "$cached_distribution_info" ]; then
          echo "$cached_distribution_info"
          return 0
    fi
    if [ -f /etc/os-release ]; then
        source /etc/os-release

        if [ -n "$ID" ]; then
            # 检查centos版本
            if [ -n "$VERSION_ID" ]; then
                version=$(echo $VERSION_ID | cut -d'.' -f1)
            else
                # 检查Ubuntu版本
                if [ -n "$UBUNTU_CODENAME" ]; then
                    version=$(lsb_release -rs | cut -d. -f1)
                fi
            fi
            if [ "$(uname -m)" == "x86_64" ]; then
              arch=$(echo "x86")
            else
              arch=$(echo "arm")
            fi
            cached_distribution_info="$ID"_"$version"_"$arch"
            echo "$cached_distribution_info"
            return 0
        fi
    fi
    return 1
}
##检查版本
function check_distribution() {
    local distribution=$1

    if [[ "$(get_distribution_info)" =~ ($distribution) ]]; then
        return 0
    fi
    return 1
}
function is_kylin() {
   check_distribution "kylin"
}
function is_openEuler() {
     check_distribution "openEuler"
}
function is_ubuntu() {
   check_distribution "ubuntu"
}
function is_centos() {
   check_distribution "centos"
}
function is_uos() {
   check_distribution "uos"
}
# 备份相关文件
function backup_important_file() {
    if [ ! -e $1.bak ]; then
        cp $1 $1.bak
    fi
}

# 修复口令相关问题
function fix_login_defs() {
    #    read -p "是否口令设置相关配置？(y/n)" flag
    #    if [ $flag == "y" ]; then
    # 修改口令更改最小间隔天数
    sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   7/g' /etc/login.defs
    # 修改口令过期前警告天数
    sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   30/g' /etc/login.defs
    # 修改口令更改最小长度
    sed -i 's/^PASS_MIN_LEN.*/PASS_MIN_LEN   8/g' /etc/login.defs
    # 修改口令生存周期
    sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/g' /etc/login.defs
    echo "修改密码周期相关配置，需每隔7到90天修改一次密码"
    if [ $(grep "^UMASK" /etc/login.defs | wc -l) -eq 0 ]; then
        echo "UMASK           027" >>/etc/login.defs
    else
        sed -i 's/^UMASK.*/UMASK           027/g' /etc/login.defs
    fi
    if is_ubuntu ; then
          str="password    requisite     pam_cracklib.so  retry=3 minlen=10 difok=3  dcredit=-1 ucredit=-1 ocredit=-1 lcredit=-1 enforce_for_root"
          sed -i "s/^password.*pam_cracklib\.so.*$/$str/g" /etc/pam.d/common-password
    else
         str="password    requisite     pam_pwquality.so try_first_pass local_users_only retry=3 authtok_type= dcredit=-1 ucredit=-1 ocredit=-1 lcredit=-1 minlen=10 minclass=3 difok=3 enforce_for_root"
         sed -i "s/.* pam_pwquality.so.*/$str/g" /etc/pam.d/system-auth
    fi
}

# 命令行操作超时时限10分钟
function fix_ssh_timeout() {
    #    read -p "是否设置命令行操作超时时限为10分钟？(y/n)" flag
    #    if [ $flag == "y" ]; then
    # 设定命令行界面超时时间
    if [ $(grep "^export TMOUT" /etc/profile | wc -l) -eq 0 ]; then
        echo "export TMOUT=600" >>/etc/profile
    fi
    echo "设定命令行界面超时时间,无操作下10分钟会关闭ssh窗口！"
    #    fi
}

# 修改umask的权限
function fix_umask_auth() {
    #    read -p "是否检查并设置umask的权限？(y/n)" flag
    #    if [ $flag == "y" ]; then
    files=(/etc/profile /etc/bashrc /etc/csh.login /etc/csh.cshrc)
    for file in ${files[*]}; do
        backup_important_file $file
        if [ $(grep "^umask" $file | wc -l) -eq 0 ]; then
            echo "umask 027" >>$file
        else
            sed -i 's/^umask.*/umask 027/g' $file
        fi
    done
    #    fi
}

# 配置保留历史文件
function fix_keep_history_config() {
    #    read -p "是否检查并配置保留历史文件？(y/n)" flag
    #    if [ $flag == "y" ]; then
    backup_important_file /etc/profile
    if [ $(grep "^HISTFILESIZE.*" /etc/profile | wc -l) -eq 0 ]; then
        echo "HISTFILESIZE=5" >>/etc/profile
    else
        sed -i 's/^HISTFILESIZE.*/HISTFILESIZE=5/g' /etc/profile
    fi
    if [ $(grep "^HISTSIZE=.*" /etc/profile | wc -l) -eq 0 ]; then
        echo "HISTSIZE=5" >>/etc/profile
    else
        sed -i 's/^HISTSIZE=.*/HISTSIZE=5/g' /etc/profile
    fi
    #    fi
}

# 配置重要文件属性
function fix_important_file() {
    #    read -p "是否检查并配置重要文件属性,并加锁？(y/n)" flag
    #    if [ $flag == "y" ]; then
    chattr +i /etc/gshadow
    chattr +i /etc/group
    #    fi
}

# 解锁重要文件
function unlock_important_files() {
    chattr -i /etc/gshadow
    chattr -i /etc/group
    chattr -i /etc/shadow
    chattr -i /etc/passwd
}

# 修改系统引导器配置
function fix_system_boot_config() {
    #    read -p "是否修改系统引导器配置文件权限？(y/n)" flag
    #    if [ $flag == "y" ]; then
    if [ -e /etc/grub.conf ] && [ ! -h /etc/grub.conf ]; then
        chmod 600 /etc/grub.conf
    fi

    if [ -e /boot/grub/grub.conf ]; then
        chmod 600 /boot/grub/grub.conf
    fi

    if [ -e /etc/lilo.conf ] && [ ! -h /etc/lilo.conf ]; then
        chmod 600 /etc/lilo.conf
    fi

    if [ -e /etc/grub2.cfg ]; then
        chmod 600 /etc/grub2.cfg
    fi

    if [ -e /boot/grub2/grub.cfg ] && [ ! -h /boot/grub2/grub.cfg ]; then
        chmod 600 /boot/grub2/grub.cfg
    fi
    chmod 751 /etc/rc.d/init.d/
    chmod 750 /etc/rc.d/rc3.d
    chmod 750 /etc/rc.d/rc5.d/
    chmod 750 /etc/rc.d/rc4.d
    chmod 750 /etc/rc.d/rc2.d/
    chmod 750 /etc/rc.d/rc1.d/
    chmod 750 /etc/rc.d/rc0.d/
    #        会引起postgresql数据的问题，暂时不修改
    #        chmod 750 /tmp
    chmod 750 /etc/rc.d/rc6.d
    chmod 600 /etc/security
    unlock_important_files
    chown $SSH_USER:root /etc/passwd /etc/shadow /etc/group /etc/gshadow
    chmod 0644 /etc/group
    chmod 0644 /etc/passwd
    chmod 0400 /etc/shadow
    chmod 0400 /etc/gshadow
    chmod 644 /etc/services
    if test -e /tmp/sangfor_mod_tmp; then
        chmod 600 /tmp/sangfor_mod_tmp
    fi
    #    可能新建用户后才会有此文件
    chmod 600 /etc/xinetd.conf 2>/dev/null
    #    fi
}

# 修改系统引导器配置
function fix_ubuntu_system_boot_config() {
  if [ -e /etc/default/grub ]; then
      chmod 600 /etc/default/grub
  fi

  if [ -e /boot/grub/grub.cfg ]; then
      chmod 600 /boot/grub/grub.cfg
  fi

  if [ -e /etc/lilo.conf ] && [ ! -h /etc/lilo.conf ]; then
      chmod 600 /etc/lilo.conf
  fi

  if [ -e /boot/grub/grub.cfg ]; then
      chmod 600 /boot/grub/grub.cfg
  fi

  chmod 751 /etc/init.d/
  chmod 750 /etc/rc3.d
  chmod 750 /etc/rc5.d/
  chmod 750 /etc/rc4.d
  chmod 750 /etc/rc2.d/
  chmod 750 /etc/rc1.d/
  chmod 750 /etc/rc0.d/
  chmod 750 /etc/rc6.d
  chmod 600 /etc/security
  unlock_important_files
  chown root:shadow /etc/passwd /etc/shadow /etc/group /etc/gshadow
  chmod 0644 /etc/group
  chmod 0644 /etc/passwd
  chmod 0400 /etc/shadow
  chmod 0400 /etc/gshadow
  chmod 644 /etc/services
  if [ -e /tmp/sangfor_mod_tmp ]; then
      chmod 600 /tmp/sangfor_mod_tmp
  fi
  # 可能新建用户后才会有此文件
  chmod 600 /etc/xinetd.conf 2>/dev/null
}

# core dump 配置
function fix_core_dump() {
    #    read -p "是否修改系统引导器配置文件权限？(y/n)" flag
    #    if [ $flag == "y" ]; then
    backup_important_file /etc/security/limits.conf
    if [ $(grep "^* soft core 0" /etc/security/limits.conf | wc -l) -eq 0 ]; then
        echo "* soft core 0" >>/etc/security/limits.conf
    fi

    if [ $(grep "^* hard core 0" /etc/security/limits.conf | wc -l) -eq 0 ]; then
        echo "* hard core 0" >>/etc/security/limits.conf
    fi

    backup_important_file /etc/systemd/system.conf
    sed -i "s/.DefaultLimitNOFILE=.*/DefaultLimitNOFILE=1048576/g" /etc/systemd/system.conf
    systemctl daemon-reexec
    #    fi
}

# 检查并修改系统openssh安全设置及禁止root用户telnet登录
# 将禁止root远程ssh登录修改为禁止密码登录，可以密钥登录
function fix_openssh_setting() {
    #    read -p "是否检查并修改系统openssh安全设置及禁止root用户telnet登录？(y/n)" flag
    #    if [ $flag == "y" ]; then
    if [ -e /etc/ssh/sshd_config ]; then
        backup_important_file /etc/ssh/sshd_config
        if [ $(grep "^Protocol 2" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
            echo "Protocol 2" >>/etc/ssh/sshd_config
        fi

        if [ $(grep "^PermitRootLogin.*" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
            echo "PermitRootLogin without-password" >>/etc/ssh/sshd_config
        else
            sed -i 's/^PermitRootLogin.*/PermitRootLogin without-password/g' /etc/ssh/sshd_config
        fi

        if [ $(grep "^telnet          23/tcp" /etc/services | wc -l) -ge 1 ]; then
            sed -i 's#^telnet          23/tcp#\#telnet          23/tcp#g' /etc/services
        fi
    elif [ -e /etc/ssh2/sshd2_config ]; then
        backup_important_file /etc/ssh2/sshd2_config
        if [ $(grep "^Protocol 2" /etc/ssh2/sshd2_config | wc -l) -eq 0 ]; then
            echo "Protocol 2" >>/etc/ssh2/sshd2_config
        fi

        if [ $(grep "^PermitRootLogin.*" /etc/ssh2/sshd2_config | wc -l) -eq 0 ]; then
            echo "PermitRootLogin without-password" >>/etc/ssh2/sshd2_config
        else
            sed -i 's/^PermitRootLogin.*/PermitRootLogin without-password/g' /etc/ssh2/sshd2_config
        fi
    fi
    if [ $(grep "^auth\s*required\s*pam_securetty.so$" /etc/pam.d/login | wc -l) -eq 0 ]; then
        backup_important_file /etc/pam.d/login
        sed -i '2i\auth required pam_securetty.so' /etc/pam.d/login
    fi
    service sshd restart

}

# 设置ssh空闲超时退出时间
function set_ssh_timeout() {
    #    read -p "是否设置ssh空闲超时退出时间(阿里云)？(y/n)" flag
    #    if [ $flag == "y" ]; then
    if [ -e /etc/ssh/sshd_config ]; then
        backup_important_file /etc/ssh/sshd_config
        if [ $(grep "^ClientAliveInterval.*" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
            echo "ClientAliveInterval 600" >>/etc/ssh/sshd_config
        else
            sed -i 's/^ClientAliveInterval.*/ClientAliveInterval 600/g' /etc/ssh/sshd_config
        fi
        if [ $(grep "^ClientAliveCountMax.*" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
            echo "ClientAliveCountMax 2" >>/etc/ssh/sshd_config
        else
            sed -i 's/^ClientAliveCountMax.*/ClientAliveCountMax 2/g' /etc/ssh/sshd_config
        fi
    fi
    #    fi
}

# 系统登录攻击防范 Login_Attack_RETRIES
function fix_login_attack_retries() {
    #    read -p "是否设置系统登录攻击防范 Login_Attack_RETRIES(华为云)？(y/n)" flag
    #    if [ $flag == "y" ]; then
    if [ -e /etc/ssh/sshd_config ]; then
        backup_important_file /etc/ssh/sshd_config
        if [ $(grep "^MaxAuthTries.*" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
            echo "MaxAuthTries 3" >>/etc/ssh/sshd_config
        else
            sed -i 's/^MaxAuthTries.*/MaxAuthTries 3/g' /etc/ssh/sshd_config
        fi
    fi
    #    fi
}

# 设置登陆前警告banner
function fix_set_before_login_banner() {
    #    read -p "是否检查并设置登陆前警告banner？(y/n)" flag
    #    if [ $flag == "y" ]; then
    touch /etc/ssh_banner
    chown bin:bin /etc/ssh_banner
    chmod 644 /etc/ssh_banner
    echo " Authorized only. All activity will be monitored and reported " >/etc/ssh_banner
    if [ $(grep "^Banner /etc/ssh_banner" /etc/ssh/sshd_config | wc -l) -eq 0 ]; then
        echo "Banner /etc/ssh_banner" >>/etc/ssh/sshd_config
    fi
    #        service sshd restart
    #    fi
}

# PAM认证禁止wheel组外用户su为root
function fix_pam_su_root() {
    #    read -p "是否检查并配置PAM认证禁止wheel组外用户su为root？(y/n)" flag
    #    if [ $flag == "y" ]; then
    backup_important_file /etc/pam.d/su
    if [ $(grep "pam_rootok.so" /etc/pam.d/su | wc -l) -eq 0 ]; then
        sed -i '2i\auth            sufficient      pam_rootok.so' /etc/pam.d/su
    fi
    if [ $(grep "pam_wheel.so\s*group=wheel" /etc/pam.d/su | wc -l) -eq 0 ]; then
        sed -i '3i\auth            required        pam_wheel.so group=wheel' /etc/pam.d/su
    fi
    #    fi
}

# 检查并设置设备密码相关配置
function fix_equ_secret_complex() {
    #    read -p "是否检查并设置设备密码相关配置？(y/n)" flag
    #    if [ $flag == "y" ]; then
    backup_important_file /etc/pam.d/system-auth
    if [ $(grep "password\s*requisite\s*pam_pwquality.so.*" /etc/pam.d/system-auth | grep "dcredit=" | wc -l) -eq 0 ]; then
        sed -i 's/password\s*requisite\s*pam_pwquality.so.*/& dcredit=0 ucredit=0 ocredit=0 lcredit=0 minlen=10 minclass=3/g' /etc/pam.d/system-auth
    fi
    if [ -e /etc/security/pwquality.conf ]; then
        backup_important_file /etc/security/pwquality.conf
        if [ $(grep "^minlen=" /etc/security/pwquality.conf | wc -l) -eq 0 ]; then
            echo "minlen=10" >>/etc/security/pwquality.conf
        fi
        if [ $(grep "^minclass=" /etc/security/pwquality.conf | wc -l) -eq 0 ]; then
            echo "minclass=3" >>/etc/security/pwquality.conf
        fi
    fi
    if [ $(grep "^password\s*requisite\s*pam_cracklib.so" /etc/pam.d/system-auth | wc -l) -eq 0 ]; then
        echo "password    requisite     pam_cracklib.so ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1" >>/etc/pam.d/system-auth
    fi

    if [ $(grep "^password\s*sufficient" /etc/pam.d/system-auth | grep "remember=.*" | wc -l) -eq 0 ]; then
        sed -i 's/^password\s*sufficient.*/& remember=5/g' /etc/pam.d/system-auth
    fi

    backup_important_file /etc/pam.d/password-auth
    if [ $(grep "^password\s*sufficient" /etc/pam.d/password-auth | grep "remember=.*" | wc -l) -eq 0 ]; then
        sed -i 's/^password\s*sufficient.*/& remember=5/g' /etc/pam.d/password-auth
    fi
    echo "密码复杂度设置完成，最小长度为10。"
    #    fi
}
# 检查并设置设备密码相关配置
function fix_ubuntu_equ_secret_complex() {
    backup_important_file /etc/pam.d/common-password
    if [ $(grep "password\s*requisite\s*pam_cracklib.so.*" /etc/pam.d/common-password | grep "dcredit=" | wc -l) -eq 0 ]; then
        sed -i 's/password\s*requisite\s*pam_cracklib.so.*/& dcredit=0 ucredit=0 ocredit=0 lcredit=0 minlen=10 minclass=3/g' /etc/pam.d/common-password
    fi
    if [ -e /etc/security/pwquality.conf ]; then
        backup_important_file /etc/security/pwquality.conf
        if [ $(grep "^minlen=" /etc/security/pwquality.conf | wc -l) -eq 0 ]; then
            echo "minlen=10" >>/etc/security/pwquality.conf
        fi
        if [ $(grep "^minclass=" /etc/security/pwquality.conf | wc -l) -eq 0 ]; then
            echo "minclass=3" >>/etc/security/pwquality.conf
        fi
    fi
    if [ $(grep "^password\s*requisite\s*pam_pwquality.so" /etc/pam.d/common-password | wc -l) -eq 0 ]; then
        echo "password    requisite     pam_cracklib.so ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1" >>/etc/pam.d/common-password
    fi

    if [ $(grep "^password\s.*pam_unix.so" /etc/pam.d/common-password | grep "remember=.*" | wc -l) -eq 0 ]; then
        sed -i 's/^password\s.*pam_unix.so.*/& remember=5/g' /etc/pam.d/common-password
    fi

    echo "密码复杂度设置完成，最小长度为10。"
    #    fi
}

# 账户认证失败次数限制
function fix_account_fail_num() {
    #    read -p "是否检查并配置账户认证失败次数限制？(y/n)" flag
    #    if [ $flag == "y" ]; then
    backup_important_file /etc/pam.d/sshd
    if [ ! -e /lib64/security/pam_tally.so ]; then
        ln -s /lib64/security/pam_tally2.so /lib64/security/pam_tally.so 2>/dev/null
    fi
    if [ $(grep "pam_tally2.so" /etc/pam.d/sshd | wc -l) -eq 0 ]; then
        sed -i '/^-auth.*/a\account    required     pam_tally2.so' /etc/pam.d/sshd
        sed -i '2i\auth       required     pam_tally2.so deny=5 unlock_time=600' /etc/pam.d/sshd
    fi
    backup_important_file /etc/pam.d/system-auth
    if [ $(grep "account.*pam_tally.so" /etc/pam.d/system-auth | wc -l) -eq 0 ]; then
        sed -i '2i\account    required     pam_tally.so' /etc/pam.d/system-auth
    fi
    if [ $(grep "auth.*deny.*unlock_time=600" /etc/pam.d/system-auth | wc -l) -eq 0 ]; then
        sed -i '2i\auth       required     pam_tally.so deny=5 unlock_time=600' /etc/pam.d/system-auth
    fi
    #    fi
}

# 配置远程日志功能
function fix_remote_log_config() {
    #    read -p "是否检查并配置rsyslog远程日志功能？(y/n)" flag
    #    if [ $flag == "y" ]; then
    service rsyslog start 2>/dev/null
    if [ -e /etc/rsyslog.conf ]; then
        echo "*.*                    @127.0.0.1" >>/etc/rsyslog.conf
        echo "*.err;kern.debug;daemon.notice                          /var/adm/messages" >>/etc/rsyslog.conf
        if [ ! -e /etc/rsyslog.conf ]; then
            touch /etc/rsyslog.conf
            chmod 666 /var/adm/messages
        fi
        service rsyslog restart 2>/dev/null
    fi
    #    fi
}

# 修复关闭IP伪装和绑定多IP功能
function fix_multi_IP() {
    #    read -p "是否检查并修复关闭IP伪装和绑定多IP功能？(y/n)" flag
    #    if [ $flag == "y" ]; then
    touch /etc/hosts.conf
    if [ $(grep "^nospoof" /etc/hosts.conf | wc -l) -eq 0 ]; then
        echo "nospoof on" >>/etc/hosts.conf
    else
        sed -i 's/^nospoof.*/nospoof on/g' /etc/hosts.conf
    fi

    if [ $(grep "^multi" /etc/host.conf | wc -l) -eq 0 ]; then
        echo "multi off" >>/etc/host.conf
    else
        sed -i 's/^multi.*/multi off/g' /etc/host.conf
    fi
    #    fi
}

# 别名文件配置相关
function fix_aliases() {
    #    read -p "是否检查并修复别名文件配置相关？(y/n)" flag
    #    if [ $flag == "y" ]; then
    if [ -e /etc/aliases ]; then
        file=/etc/aliases
    else
        file=/etc/mail/aliases
    fi
    backup_important_file ${file}
    sed -i 's/^games:.*root$/#&/g' ${file}
    sed -i 's/^ingres:.*root$/#&/g' ${file}
    sed -i 's/^system:.*root$/#&/g' ${file}
    sed -i 's/^toor:.*root$/#&/g' ${file}
    sed -i 's/^uucp.*root$/#&/g' ${file}
    sed -i 's/^manager.*root$/#&/g' ${file}
    sed -i 's/^dumper.*root$/#&/g' ${file}
    sed -i 's/^operator.*root$/#&/g' ${file}
    sed -i 's/^decode.*root$/#&/g' ${file}
    sed -i 's/^root.*marc$/#&/g' ${file}
    if is_centos ;then
       sed -i 's/^inet_interfaces.*/#&/g' /etc/postfix/main.cf
       systemctl restart postfix
       /usr/bin/newaliases
    fi
}

# 系统内核参数配置
function fix_linux_sys_congfig() {
    #    read -p "是否检查并修复系统内核参数配置？(y/n)" flag
    #    if [ $flag == "y" ]; then
    file=/etc/sysctl.conf
    backup_important_file ${file}
    # 开启icmp_echo_ignore_broadcasts功能
    if [ $(grep "echo_ignore_broadcasts" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.icmp_echo_ignore_broadcasts = 1" >>${file}
    fi
    # 关闭数据包转发功能
    if [ $(grep "ip_forward" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.ip_forward = 0" >>${file}
    fi
    # send_redirects配置
    if [ $(grep "send_redirects" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.conf.all.send_redirects = 0" >>${file}
    fi
    # 禁止icmp重定向报文
    if [ $(grep "accept_redirects" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.conf.all.accept_redirects = 0" >>${file}
    fi
    # 禁止icmp源路由
    if [ $(grep "accept_source_route" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.conf.all.accept_source_route = 0" >>${file}
    fi
    # 开启syncookies功能
    if [ $(grep "tcp_syncookies" ${file} | wc -l) -eq 0 ]; then
        echo "net.ipv4.tcp_syncookies = 1" >>${file}
    fi
    sysctl -p >/dev/null
}
# 创建egova用户，并加入wheel组
function create_new_user() {
    username=$1
    password=$2
    res=$(grep -w "$username:" /etc/passwd | wc -l)
    if [ $res -eq 1 ]; then
        echo "用户已存在"
    else
        useradd -m $username
        echo $password | passwd --stdin $username 2>/dev/null
    fi
}

function create_user_egova() {
    unlock_important_files
    create_new_user egova $EGOVA_PASSWORD
    fix_important_file
}

function users_create() {
    unlock_important_files
    create_new_user egova $EGOVA_PASSWORD
    # 强制首次登录改密码
    chage -d 0 egova
    create_new_user egova_admin eGovaAdmin@2022
    usermod -G wheel egova_admin
    echo "新增用户egova，密码为${EGOVA_PASSWORD}，首次登录需改密码，root用户仅能使用密钥方式登录!"
    fix_important_file
}
# 启动ntpd服务
function fix_start_ntpd() {
    if is_ubuntu ;then
      systemctl start ntp
    else
      systemctl start ntpd
    fi
}

function fix_egova_systemctl_config() {
    file=/usr/share/polkit-1/actions/org.freedesktop.systemd1.policy
    config=../template/org.freedesktop.systemd1.policy
    backup_important_file ${file}
    dos2unix ${config}
    cat ${config} >${file}
    systemctl restart polkit
}

#配置cron、at的安全性, 如果存在非root用户，需要人工确认是否正常,这里只判断如果没有/etc/cron.allow /etc/at.allow就创建
function fix_cron_at_allow() {
    if ! test -e "/etc/cron.allow"; then
        touch /etc/cron.allow
        echo "root" >/etc/cron.allow
        echo "egova" >/etc/cron.allow
    fi
    if ! test -e "/etc/at.allow"; then
        touch /etc/at.allow
        echo "root" >/etc/at.allow
        echo "egova" >/etc/at.allow
    fi
}

function fix_log4j_bug() {
    echo "FORMAT_MESSAGES_PATTERN_DISABLE_LOOKUPS=true" >>/etc/profile
    source /etc/profile
}

function patch_for_tool_box() {
    fix_login_defs
    fix_egova_systemctl_config
    users_create
    fix_ssh_timeout
    ! if is_ubuntu; then
        fix_umask_auth
    fi
    #fix_keep_history_config
    fix_core_dump
    fix_start_ntpd
    fix_openssh_setting
    set_ssh_timeout
    fix_login_attack_retries
    fix_set_before_login_banner
    fix_pam_su_root
    if is_ubuntu; then
          fix_ubuntu_equ_secret_complex
    else
      fix_equ_secret_complex
      fix_account_fail_num
    fi
    #fix_remote_log_config
    fix_multi_IP
    if is_ubuntu; then
      fix_ubuntu_system_boot_config
    else
      fix_aliases
      fix_linux_sys_congfig
      fix_system_boot_config
    fi
    fix_important_file
    fix_cron_at_allow
    fix_log4j_bug
    echo "linux系统安全修复完成！"
}

is_sourced() {
    [ "${#FUNCNAME[@]}" -ge 2 ] &&
        [ "${FUNCNAME[0]}" = 'is_sourced' ] &&
        [ "${FUNCNAME[1]}" = 'source' ]
}

if ! is_sourced; then
    patch_for_tool_box
fi
