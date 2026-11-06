# 基础时间线

路径相对时间线 JSON 所在目录，不相对命令行目录。width/height 是正偶数，fps 是 1–60 整数，duration 必须落在完整帧上。每段保留原声；无声段补静音供拼接，不伪造旁白。视频裁切默认保留整帧、黑边补齐，不硬裁人物。

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "deliberate_silent": false,
  "clips": [
    {"path": "素材/片段.mp4", "start": 1, "duration": 3},
    {"path": "素材/照片.jpg", "duration": 3, "verified_srgb": true}
  ]
}
```

verified_srgb 只能在实际核对或转换照片颜色配置后填写，不是绕过颜色检查的按钮。照片输入仅 JPG/PNG；HEIC、P3、HDR 和动态图片先另行转换。视频必须有完整 bt709 标记及已知色彩范围，不接受只改标签的假转换。

整片有意无声时才设置 deliberate_silent=true。该项跳过音量信号门槛，仍执行完整解码；语音片音量过低应修复。基本装配之后，字幕、旁白、音乐、照片推拉与转场按用户需求另用已具备工具处理。本脚本不宣称实现这些效果。
