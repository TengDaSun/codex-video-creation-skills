# 平台接入与执行

优先使用已连接的适用工具；没有时，使用允许访问的官方创作者后台。小红书入口 https://creator.xiaohongshu.com/ ，抖音 https://creator.douyin.com/ ，视频号 https://channels.weixin.qq.com/ 。访问失败按实际错误处理，不能绕过限制。

## 可选 sau 路径

分享者使用过 social-auto-upload 的 sau CLI。这个包不附带该第三方代码、浏览器或 Cookie；上游版本不一定有相同 CLI，不把安装上游仓库等同于已接通。上游项目 https://github.com/dreammis/social-auto-upload 。需要时读取当前项目说明与授权，选兼容版本，在独立虚拟环境安装；不要安装名称相近但来源未核实的包。若没有 sau，不为简单发布无限改造第三方代码，改用已允许的后台操作。

先运行 sau --help、sau douyin --help 或 sau xiaohongshu --help，实际核实支持 login/check/upload-video。以下只是兼容 CLI 的命令契约，应以安装版本帮助为准：

- sau PLATFORM login --account STUDENT_ALIAS：学生扫码，展示工具实际二维码。
- sau PLATFORM check --account STUDENT_ALIAS：检查当前登录，不输出 Cookie。
- sau PLATFORM upload-video --account STUDENT_ALIAS --file VIDEO --title TITLE --desc BODY --tags TAGS --thumbnail COVER

PLATFORM 为 douyin 或 xiaohongshu；参数使用程序列表传给 subprocess，不把用户标题拼接成 shell 命令。没有 --schedule 的兼容命令通常立即发布，绝不能拿它试登录或存草稿。

定时参数与时区需按当前 CLI 和后台验证；清单保存带偏移的 ISO 时间及 IANA 时区，后台时区可能不同于电脑。无法确定时区就不提交定时任务。分钟值、日期和发布账号都在提交前后回读；不保证工具支持任意精度或平台任意未来时刻。

## 浏览器/手动路径

读取当前连接工具能力；通过真实可见后台选择文件、填文案、设置封面与授权排期。平台要求用户扫码或验证时交给本人。无可用浏览器操作能力时给出实际文件与完整文案，状态记 awaiting_manual_publish，等待真实回执。不在本地伪造“已发布”。

无论用哪条路径，每个平台保留提交时间、目标账号、文件指纹、状态和实际回执。不因 CLI 返回零就认定公开，需后台作品状态；超时记 unknown 并先核查。
