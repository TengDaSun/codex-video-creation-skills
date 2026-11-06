---
name: video-edit
description: 根据真实照片、视频与原声确定看点，制作视频并检查实际导出。
metadata:
  version: "2026.11.05"
---

# 自动剪辑

依赖随包安装的 video-workflow。读取 [剪辑与验收](../video-workflow/references/editing.md)；需要选工具才读 [工具分工](../video-workflow/references/tools.md)。

先看素材及原声，确定面向谁、具体看点、开头、删留和收口，记录到发布清单 production_plan。按最后认可版本局部修改，保留未要求改变的样式。首次无明确时长可提出约 30–60 秒预览，不能为了凑长度编内容。

## 可直接执行的基础路径

本技能 `scripts/render_sequence.py` 接受 [时间线格式](references/timeline.md)，将选定视频切段、照片停留、保留原声并适配画幅，输出 H.264/AAC MP4。先用 ffprobe 核对源色彩；此脚本仅供已核实的 SDR bt709 视频及 sRGB JPG/PNG，拒绝 HDR、广色域、色彩未知视频和动态图片。HDR 素材应先用已验证工具实际映射并看片；不能仅重写标签。

命令：`python scripts/render_sequence.py "时间线.json" "新的成片.mp4"`。脚本不识别内容、不生成字幕或旁白；Codex 负责选段、编写时间线，按需求用实际具备的工具完成文字、转写、混音等。脚本是稳定的基础装配路径，不把基础串接称为完整精剪。

需要转写时先检查用户已有工具或字幕；没有可用转写能力，准确报告缺项，不从听不清的音频编造文字。无授权的收费生成先说明。AI 配音和图片生成可选，不能强制购买服务。

导出后使用通用 `scripts/check_media.py`，有意无声用 `--allow-silent`；检查尺寸按本条目标传入。机器检查不代替完整看听、字幕与真实肤色检查。分别记录未核验项目，成片与封面文案一起交付。
