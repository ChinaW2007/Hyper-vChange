using System.ComponentModel;
using System.Windows;
using System.Windows.Media;

namespace HyperVSwitch
{
    public partial class MainWindow : Window, INotifyPropertyChanged
    {
        private HyperVDetail _detail;

        private string _statusTitle = "检测中...";
        public string StatusTitle
        {
            get => _statusTitle;
            set { _statusTitle = value; OnPropertyChanged(nameof(StatusTitle)); }
        }

        private string _statusDescription = "";
        public string StatusDescription
        {
            get => _statusDescription;
            set { _statusDescription = value; OnPropertyChanged(nameof(StatusDescription)); }
        }

        private Brush _statusColor = new SolidColorBrush(Color.FromRgb(0x99, 0x99, 0x99));
        public Brush StatusColor
        {
            get => _statusColor;
            set { _statusColor = value; OnPropertyChanged(nameof(StatusColor)); }
        }

        private string _currentMode = "";
        public string CurrentMode
        {
            get => _currentMode;
            set { _currentMode = value; OnPropertyChanged(nameof(CurrentMode)); }
        }

        private string _modeEmoji = "";
        public string ModeEmoji
        {
            get => _modeEmoji;
            set { _modeEmoji = value; OnPropertyChanged(nameof(ModeEmoji)); }
        }

        private string _detailInfo = "";
        public string DetailInfo
        {
            get => _detailInfo;
            set { _detailInfo = value; OnPropertyChanged(nameof(DetailInfo)); }
        }

        private string _toggleButtonText = "切换";
        public string ToggleButtonText
        {
            get => _toggleButtonText;
            set { _toggleButtonText = value; OnPropertyChanged(nameof(ToggleButtonText)); }
        }

        private Brush _toggleButtonColor = new SolidColorBrush(Color.FromRgb(0x42, 0xA5, 0xF5));
        public Brush ToggleButtonColor
        {
            get => _toggleButtonColor;
            set { _toggleButtonColor = value; OnPropertyChanged(nameof(ToggleButtonColor)); }
        }

        private LinearGradientBrush _modeGradientBrush = new LinearGradientBrush(
            Color.FromRgb(0x42, 0xA5, 0xF5), Color.FromRgb(0x1E, 0x88, 0xE5), 0.0);
        public LinearGradientBrush ModeGradientBrush
        {
            get => _modeGradientBrush;
            set { _modeGradientBrush = value; OnPropertyChanged(nameof(ModeGradientBrush)); }
        }

        private bool _showRebootBanner;
        public bool ShowRebootBanner
        {
            get => _showRebootBanner;
            set { _showRebootBanner = value; OnPropertyChanged(nameof(ShowRebootBanner)); }
        }

        public MainWindow()
        {
            InitializeComponent();
            DataContext = this;
            Loaded += async (s, e) => await RefreshStatusAsync();
        }

        private async System.Threading.Tasks.Task RefreshStatusAsync()
        {
            await System.Threading.Tasks.Task.Run(() =>
            {
                _detail = HyperVManager.GetCurrentDetail();
            });

            ApplyDetailToUI(_detail);
        }

        private void ApplyDetailToUI(HyperVDetail detail)
        {
            switch (detail.HyperVState)
            {
                case HyperVState.Enabled:
                    StatusTitle = "Hyper-V 虚拟化已开启";
                    StatusDescription = "适合运行 WSL2、Docker、Android 模拟器";
                    StatusColor = new SolidColorBrush(Color.FromRgb(0x4C, 0xAF, 0x50));
                    CurrentMode = "WSL 模式";
                    ModeEmoji = "🐧";
                    ModeGradientBrush = new LinearGradientBrush(
                        Color.FromRgb(0x00, 0x96, 0x88), Color.FromRgb(0x00, 0x78, 0x6B), 0.0);
                    ToggleButtonText = "🔧 切换到 VM 模式 (关闭 Hyper-V)";
                    ToggleButtonColor = new SolidColorBrush(Color.FromRgb(0xFF, 0x98, 0x00));
                    ShowRebootBanner = false;
                    break;

                case HyperVState.Disabled:
                    StatusTitle = "Hyper-V 虚拟化已关闭";
                    StatusDescription = "适合运行 VMware、VirtualBox 等虚拟机";
                    StatusColor = new SolidColorBrush(Color.FromRgb(0xFF, 0x98, 0x00));
                    CurrentMode = "VM 模式";
                    ModeEmoji = "💻";
                    ModeGradientBrush = new LinearGradientBrush(
                        Color.FromRgb(0xFF, 0x70, 0x42), Color.FromRgb(0xE6, 0x51, 0x00), 0.0);
                    ToggleButtonText = "🔧 切换到 WSL 模式 (开启 Hyper-V)";
                    ToggleButtonColor = new SolidColorBrush(Color.FromRgb(0x42, 0xA5, 0xF5));
                    ShowRebootBanner = false;
                    break;

                default:
                    StatusTitle = "未能检测到 Hyper-V 配置";
                    StatusDescription = "请以管理员身份运行此应用";
                    StatusColor = new SolidColorBrush(Color.FromRgb(0x99, 0x99, 0x99));
                    CurrentMode = "未知";
                    ModeEmoji = "❓";
                    ModeGradientBrush = new LinearGradientBrush(
                        Color.FromRgb(0x78, 0x90, 0x9C), Color.FromRgb(0x54, 0x6E, 0x7A), 0.0);
                    ToggleButtonText = "请以管理员身份重新运行";
                    ToggleButtonColor = new SolidColorBrush(Color.FromRgb(0x99, 0x99, 0x99));
                    ShowRebootBanner = false;
                    break;
            }

            DetailInfo = detail.DetailInfo;
        }

