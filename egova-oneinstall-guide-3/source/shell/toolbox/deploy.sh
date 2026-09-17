#!/bin/bash

[ -f security/tools/src/fscan ] || wget http://oneops.egova.com.cn:8093/one/tools/security/tools/fscan -O \
        security/tools/src/fscan
[ -f security/tools/src/fscan_arm64 ] || wget http://oneops.egova.com.cn:8093/one/tools/security/tools/fscan_arm64 -O \
    security/tools/src/fscan_arm64
[ -f security/tools/src/yq_x86 ] || wget http://oneops.egova.com.cn:8093/one/tools/security/tools/yq_x86 -O \
        security/tools/src/yq_x86
[ -f security/tools/src/yq_arm64 ] || wget http://oneops.egova.com.cn:8093/one/tools/security/tools/yq_arm64 -O \
    security/tools/src/yq_arm64
[ -f security/tools/src/egova-security-agent.jar ] || \
    wget http://oneops.egova.com.cn:8093/one/tools/security_agent/egova-security-agent.jar -O \
    security/tools/src/egova-security-agent.jar
[ -f security/tools/src/egova-check-save-tools.jar ] || \
    wget http://oneops.egova.com.cn:8093/one/tools/security/egova-check-save-tools.jar -O \
    security/tools/src/egova-check-save-tools.jar
[ -f security/tools/src/weakPwd_Check.tar.gz ] || \
    wget http://oneops.egova.com.cn:8093/one/tools/security/weakPwd_Check.tar.gz -O \
    security/tools/src/weakPwd_Check.tar.gz
[ -f security/tools/src/update_jars.tar.gz ] || \
    wget http://oneops.egova.com.cn:8093/one/tools/security/tools/update_jars.tar.gz -O \
    security/tools/src/update_jars.tar.gz
tar -czpf egova-security-toolbox.tar.gz security/

scp egova-security-toolbox.tar.gz root@10.255.1.25:/egova/one/v1/tools/security/