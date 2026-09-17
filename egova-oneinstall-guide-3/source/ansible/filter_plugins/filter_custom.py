# -*- coding:utf-8 -*-
import os
import subprocess
import json

CRYPTO_JAR = os.environ.get('CRYPTO_JAR_PATH', '/egova/onekey_install/oneinstall_v2/src/bin/tools/cryptographic-tools-1.0.0-SNAPSHOT-all.jar')
DEFAULT_KEY = os.environ.get('ENCRYPTION_KEY', 'd0196a195f5653e54971a82de1fa87d7')

# 加密结果缓存路径
CACHE_FILE_PATH = os.environ.get('ENCRYPTION_CACHE_PATH', os.path.join(os.getcwd(), '.cache'))

# 加密结果缓存，避免重复加密相同内容
_encrypt_cache = {}


def save_encrypt_cache():
    """将加密缓存保存到文件"""
    try:
        # 确保缓存目录存在
        cache_dir = os.path.dirname(CACHE_FILE_PATH)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 将元组键转换为字符串
        cache_data = {json.dumps(list(key)): value for key, value in _encrypt_cache.items()}
        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_encrypt_cache():
    """从文件加载加密缓存"""
    global _encrypt_cache
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # 将字符串键转换为元组
                _encrypt_cache = {tuple(json.loads(key)): value for key, value in cache_data.items()}
        except Exception:
            _encrypt_cache = {}


# 初始化时加载缓存
load_encrypt_cache()


def encrypt_value(value, encryption_key=DEFAULT_KEY):
    """加密函数，使用SM4算法加密值"""
    if not value:
        return ""

    if not encryption_key or encryption_key == "none" or encryption_key == "":
        return value

    if not os.path.exists(CRYPTO_JAR):
        return value

    # 使用值和密钥作为缓存键
    cache_key = (value, encryption_key)
    if cache_key in _encrypt_cache:
        return _encrypt_cache[cache_key]

    try:
        process = subprocess.Popen(
            ['java', '-jar', CRYPTO_JAR, '-t', 'SM4', '-o', 'encrypt', '-p', value, '-key', encryption_key, '-alg', 'SM4/CBC/PKCS5Padding', '-f', 'BASE64'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        result = value
        if process.returncode == 0:
            output = stdout.decode('utf-8')
            
            # 直接按行分割，不做过滤，保留原始行结构
            lines = output.split('\n')
            
            # 遍历所有行，找到"加密结果："行
            for i, line in enumerate(lines):
                if '加密结果：' in line:
                    # 找到"加密结果："行后的非空行
                    for j in range(i + 1, len(lines)):
                        result_line = lines[j].strip()
                        if result_line:
                            # 检查是否为有效的Base64字符串
                            if all(c.isalnum() or c in '+/=' for c in result_line):
                                result = result_line
                                break
                    if result != value:
                        break
            
            # 如果没有找到预期的格式，尝试找到最后一行非空行
            if result == value:
                for line in reversed(lines):
                    line = line.strip()
                    if line and all(c.isalnum() or c in '+/=' for c in line):
                        result = line
                        break
            
            # 如果都没找到，返回原始输出
            if result == value:
                result = output.strip()
        
        # 缓存加密结果
        _encrypt_cache[cache_key] = result
        # 保存缓存到文件
        save_encrypt_cache()
        return result
    except Exception:
        return value





def encrypt(value, encryption_key=DEFAULT_KEY):
    return encrypt_value(value, encryption_key)


def enc(value):
    """将值包装为ENC()格式"""
    if not value:
        return ""
    if value.startswith("ENC("):
        return value
    return "ENC(" + value + ")"


def get_username(config, encryption_key=DEFAULT_KEY):
    """获取用户名，只处理明文配置"""
    if not config:
        return ""
    # 只处理明文用户名，不处理加密用户名
    return config.get('username', '')


def get_password(config, encryption_key=DEFAULT_KEY):
    """获取密码，只处理明文配置"""
    if not config:
        return ""
    # 只处理明文密码，不处理加密密码
    return config.get('password', '')





def get_access_key(config):
    if not config:
        return ""
    return config.get('access_key', '')


def get_secret_key(config):
    if not config:
        return ""
    return config.get('secret_key', '')


def get_server_node(ms_dict):
    nodes = []
    backends = []
    url_backend = ""
    url_frontend = ""

    for ms_name, v in ms_dict.items():
        if ms_dict[ms_name]["status"] == "success":
            nodes.append(ms_dict[ms_name]["host"])
            backends.append({'host': ms_dict[ms_name]["host"], 'port': str(ms_dict[ms_name]["server_port"])})
            if ms_dict[ms_name].get("url"):
                url_frontend = url_frontend or ms_dict[ms_name]["url"]["frontend"]
                url_backend = url_backend or ms_dict[ms_name]["url"]["backend"]

    return {'nodes': nodes, 'backends': backends, 'url_backend': url_backend, 'url_frontend': url_frontend}


def filter_list_by_attribute(data):
    return [item for item in data if item.get('type') == 'mysql']


def custom_json_query(params_dic):
    dependencies = params_dic.get('data', [])
    type_value = params_dic.get('type_value')
    sub_type_value = params_dic.get('sub_type_value')
    filtered_dependencies = filter(lambda dep: dep.get('type') == type_value and (sub_type_value is None or dep.get('sub_type') == sub_type_value), dependencies)
    result = next(iter(filtered_dependencies), {}).get('depend_key', None)

    return result


class FilterModule(object):
    def filters(self):
        return {
            'get_server_node': get_server_node,
            'filter_list_by_attribute': filter_list_by_attribute,
            'custom_json_query': custom_json_query,
            'encrypt': encrypt,
            'enc': enc,
            'get_username': get_username,
            'get_password': get_password,
            'get_access_key': get_access_key,
            'get_secret_key': get_secret_key,
        }
