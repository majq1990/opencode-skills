# xray 多平台客户端

## 已安装平台

- [x] **windows_amd64** - 已安装 (v1.9.11 COMMUNITY)
- [ ] linux_amd64 - 需要手动下载
- [ ] linux_386 - 需要手动下载
- [ ] linux_arm64 - 需要手动下载
- [ ] darwin_amd64 - 需要手动下载
- [ ] darwin_arm64 - 需要手动下载

## 手动下载其他平台

由于 GitHub 下载速度较慢，建议手动下载其他平台版本：

### 方法 1：直接下载

访问官方 Release 页面：
```
https://github.com/chaitin/xray/releases/tag/1.9.11
```

下载对应平台的文件：
- Windows: `xray_windows_amd64.exe.zip`
- Linux: `xray_linux_amd64.zip`
- macOS: `xray_darwin_amd64.zip`

### 方法 2：使用镜像加速

在 GitHub URL 前添加镜像前缀：

**原始 URL:**
```
https://github.com/chaitin/xray/releases/download/1.9.11/xray_windows_amd64.exe.zip
```

**镜像 URL (推荐):**
```
https://ghfast.top/https://github.com/chaitin/xray/releases/download/1.9.11/xray_windows_amd64.exe.zip
```

### 方法 3：使用脚本下载

运行安装脚本（可能需要较长时间）：

```bash
# 下载所有平台
python scripts/install_xray.py --all

# 下载指定平台
python scripts/install_xray.py --platform linux --arch amd64
```

## 安装位置

所有平台版本应放置在以下目录结构中：

```
binaries/
├── version.txt              # 版本信息
├── windows_amd64/
│   └── xray.exe            # Windows x64 (已安装)
├── windows_386/
│   └── xray.exe            # Windows x86
├── linux_amd64/
│   └── xray                # Linux x64
├── linux_386/
│   └── xray                # Linux x86
├── linux_arm64/
│   └── xray                # Linux ARM64
├── darwin_amd64/
│   └── xray                # macOS Intel
└── darwin_arm64/
    └── xray                # macOS Apple Silicon
```

## 下载链接模板

使用以下模板替换 `{platform}` 和 `{arch}`：

```
https://github.com/chaitin/xray/releases/download/1.9.11/xray_{platform}_{arch}.zip
```

支持的组合：
- `windows_amd64` / `windows_386`
- `linux_amd64` / `linux_386` / `linux_arm64`
- `darwin_amd64` / `darwin_arm64`

## 验证安装

下载后验证文件完整性：

```bash
# Windows
.\binaries\windows_amd64\xray.exe version

# Linux/macOS
./binaries/linux_amd64/xray version
```

## 版本信息

当前版本：**1.9.11** (COMMUNITY)

最后更新：2026-06-16
