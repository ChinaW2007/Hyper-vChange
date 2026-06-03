# Hyper-V Switch Manager

一个用于管理 Windows Hyper-V 虚拟化功能的工具，可方便地在 WSL2 和 VMware/VirtualBox 之间切换。

## 功能特性

- **状态检测**: 检测当前 Hyper-V 的启用状态
- **一键切换**: 在 WSL2 模式和 VM 模式之间快速切换
- **详细信息**: 显示当前模式的兼容性说明

## 模式说明

| 模式 | Hyper-V 状态 | 兼容性 |
|------|-------------|--------|
| **WSL2** | 开启 | ✅ WSL2 可流畅运行<br>⚠️ VMware/VirtualBox 可能无法正常使用 |
| **VM** | 关闭 | ✅ VMware/VirtualBox 可流畅运行<br>⚠️ WSL2 不可用（WSL1 仍可用） |

## 运行方式

### 方法一：运行 C# 应用

1. 使用 Visual Studio 打开 `HyperVSwitch.sln`
2. 以**管理员身份**运行项目

### 方法二：运行 Python 脚本

```bash
python hyperv_switch.py
```

### 方法三：运行批处理文件

```bash
run.bat
```

## 注意事项

- **必须以管理员身份运行**，否则无法修改系统配置
- 修改 Hyper-V 设置后需要**重启电脑**才能生效
- 切换到 VM 模式后，WSL2 将不可用，需要切换回 WSL2 模式才能使用

## 项目结构

```
Hyper-vChange/
├── HyperVSwitch/          # C# WPF 项目
│   ├── App.xaml          # 应用程序入口
│   ├── MainWindow.xaml   # 主窗口
│   └── HyperVManager.cs  # Hyper-V 管理逻辑
├── hyperv_switch.py      # Python 版本脚本
├── run.bat               # 快速运行批处理
└── HyperVSwitch.sln      # Visual Studio 解决方案
```

## 技术栈

- **C# .NET 8** - 主应用程序框架
- **WPF** - 用户界面
- **bcdedit** - 系统配置工具
- **PowerShell** - Windows 功能检测

## License

MIT License
