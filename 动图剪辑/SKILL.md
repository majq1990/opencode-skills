---
name: gif-editor
description: 动图剪辑（Windows PowerShell）。培训 PPT 全流程：录屏（ScreenToGif GUI + ffmpeg gdigrab CLI）+ 剪辑（mp4/gif 时间段裁剪、加速、烧字幕、画面裁切、体积压缩、多段拼接）。触发词：动图剪辑 / gif 剪辑 / gif 压缩 / gif 优化 / 录屏 / 录 gif / mp4 转 gif / gif 加字幕 / gif 拼接 / screentogif / gif-editor。
---

# 动图剪辑 skill

面向 Windows 培训场景：**录屏 → 剪辑 → 压缩**一站式。ScreenToGif 或 gif123 出的 mp4/gif，批量剪成适合 PPT/钉钉/飞书分享的小体积、带步骤说明的动图。

## 工具链（全部国内可达）

集中安装到 `C:\tools\gif-editor\`（已加用户 PATH）。装完后新开 PowerShell 用 `ffmpeg -version` / `gifski --version` / `gifsicle --version` 验证。

| 工具 | 干什么 | 装法（国内友好） |
|---|---|---|
| **ScreenToGif** | 录屏 GUI 主力：录 mp4/gif、简单编辑（剪帧/水印/字幕） | `winget install -e --id NickeManarin.ScreenToGif` |
| **ffmpeg** | 剪辑万金油：mp4→gif、时间裁剪、变速、烧字幕、裁画面；也可 gdigrab 命令行录屏 | `winget install -e --id Gyan.FFmpeg` |
| **gifski** | 顶级 GIF 编码器，把 mp4 或 png 序列做出最高画质 gif | `winget install -e --id ImageOptim.gifski`；winget 装失败时下 GitHub Release `gifski-*.tar.xz`，走 `ghfast.top` 加速：`https://ghfast.top/https://github.com/ImageOptim/gifski/releases/latest`，`tar -xf` 解压取 `win/gifski.exe` 丢到 `C:\tools\gif-editor\` |
| **gifsicle** | 老牌 GIF 后处理：压缩、裁时间段、拼接、单帧改动、无损优化 | 官网 https://eternallybored.org/misc/gifsicle/ 下 `gifsicle-*-win64.zip`（国内还行）；备选 `ghfast.top` 加速 GitHub `kohler/gifsicle` release；解压丢到 `C:\tools\gif-editor\` |
| **gif123**（可选） | 极简 GIF 录屏 GUI（用户已用），拖框即录 | GitHub aardio/Gif123；已在 `C:\Users\majq1\AppData\Local\gif123\` |

选型逻辑：**ScreenToGif/gif123 GUI 录屏 → ffmpeg 剪辑与烧字幕 → gifski 高质量编码 → gifsicle 体积二次压缩和后期拼接**。四段接力用最合适。

---

## 能力块 1：视频 → GIF（高质量）

### 1A. ffmpeg 一步出 GIF（palette 法，画质好、够小）

```powershell
ffmpeg -i "<输入.mp4>" -vf "fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" "<输出.gif>"
```

参数解读：
- `fps=15` 培训动图 12–15 帧足够；越低越小
- `scale=800:-1` 宽度 800，高度按比例；PPT 用 800/600 都够
- `palettegen + paletteuse` 两遍走生成 256 色调色板，避免默认 GIF 花屏
- `dither=bayer:bayer_scale=5` 消除色带

### 1B. gifski 走最高画质（PPT 特写/UI 演示优先）

```powershell
# 先 ffmpeg 抽 png 序列
ffmpeg -i "<输入.mp4>" -vf "fps=15,scale=800:-1:flags=lanczos" "<frames_%04d.png>"
# gifski 编码
gifski -o "<输出.gif>" --fps 15 --quality 90 --width 800 frames_*.png
# 清理临时帧
Remove-Item frames_*.png
```

`--quality 90` 是画质，60 起就很好；`--lossy-quality` 可以再进一步压。

---

## 能力块 2：GIF/视频 裁剪时间段

保留第 5 秒到第 15 秒（去掉前 3 秒 + 后段）：

```powershell
# 视频剪时间段（快，无重编码）
ffmpeg -ss 00:00:05 -to 00:00:15 -i "<输入.mp4>" -c copy "<裁剪.mp4>"