        private async void ToggleButton_Click(object sender, RoutedEventArgs e)
        {
            if (_detail == null) return;

            bool enableHyperV;
            string confirmMsg;

            if (_detail.HyperVState == HyperVState.Enabled)
            {
                enableHyperV = false;
                confirmMsg = "确定要关闭 Hyper-V 吗？\n\n关闭后：\n✅ VMware / VirtualBox 可以流畅运行\n⚠️ WSL2 将不可用（WSL1 仍可使用）\n⚠️ 需要重启电脑";
            }
            else if (_detail.HyperVState == HyperVState.Disabled)
            {
                enableHyperV = true;
                confirmMsg = "确定要开启 Hyper-V 吗？\n\n开启后：\n✅ WSL2 可以流畅运行\n⚠️ VMware / VirtualBox 可能无法正常使用\n⚠️ 需要重启电脑";
            }
            else
            {
                MessageBox.Show("无法检测到当前 Hyper-V 状态，请以管理员身份运行此应用。",
                    "检测失败", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var result = MessageBox.Show(confirmMsg, "确认切换",
                MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes) return;

            var button = sender as System.Windows.Controls.Button;
            if (button != null) button.IsEnabled = false;

            var (success, message) = await HyperVManager.SetHyperVEnabledAsync(enableHyperV);

            if (success)
            {
                ShowRebootBanner = true;

                if (enableHyperV)
                {
                    StatusTitle = "Hyper-V 将开启（待重启）";
                    StatusDescription = "重启后 WSL2 将可正常使用";
                    StatusColor = new SolidColorBrush(Color.FromRgb(0x66, 0xBB, 0x6A));
                    CurrentMode = "WSL 模式 (待重启)";
                    ModeEmoji = "🐧⏳";
                    ModeGradientBrush = new LinearGradientBrush(
                        Color.FromRgb(0x00, 0x96, 0x88), Color.FromRgb(0x00, 0x78, 0x6B), 0.0);
                    ToggleButtonText = "✅ 已设置，等待重启";
                    ToggleButtonColor = new SolidColorBrush(Color.FromRgb(0x99, 0x99, 0x99));
                    DetailInfo = "✅ 已设置开启 Hyper-V\n⏳ 请重启电脑以完成切换\n重启后 WSL2 即可正常使用";
                }
                else
                {
                    StatusTitle = "Hyper-V 将关闭（待重启）";
                    StatusDescription = "重启后 VMware/VirtualBox 将可正常使用";
                    StatusColor = new SolidColorBrush(Color.FromRgb(0xFF, 0xA7, 0x26));
                    CurrentMode = "VM 模式 (待重启)";
                    ModeEmoji = "💻⏳";
                    ModeGradientBrush = new LinearGradientBrush(
                        Color.FromRgb(0xFF, 0x70, 0x42), Color.FromRgb(0xE6, 0x51, 0x00), 0.0);
                    ToggleButtonText = "✅ 已设置，等待重启";
                    ToggleButtonColor = new SolidColorBrush(Color.FromRgb(0x99, 0x99, 0x99));
                    DetailInfo = "✅ 已设置关闭 Hyper-V\n⏳ 请重启电脑以完成切换\n重启后 VMware/VirtualBox 即可正常使用";
                }
            }
            else
            {
                MessageBox.Show($"操作失败：{message}", "错误",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }

            if (button != null) button.IsEnabled = !ShowRebootBanner;
            _detail = HyperVManager.GetCurrentDetail();
        }

        private void RestartButton_Click(object sender, RoutedEventArgs e)
        {
            var result = MessageBox.Show(
                "确定要立即重启电脑吗？\n\n请确保已保存所有工作。",
                "确认重启", MessageBoxButton.YesNo, MessageBoxImage.Warning);

            if (result == MessageBoxResult.Yes)
            {
                System.Diagnostics.Process.Start("shutdown.exe", "/r /t 10 /c \"Hyper-V 切换助手将在 10 秒后重启电脑\"");
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
