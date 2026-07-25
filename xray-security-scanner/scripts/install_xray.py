#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xray 多平台客户端自动下载脚本
自动下载 Linux、Windows、Darwin (macOS) 的最新版 xray 客户端
保存到 skill 目录中，方便分发和使用
"""

import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import json
import subprocess
import shutil
from pathlib import Path

# 颜色输出 - 使用简单字符避免编码问题
class Colors:
    GREEN = '[OK]'
    YELLOW = '[WARN]'
    RED = '[ERROR]'
    BLUE = '[INFO]'
    CYAN = '[PLATFORM]'
    END = ''

def print_info(msg):
    print(f"{Colors.BLUE} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW} {msg}")

def print_error(msg):
    print(f"{Colors.RED} {msg}")

def print_platform(msg):
    print(f"{Colors.CYAN} {msg}")

# 定义支持的平台和架构
SUPPORTED_PLATFORMS = {
    'windows': ['amd64', '386'],
    'linux': ['amd64', '386', 'arm64', 'arm'],
    'darwin': ['amd64', 'arm64']  # macOS
}

# xray 最新版本号（手动指定，避免获取到 xpoc 等其他工具）
XRAY_LATEST_VERSION = "1.9.11"

def get_skill_directory():
    """获取 skill 目录路径"""
    # 脚本所在目录的上级目录就是 skill 根目录
    script_dir = Path(__file__).parent.absolute()
    skill_dir = script_dir.parent
    return skill_dir

def get_download_url(system, arch, version=None):
    """获取下载 URL"""
    if version is None:
        version = XRAY_LATEST_VERSION
    
    # GitHub releases 页面 URL 格式
    base_url = f"https://github.com/chaitin/xray/releases/download/{version}"
    
    # 构建文件名
    if system == "windows":
        filename = f"xray_windows_{arch}.exe.zip"
    else:
        filename = f"xray_{system}_{arch}.zip"
    
    return f"{base_url}/{filename}", version

def download_file(url, dest_path, platform_name):
    """下载文件"""
    print_info(f"[{platform_name}] Downloading: {url}")
    
    # 使用镜像加速
    mirror_urls = [
        url,
        url.replace('https://github.com', 'https://ghfast.top/https://github.com'),
    ]
    
    last_error = None
    for mirror_url in mirror_urls:
        try:
            req = urllib.request.Request(mirror_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=120) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = min(100, downloaded * 100 // total_size)
                            sys.stdout.write(f"\r[{platform_name}] Progress: {percent}% ({downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB)")
                            sys.stdout.flush()
            
            print()  # 换行
            print_success(f"[{platform_name}] Download complete: {dest_path}")
            return True
            
        except Exception as e:
            last_error = e
            if mirror_url != mirror_urls[-1]:
                print_warning(f"[{platform_name}] Primary link failed, trying mirror...")
            continue
    
    print_error(f"[{platform_name}] Download failed: {last_error}")
    return False

def extract_archive(archive_path, extract_to, platform_name):
    """解压归档文件"""
    print_info(f"[{platform_name}] Extracting: {archive_path}")
    
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise Exception(f"Unsupported archive format: {archive_path}")
        
        print_success(f"[{platform_name}] Extraction complete")
        return True
    except Exception as e:
        print_error(f"[{platform_name}] Extraction failed: {e}")
        return False

def find_xray_binary(extract_dir, system):
    """查找 xray 二进制文件"""
    exe_suffix = '.exe' if system == 'windows' else ''
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.startswith('xray') and not file.endswith(('.zip', '.tar.gz', '.md', '.txt')):
                if not file.endswith(exe_suffix):
                    continue
                return os.path.join(root, file)
    return None

def download_platform(platform_name, arch, dest_dir, version=None):
    """下载指定平台的 xray"""
    if version is None:
        version = XRAY_LATEST_VERSION
    
    print_platform(f"Downloading {platform_name} {arch}")
    
    try:
        # 获取下载链接
        download_url = get_download_url(platform_name, arch, version)[0]
        print_info(f"[{platform_name}_{arch}] Version: {version}")
        
        # 创建平台目录
        platform_dir = os.path.join(dest_dir, f"{platform_name}_{arch}")
        os.makedirs(platform_dir, exist_ok=True)
        
        # 确定文件名
        if platform_name == 'windows':
            archive_name = f"xray_{version}_{platform_name}_{arch}.zip"
        else:
            archive_name = f"xray_{version}_{platform_name}_{arch}.zip"
        
        archive_path = os.path.join(platform_dir, archive_name)
        
        # 检查是否已存在
        binary_name = f"xray{'.exe' if platform_name == 'windows' else ''}"
        binary_path = os.path.join(platform_dir, binary_name)
        
        if os.path.exists(binary_path):
            print_warning(f"[{platform_name}_{arch}] xray already exists, skipping")
            return True
        
        # 下载
        if not download_file(download_url, archive_path, f"{platform_name}_{arch}"):
            return False
        
        # 解压
        if not extract_archive(archive_path, platform_dir, f"{platform_name}_{arch}"):
            return False
        
        # 查找并移动二进制文件
        extracted_binary = find_xray_binary(platform_dir, platform_name)
        if extracted_binary:
            if extracted_binary != binary_path:
                shutil.move(extracted_binary, binary_path)
                # 清理子目录
                for item in os.listdir(platform_dir):
                    item_path = os.path.join(platform_dir, item)
                    if item_path != binary_path and item != archive_name:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
        else:
            print_error(f"[{platform_name}_{arch}] xray binary not found")
            return False
        
        # 设置可执行权限（非 Windows）
        if platform_name != 'windows':
            os.chmod(binary_path, 0o755)
        
        # 清理压缩包
        if os.path.exists(archive_path):
            os.remove(archive_path)
        
        print_success(f"[{platform_name}_{arch}] Installation complete: {binary_path}")
        return True
        
    except Exception as e:
        print_error(f"[{platform_name}_{arch}] Installation failed: {e}")
        return False

def download_all_platforms(dest_dir=None, platforms=None):
    """下载所有平台的 xray"""
    if dest_dir is None:
        skill_dir = get_skill_directory()
        dest_dir = os.path.join(skill_dir, 'binaries')
    
    os.makedirs(dest_dir, exist_ok=True)
    
    if platforms is None:
        platforms = SUPPORTED_PLATFORMS
    
    print_info("=" * 60)
    print_info("Starting xray multi-platform client download")
    print_info(f"Target directory: {dest_dir}")
    print_info(f"Version: {XRAY_LATEST_VERSION}")
    print_info("=" * 60)
    
    results = {}
    success_count = 0
    fail_count = 0
    
    for platform_name, archs in platforms.items():
        for arch in archs:
            key = f"{platform_name}_{arch}"
            success = download_platform(platform_name, arch, dest_dir)
            results[key] = success
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            print()  # 空行分隔
    
    # 打印汇总
    print_info("=" * 60)
    print_info("Download Summary")
    print_info("=" * 60)
    
    for key, success in results.items():
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} {key}")
    
    print()
    print_success(f"Success: {success_count} platforms")
    if fail_count > 0:
        print_error(f"Failed: {fail_count} platforms")
    
    # 创建版本信息文件
    version_file = os.path.join(dest_dir, 'version.txt')
    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(f"xray version: {XRAY_LATEST_VERSION}\n")
            f.write(f"download date: {os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip()}\n")
            f.write(f"\nInstalled platforms:\n")
            for key, success in results.items():
                if success:
                    f.write(f"  - {key}\n")
        print_success(f"Version info saved: {version_file}")
    except Exception as e:
        print_warning(f"Failed to save version info: {e}")
    
    return success_count, fail_count

def get_current_platform_binary():
    """获取当前平台的二进制文件路径"""
    current_system = platform.system().lower()
    current_machine = platform.machine().lower()
    
    arch_map = {
        'amd64': 'amd64',
        'x86_64': 'amd64',
        'i386': '386',
        'i686': '386',
        '386': '386',
        'arm64': 'arm64',
        'aarch64': 'arm64',
        'arm': 'arm'
    }
    current_arch = arch_map.get(current_machine, current_machine)
    
    skill_dir = get_skill_directory()
    binary_dir = os.path.join(skill_dir, 'binaries', f"{current_system}_{current_arch}")
    binary_name = f"xray{'.exe' if current_system == 'windows' else ''}"
    binary_path = os.path.join(binary_dir, binary_name)
    
    if os.path.exists(binary_path):
        return binary_path
    return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='xray Multi-Platform Client Download Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all platforms
  python install_xray.py --all
  
  # Download specific platform
  python install_xray.py --platform linux --arch amd64
  
  # Download current platform
  python install_xray.py
  
  # Check downloaded version
  python install_xray.py --version
        """
    )
    
    parser.add_argument('--all', action='store_true', 
                        help='Download xray for all platforms')
    parser.add_argument('--platform', choices=['linux', 'windows', 'darwin'],
                        help='Specify platform')
    parser.add_argument('--arch', 
                        choices=['amd64', '386', 'arm64', 'arm'],
                        help='Specify architecture')
    parser.add_argument('--dest', 
                        help='Specify download directory (default: skill/binaries)')
    parser.add_argument('--version', action='store_true',
                        help='Check current downloaded version')
    parser.add_argument('--use-local', action='store_true',
                        help='Use locally downloaded binary')
    
    args = parser.parse_args()
    
    # 查看版本
    if args.version:
        binary_path = get_current_platform_binary()
        if binary_path:
            print_success(f"Found local xray: {binary_path}")
            try:
                result = subprocess.run([binary_path, 'version'], 
                                      capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print_error(f"Failed to get version: {e}")
        else:
            skill_dir = get_skill_directory()
            binaries_dir = os.path.join(skill_dir, 'binaries')
            if os.path.exists(binaries_dir):
                print_info("Downloaded platforms:")
                for item in os.listdir(binaries_dir):
                    item_path = os.path.join(binaries_dir, item)
                    if os.path.isdir(item_path):
                        print(f"  - {item}")
                
                version_file = os.path.join(binaries_dir, 'version.txt')
                if os.path.exists(version_file):
                    print()
                    with open(version_file, 'r') as f:
                        print(f.read())
            else:
                print_warning("No downloaded xray clients found")
                print_info("Please run: python install_xray.py --all")
        return 0
    
    # 下载所有平台
    if args.all:
        dest_dir = args.dest
        success, fail = download_all_platforms(dest_dir)
        return 0 if fail == 0 else 1
    
    # 下载指定平台
    if args.platform:
        arch = args.arch
        if not arch:
            arch = 'amd64'
        
        dest_dir = args.dest
        if not dest_dir:
            skill_dir = get_skill_directory()
            dest_dir = os.path.join(skill_dir, 'binaries')
        
        success = download_platform(args.platform, arch, dest_dir)
        return 0 if success else 1
    
    # 默认：下载当前平台
    print_info("No platform specified, downloading for current platform...")
    current_system = platform.system().lower()
    current_machine = platform.machine().lower()
    
    arch_map = {
        'amd64': 'amd64',
        'x86_64': 'amd64',
        'i386': '386',
        'i686': '386',
        '386': '386',
        'arm64': 'arm64',
        'aarch64': 'arm64',
        'arm': 'arm'
    }
    current_arch = arch_map.get(current_machine, current_machine)
    
    skill_dir = get_skill_directory()
    dest_dir = os.path.join(skill_dir, 'binaries')
    
    # 检查是否已存在
    binary_path = get_current_platform_binary()
    if binary_path and args.use_local:
        print_success(f"Using locally installed xray: {binary_path}")
        try:
            result = subprocess.run([binary_path, 'version'], 
                                  capture_output=True, text=True)
            print(result.stdout)
            return 0
        except Exception as e:
            print_error(f"Verification failed: {e}")
            return 1
    
    success = download_platform(current_system, current_arch, dest_dir)
    
    if success:
        binary_path = get_current_platform_binary()
        print("\n" + "=" * 60)
        print_success("xray installation complete!")
        print(f"\nBinary location: {binary_path}")
        print("\nQuick Start:")
        print(f"  1. Scan single URL: {binary_path} webscan --url http://example.com")
        print(f"  2. Crawler scan: {binary_path} webscan --basic-crawler http://example.com")
        print(f"  3. Proxy scan: {binary_path} webscan --listen 127.0.0.1:7777")
        print(f"  4. View help: {binary_path} webscan --help")
        print("\nDocumentation: https://docs.xray.cool")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
