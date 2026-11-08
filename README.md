# 用终端和 AI 无线控制 iPhone

这是一份独立的中文配置指南，帮助你把真实 iPhone 接入 Codex 等 AI 客户端。手机控制能力来自 Joseph Zhou 与贡献者开发的 [Poki](https://github.com/JosssphZhou/poki)，本仓库不重新发布 Poki 源码，也不是官方项目。

**推荐直接克隆作者的 Poki；把本指南分享给需要配置的人即可。** 只有准备修改控制引擎时才需要 fork 上游。

## 能做什么、是否收费

AI 读取手机界面上的文字、按钮和输入框，再执行点击、滑动、输入与打开 App。也能截图，在无障碍信息不足时使用文字识别。默认真机方式不需要越狱，也不需要安装 WebDriverAgent。

Poki MCP 与 Poki Agent 免费开源，许可证为 AGPL-3.0-only。接入现有 Codex 等客户端，使用该客户端原有模型账号与额度；使用 API 密钥时，按模型服务商规则付费。免费软件不等于无限免费模型调用。

本指南优先使用 MCP，即让现有 AI 客户端调用手机工具，不安装可选的独立 Poki Agent，不需要额外执行 `poki login`。

## 适用环境与验证边界

- Mac，macOS 15 或更新，完整 Xcode，Git，Python 3，Node.js 24+，Rust/Cargo，ffmpeg/ffprobe。
- 首次配对需要能传数据的 USB 线。无线操作需要 Mac 与手机在同一可互通的局域网，手机保持解锁。
- 以 Poki 0.1.1、上游提交 `131a8ebcbf5bae17e09db72c2311eec37ab1d86e` 为本次记录基线，日期 2026-11-08。上游更新后以官方文档为准。
- 本次实际验证：中文界面、竖屏实体 iPhone，有线及拔线后的局域网截图、打开 App、点击；有线中文混合输入及字段读回；无线打开微信并读取会话。
- 新设备、其他系统版本、横屏、跨网络、长期无人值守没有因此获得验证。官方目前主要验证中文竖屏真机。
- 本次全套上游自动测试没有全部通过，部分超时用例单独复验通过，另有用例依赖未安装的可选 Agent。上述真机通过项是独立实测结果。

## 1. 安装 Mac 端

安装完整 Xcode，打开一次并完成首次初始化。仅有 Command Line Tools 不够。

```sh
sw_vers
xcodebuild -version
node -v
cargo --version
python3 --version
command -v ffmpeg ffprobe
```

缺少 Node 或 ffmpeg 时可通过 Homebrew 安装，Rust 可通过 [rustup](https://rustup.rs/) 安装。不要为了本工具覆盖已有开发环境，先检查版本。

```sh
mkdir -p "$HOME/coding"
git clone https://github.com/JosssphZhou/poki.git "$HOME/coding/poki"
cd "$HOME/coding/poki"
./bin/setup
npm start
```

已有该目录时先检查它，不要覆盖或重复克隆。保留服务终端运行，看到 `"event":"ready"` 表示服务启动。默认只监听本机 `127.0.0.1:47825`。

`./bin/setup` 会安装依赖并编译原生桥，不会替你安装 Xcode、签名身份或苹果设备支持镜像。

## 2. 接入 Codex

另开终端：

```sh
cd "$HOME/coding/poki"
codex mcp add poki-mcp -- node "$PWD/src/stdio.mjs"
codex mcp get poki-mcp
```

把上游 `skills/poki-mcp` 整个目录安装到你的客户端技能目录，再新开客户端会话。标准 Codex 可放 `~/.codex/skills/poki-mcp`；若你有统一技能清单或同步脚本，应按自己的管理方式登记，避免下次同步被清理。不要覆盖已有同名技能。

也可以把这句话交给 AI 客户端：

```text
安装 https://github.com/JosssphZhou/poki，遵循根目录 AGENTS.md。只接入本客户端的 MCP 并安装对应技能，不安装独立 Agent。保留其他配置，在需要我操作手机时告诉我具体步骤。
```

其他 MCP 客户端参照[上游安装说明](https://github.com/JosssphZhou/poki/blob/main/docs/install.md)，使用绝对路径配置 `node .../src/stdio.mjs`。客户端和后台服务必须使用相同的 `POKI_MCP_STATE_DIR`；未自定义时均使用默认值。

## 3. 新 iPhone 首次有线配对

每台新手机都需要单独完成，不能复制另一台手机的配对记录。

1. 用 USB 数据线连接 Mac，解锁 iPhone，确认“信任此电脑”。
2. 开启“设置 → 隐私与安全性 → 开发者模式”，按手机提示重启并再次确认。不同系统的菜单可能略有不同，找不到时结合实际页面与官方文档检查。
3. 开启“设置 → 开发者 → UI 自动化”。
4. 为测试临时延长自动锁定时间，保持解锁。下文的 `DEVICE_ID` 要替换为实际设备标识。

```sh
cd "$HOME/coding/poki"
node bin/call.mjs list_devices
node bin/prepare-device.mjs DEVICE_ID
node bin/call.mjs take_screenshot '{"device":"DEVICE_ID"}'
```

选设备时核对型号与标识。连接多台手机时，每条终端调用都带 `device`，不要依赖上一条命令的选择状态。`bin/call.mjs` 每次都会结束自己的会话。

如果截图成功但点击失败，先检查 `prepare-device` 是否确认存在 `com.apple.coredevice.displayservice`。开发者镜像缺失或版本不兼容时，按[官方真机文档](https://github.com/JosssphZhou/poki/blob/main/docs/physical-iphone.md)准备匹配的苹果签名镜像。

## 4. 配置同一局域网无线控制

普通 USB 信任配对不代表本次安装已具备无线控制，必须实际配置、拔线验证。

先保持 USB 连接、手机解锁，并让 Mac 和 iPhone 连接同一可互通网络。访客网络或设备隔离可能阻止互通。

发现手机真正广播的 Bonjour 名称：

```sh
dns-sd -B _remotepairing._tcp local.
# 记下目标服务的实例名称后，Ctrl-C 停止浏览，再解析：
dns-sd -L 'INSTANCE_NAME' _remotepairing._tcp local.
```

解析结果会给出类似 `Phone-Example.local.:49152` 的主机和端口。不要猜设备的 `.local` 名称，也不要把别人的设备实例当成自己的。多台设备时逐项核对，必要时由操作者确认。

```sh
cd "$HOME/coding/poki"
node bin/prepare-remote.mjs DEVICE_ID Phone-Example.local. 49152
node bin/call.mjs list_devices
node bin/call.mjs take_screenshot '{"device":"DEVICE_ID"}'
```

`connection` 应显示 `RemotePairing`。如果服务运行中未识别新配置，停止并重启本次 Poki 服务；不要启动第二个控制同一手机的服务。

现在拔掉数据线，保持解锁，再执行截图与点击：

```sh
python3 native/devices.py
node bin/call.mjs take_screenshot '{"device":"DEVICE_ID"}'
node bin/call.mjs launch_app '{"device":"DEVICE_ID","bundle_id":"com.apple.Preferences"}'
```

`native/devices.py` 应不再将目标设备列为 USB。截图必须是新捕获的页面；点击应有页面变化并读回。只看到设备列表、`sent=true` 或线仍插着时的 RemotePairing，均不等于完成拔线验收。

## 5. 拔线失败时怎么处理

本次遇到过：插线时 RemotePairing 可用，拔线后报告 unreachable；Mac 可以连接手机 Wi-Fi 地址的端口，但原连接助手仍无法工作。重新建立目标设备的助手后恢复，最后使用 Bonjour 名称再次通过拔线截图与点击。没有据此认定所有断连都由同一个原因造成。

先保持手机解锁，核对同一局域网，尝试：

```sh
cd "$HOME/coding/poki"
node bin/call.mjs disconnect_device '{"device":"DEVICE_ID"}'
node bin/call.mjs take_screenshot '{"device":"DEVICE_ID"}'
```

若仍失败，先查看当前页面再重试输入，避免重复发送消息或重复提交。必要时停止正在执行的手机任务后，使用本仓库的助手刷新工具：

```sh
# 默认仅检查，不终止进程
python3 /path/to/poki-iphone-guide/scripts/refresh-wireless.py DEVICE_ID
# 确认没有手机任务在执行后，刷新这一台设备的连接助手
python3 /path/to/poki-iphone-guide/scripts/refresh-wireless.py DEVICE_ID --restart
```

该工具只匹配当前用户、指定安装目录、指定设备配置文件的远程助手，不删除配对记录，不改网络/VPN，不操作手机。它会结束目标连接助手，所以不要在点击、输入或提交进行中使用。配置了自定义位置时用 `--poki-root` 和 `--state-dir` 指定。

Bonjour 名称可适应局域网 IP 变化；临时用数字 IP 定位问题后，不要忘记地址可能变化。手机锁屏不会被普通截图或唤醒操作自动解锁。

## 6. 日常怎么使用

保持 Poki 服务运行，在已接入 MCP 的 AI 客户端里说：

```text
用 Poki 操作目标 iPhone，打开设置，读出 iOS 版本。
打开微信，查看最近的会话消息，只读取，不回复。
```

已有目标设备 ID 时同时告诉客户端，避免误选其他手机。界面文字和截图会进入你配置的模型服务；本地运行控制服务不代表内容不会离开电脑。

读取、点击和输入不是全程只读，点进会话可能改变未读状态。发送消息、删除内容和付款都可能真实发生，应该事先明确任务边界。不要把消息记录、截图、真实账号、设备标识、配对密钥或 `mcp.json` 上传到公开仓库。

## 7. 可选：后台常驻与跨网络

最简单的方式是保留 `npm start` 终端。需要登录后自动启动时，先停止手动运行的 `npm start`，确认没有其他 Poki 服务使用同一端口，再执行：

```sh
python3 - <<'PYTHON'
from pathlib import Path
import os, plistlib, shutil
home = Path.home()
node = shutil.which('node')
assert node, '先安装 Node.js'
root = home / 'coding/poki'
assert (root / 'src/daemon.mjs').is_file(), '先安装 Poki'
logs = home / 'Library/Logs/PokiMCP'
logs.mkdir(parents=True, exist_ok=True, mode=0o700)
logs.chmod(0o700)
for name in ['stdout.log', 'stderr.log']:
    log = logs / name
    log.touch(mode=0o600, exist_ok=True)
    log.chmod(0o600)
agents = home / 'Library/LaunchAgents'
agents.mkdir(parents=True, exist_ok=True)
path = agents / 'local.poki-mcp.plist'
assert not path.exists(), '服务文件已存在，请检查，勿覆盖'
path.write_bytes(plistlib.dumps({
    'Label': 'local.poki-mcp',
    'ProgramArguments': [node, str(root / 'src/daemon.mjs')],
    'WorkingDirectory': str(root),
    'EnvironmentVariables': {'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
    'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 15,
    'StandardOutPath': str(logs / 'stdout.log'),
    'StandardErrorPath': str(logs / 'stderr.log'),
}))
path.chmod(0o600)
print('服务配置已生成')
PYTHON
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.poki-mcp.plist"
launchctl print "gui/$(id -u)/local.poki-mcp"
tail -n 5 "$HOME/Library/Logs/PokiMCP/stdout.log"
```

看到 `event: ready` 对应的 JSON 日志后，再从客户端验证。若此前使用自定义 `POKI_MCP_STATE_DIR`，也要把该值加入服务的 `EnvironmentVariables`，与客户端保持一致。

更新源码后需要重启服务，旧进程不会自动加载新代码：

```sh
launchctl kickstart -k "gui/$(id -u)/local.poki-mcp"
# 停止后台服务：
# launchctl bootout "gui/$(id -u)/local.poki-mcp"
```


跨网络需要另行配置 Tailscale，按[官方远程连接说明](https://github.com/JosssphZhou/poki/blob/main/docs/remote-iphone.md)操作。该路径仍属实验功能，本指南没有验证蜂窝网络、外网远程或 Mac 关机独立运行。iPhone 上 Tailscale 与其他普通 VPN 可能冲突，不要直接覆盖已有网络配置。

## 8. 给另一台手机配置的检查清单

- [ ] Mac 依赖齐全，Poki 服务 ready，客户端 MCP 接入成功。
- [ ] 新手机独立完成 USB 信任、开发者模式、UI 自动化。
- [ ] 核对目标设备，有线截图、点击、输入及读回通过。
- [ ] 找到新手机真正的 Bonjour 服务，独立执行 prepare-remote。
- [ ] 拔线后确认 USB 清单不含目标，重新截图、点击及读回通过。
- [ ] 如需无线输入，另测中文/英文输入、字段读回与清理，不由无线截图结果推断。
- [ ] 已告知解锁、网络、模型额度及数据流向要求。

## 上游与许可证

- [Poki 源码](https://github.com/JosssphZhou/poki)、[官网](https://poki.bot/)、[安装](https://github.com/JosssphZhou/poki/blob/main/docs/install.md)、[真机](https://github.com/JosssphZhou/poki/blob/main/docs/physical-iphone.md)、[已知限制](https://github.com/JosssphZhou/poki/blob/main/docs/verification.md)。
- Poki 原项目为 AGPL-3.0-only，版权属于其作者与贡献者。使用或修改上游代码时遵循上游许可证。
- 本仓库独立编写的指南和辅助脚本使用 MIT 许可证，不改变 Poki 的许可证。