# 直接对 gif 裁时间段：先看总帧数
gifsicle "<输入.gif>" -I | Select-String "loop\|frames"
# 保留第 50–150 帧（gifsicle 帧号从 0 起）
gifsicle "<输入.gif>" "#50-150" -o "<输出.gif>"
```

---

## 能力块 3：加速 / 慢放

### 视频侧（ffmpeg，推荐，剪完再转 gif）

```powershell
# 2 倍速
ffmpeg -i "<输入.mp4>" -filter:v "setpts=0.5*PTS" -an "<快放.mp4>"
# 1.5 倍速
ffmpeg -i "<输入.mp4>" -filter:v "setpts=PTS/1.5" -an "<快放.mp4>"
# 0.5 倍速（慢放）
ffmpeg -i "<输入.mp4>" -filter:v "setpts=2.0*PTS" -an "<慢放.mp4>"
```

### GIF 侧（gifsicle，改帧延时）

```powershell
# 所有帧统一到 5/100 秒（=20fps 播放，等效加速）
gifsicle "<输入.gif>" -d5 -o "<快放.gif>"
# 20/100 秒 = 5fps（慢放）
gifsicle "<输入.gif>" -d20 -o "<慢放.gif>"
```

---

## 能力块 4：加字幕（烧硬字幕）

推荐：**先写 srt，ffmpeg 烧进视频，再转 gif**。字幕在 gif 里就是像素，不会掉。

### 4A. 手写 srt（PPT 培训步骤最快的姿势）

新建 `steps.srt`（记事本存 UTF-8 无 BOM）：

```
1
00:00:00,000 --> 00:00:03,000
第一步：打开系统设置

2
00:00:03,000 --> 00:00:07,000
第二步：进入用户管理

3
00:00:07,000 --> 00:00:10,000
第三步：新增账号
```

### 4B. ffmpeg 烧字幕 + 转 gif（一条命令）

```powershell
ffmpeg -i "<输入.mp4>" -vf "subtitles=steps.srt:force_style='FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=20',fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" "<带字幕.gif>"
```

样式说明：白字黑边描 2px、微软雅黑 22 号、底部居中距底 20px。中文务必用 `Microsoft YaHei` 或 `SimHei`，否则显示方框。

### 4C. 简单叠一行文字（不用 srt，drawtext 法）

```powershell
ffmpeg -i "<输入.mp4>" -vf "drawtext=fontfile='C\:/Windows/Fonts/msyh.ttc':text='点击提交按钮':fontcolor=white:fontsize=24:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-40,fps=15,scale=800:-1:flags=lanczos" -y "<单条字幕.gif>"
```

PowerShell 里 `C:/Windows/Fonts/msyh.ttc` 路径中的冒号要转义成 `C\:/...`。

---

## 能力块 5：裁切画面区域（只保留矩形）

用 ffmpeg 的 `crop=W:H:X:Y`（左上角 X,Y 起，宽 W 高 H）：

```powershell
# 只保留左上角 800x600 区域
ffmpeg -i "<输入.mp4>" -vf "crop=800:600:0:0,fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" "<裁切.gif>"

# 只保留中间的对话框（示例：1920x1080 视频中取中间 1000x700）
ffmpeg -i "<输入.mp4>" -vf "crop=1000:700:460:190,fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" "<对话框.gif>"
```

不确定坐标：先 `ffplay "<输入.mp4>"` 或截一帧 `ffmpeg -i in.mp4 -vframes 1 shot.png`，用画图量像素。

---

## 能力块 6：压缩体积（< 2MB 适合 PPT/钉钉）

三级递进，前一级不够小再上下一级：

### L1. gifsicle 无损优化（先跑，快）

```powershell
gifsicle -O3 "<输入.gif>" -o "<输出.gif>"
```

### L2. gifsicle 有损压缩

```powershell
# lossy 30 几乎看不出损失，80 明显但可接受
gifsicle -O3 --lossy=60 "<输入.gif>" -o "<输出.gif>"
```

### L3. 减色 + 降帧 + 缩尺寸（终极大招）

```powershell
# 减到 128 色 + 缩到宽 600
gifsicle -O3 --lossy=80 --colors 128 --resize-width 600 "<输入.gif>" -o "<输出.gif>"

