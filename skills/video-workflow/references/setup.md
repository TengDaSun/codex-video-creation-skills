# 环境配置

Python 3.10+ 用于本包脚本；Mac 常用 python3，Windows 用 py -3 或 python。检查实际版本再运行。FFmpeg/ffprobe 用于媒体读取和基础剪辑；不需要全部安装所有剪辑产品。

先运行 scripts/doctor.py：只检查，不安装、不访问账号、不联网。整理索引在没有 FFmpeg 时仍可按哈希工作；缺失元数据归未知。

依赖安装由 Codex 根据用户系统和现有包管理器执行，先检查是否已有兼容工具，不运行未经阅读的远端脚本。Mac 有 Homebrew 时可用 brew install ffmpeg；Python 从已有管理器或 python.org 获取。Windows 从 ffmpeg.org/download.html 指向的构建和 python.org 获取，把 bin 加入 PATH，重开终端后验证。exiftool.org 提供可选照片 EXIF 工具。具体当前安装方式以各项目官方说明为准。

只做基础本地剪辑不需 API Key。转写、AI 配音、生成图片的服务费用与 Codex 订阅分开核实；先用已具备工具。平台登录使用学生自己账号，凭据不进入分享包、项目设置或聊天输出。

Windows 路径通过 Python pathlib 和参数列表处理，不依赖 Bash、ln 或 Unix 路径。未在 Windows 实机测试前，状态必须写“待实测”，不能仅由代码跨平台推断成功。
