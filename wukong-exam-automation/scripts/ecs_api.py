#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阿里云 ECS RPC 签名调用助手。

用途：绕开旧版 aliyun CLI 3.3.4 在 Windows 上对 --CommandContent 的编码 bug
（传入任何内容都被确定性乱码，Git Bash/PowerShell 均复现），由本脚本直接对
ECS RPC API 签名并发请求，CommandContent 的 base64 编码完全可控。
典型场景：云助手（CreateCommand/InvokeCommand/DescribeInvocations）给新实例
补 SSH 公钥、执行初始化命令。

安全约束：仅允许 https；host 必须在 ALLOWED_HOSTS 白名单内（拒绝 localhost、
环回、私有和保留地址）；不在输出中打印 AccessKeySecret。

用法：
  python ecs_api.py raw '<Action>' '<json-params>' [host]
  python ecs_api.py run <script-file> <instance-id> [command-name]
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_HOSTS = {
    "ecs.cn-wulanchabu.aliyuncs.com",
    "ecs.aliyuncs.com",
    "ecs.cn-beijing.aliyuncs.com",
}
DEFAULT_HOST = "ecs.cn-wulanchabu.aliyuncs.com"
ECS_VERSION = "2014-05-26"


def get_credentials():
    path = os.path.expanduser("~/.aliyun/config.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for prof in data.get("profiles", []):
        if prof.get("name") == "default":
            return prof.get("access_key_id"), prof.get("access_key_secret")
    raise RuntimeError("default profile not found in ~/.aliyun/config.json")


def percent_encode(value):
    return urllib.parse.quote(value, safe="-_.~")


def sign_and_call(params, host=DEFAULT_HOST):
    if host not in ALLOWED_HOSTS:
        raise RuntimeError("host not allowed: %s" % host)
    ak, sk = get_credentials()
    common = {
        "Format": "JSON",
        "Version": ECS_VERSION,
        "AccessKeyId": ak,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    merged = dict(common)
    merged.update(params)
    pairs = sorted(
        (percent_encode(str(k)), percent_encode(str(v))) for k, v in merged.items()
    )
    query = "&".join("%s=%s" % (k, v) for k, v in pairs)
    string_to_sign = "GET&%s&%s" % (percent_encode("/"), percent_encode(query))
    secret = (sk + "&").encode("utf-8")
    signature = base64.b64encode(
        hmac.new(secret, string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")
    url = "https://%s/?%s&Signature=%s" % (host, query, percent_encode(signature))
    # 不走系统代理：本地代理会掐断到阿里云的连接
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def decode_output(value):
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


def main():
    """用法:
      python ecs_api.py raw '<Action>' '<json-params>' [host]
      python ecs_api.py run <script-file> <instance-id> [command-name]
    """
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    mode = sys.argv[1]
    if mode == "raw":
        action = sys.argv[2]
        params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        host = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_HOST
        params.setdefault("Action", action)
        params.setdefault("RegionId", "cn-wulanchabu")
        print(json.dumps(sign_and_call(params, host), ensure_ascii=False, indent=1))
        return 0
    if mode == "run":
        script_path, instance_id = sys.argv[2], sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else "ops-script"
        with open(script_path, encoding="utf-8") as f:
            script = f.read()
        content_b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
        created = sign_and_call({
            "Action": "CreateCommand",
            "RegionId": "cn-wulanchabu",
            "Type": "RunShellScript",
            "Name": name,
            "CommandContent": content_b64,
        })
        command_id = created.get("CommandId")
        if not command_id:
            print(json.dumps(created, ensure_ascii=False))
            return 1
        invoked = sign_and_call({
            "Action": "InvokeCommand",
            "RegionId": "cn-wulanchabu",
            "CommandId": command_id,
            "InstanceId.1": instance_id,
        })
        invoke_id = invoked.get("InvokeId")
        if not invoke_id:
            print(json.dumps(invoked, ensure_ascii=False))
            return 1
        time.sleep(6)
        result = sign_and_call({
            "Action": "DescribeInvocations",
            "RegionId": "cn-wulanchabu",
            "InvokeId": invoke_id,
        })
        for inv in result.get("Invocations", {}).get("Invocation", []):
            print("invocation_status:", inv.get("InvocationStatus"))
            insts = inv.get("InvokeInstances", {})
            items = insts.get("InvokeInstance", []) if isinstance(insts, dict) else insts
            for item in items:
                print("--- instance %s exit=%s err=%s" % (
                    item.get("InstanceId"), item.get("ExitCode"), item.get("ErrorInfo", "")
                ))
                print(decode_output(item.get("Output", "")))
        return 0
    print("unknown mode:", mode)
    return 1


if __name__ == "__main__":
    sys.exit(main())