# ffmpeg 侧降帧重编（10fps + 600 宽）
ffmpeg -i "<输入.gif>" -vf "fps=10,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse" "<小.gif>"
```

看结果大小：`(Get-Item "<输出.gif>").Length / 1MB`

---

## 能力块 7：多段 GIF 拼接

### 7A. gifsicle 直接顺序拼（帧率相同最稳）

```powershell
gifsicle "<段1.gif>" "<段2.gif>" "<段3.gif>" -o "<合并.gif>"
```

### 7B. 视频段先合再转 gif（不同分辨率/帧率友好）

```powershell
# 建 concat 列表
@"
file '<段1.mp4>'
file '<段2.mp4>'
file '<段3.mp4>'
"@ | Out-File -Encoding ascii concat.txt

ffmpeg -f concat -safe 0 -i concat.txt -c copy "<合并.mp4>"

# 再走能力块 1 转 gif
```

---

## 典型培训流程（60s mp4 → 10s 带字幕 1.5MB gif）

假设：`raw.mp4` 是 ScreenToGif 录的 60 秒 1920x1080 操作视频，要做成两句字幕的 10 秒 gif 塞 PPT。

```powershell
# 1) 裁时间段：保留 20s–30s 这 10 秒关键操作
ffmpeg -ss 00:00:20 -to 00:00:30 -i "raw.mp4" -c copy "step1.mp4"

# 2) 裁画面：只留中间 1200x800 的操作区
ffmpeg -i "step1.mp4" -vf "crop=1200:800:360:140" -c:v libx264 -crf 18 "step2.mp4"

# 3) 写字幕
@"
1
00:00:00,000 --> 00:00:05,000
第一步：点击"新增"

2
00:00:05,000 --> 00:00:10,000
第二步：填写名称后保存
"@ | Out-File -Encoding utf8 steps.srt

# 4) 烧字幕 + 转 gif（一步到位）
ffmpeg -i "step2.mp4" -vf "subtitles=steps.srt:force_style='FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=20',fps=12,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" -y "step3.gif"

# 5) 二次压缩到 <2MB
gifsicle -O3 --lossy=60 "step3.gif" -o "final.gif"

# 6) 查体积
"{0:N2} MB" -f ((Get-Item final.gif).Length / 1MB)

# 7) 清理
Remove-Item step1.mp4, step2.mp4, step3.mp4, steps.srt
```

---

## 常见坑

1. **中文字幕方框**：`force_style` 里必须指定装了中文的字体（`Microsoft YaHei` / `SimHei` / `Noto Sans CJK SC`）。
2. **PowerShell 路径带空格**：一律用双引号包，别用反引号续行，用 `` ` ``（反撇）在行尾续行也行但容易翻车，宁可写一行长命令。
3. **gifsicle 找不到**：`choco install gifsicle -y` 有时需要 PowerShell 管理员；choco 没装就手动到 https://eternallybored.org/misc/gifsicle/ 下 win64 zip，解压把 `gifsicle.exe` 丢到 `C:\Windows\` 或 PATH 里任一目录。
4. **gif 越压越花**：先降 `fps` 和 `scale`，再动 `--colors` 和 `--lossy`；不要一上来就减色到 64。
5. **ScreenToGif 直接出的 gif 已经很小但花**：说明它内部编码器不是 gifski；重新走 `gif → ffmpeg 抽 png → gifski` 一遍能显著提画质。
6. **烧字幕位置乱**：`Alignment=2` 底部居中，`=6` 顶部居中，`=5` 中间居中；`MarginV` 控距离上/下边缘的像素。
