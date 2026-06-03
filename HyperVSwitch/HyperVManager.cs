using System;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Text.RegularExpressions;

namespace HyperVSwitch
{
    public enum HyperVState
    {
        Unknown,
        Enabled,
        Disabled,
        PendingEnable,
        PendingDisable
    }

    public class HyperVDetail
    {
        public HyperVState HyperVState { get; set; } = HyperVState.Unknown;
        public bool VirtualMachinePlatformEnabled { get; set; }
        public bool HyperVFeatureEnabled { get; set; }
        public bool NeedsReboot { get; set; }
        public string BestMode { get; set; } = "";
        public string Description { get; set; } = "";
        public string DetailInfo { get; set; } = "";
    }

    public static class HyperVManager
    {
        public static HyperVDetail GetCurrentDetail()
        {
            var detail = new HyperVDetail();

            var launchType = GetHypervisorLaunchType();
            var hyperVFeature = IsWindowsFeatureEnabled("Microsoft-Hyper-V-All");
            var vmPlatform = IsWindowsFeatureEnabled("VirtualMachinePlatform");

            detail.VirtualMachinePlatformEnabled = vmPlatform;
            detail.HyperVFeatureEnabled = hyperVFeature;

            if (launchType == "auto")
            {
                detail.HyperVState = HyperVState.Enabled;
                detail.BestMode = "WSL2";
                detail.Description = "Hyper-V 已开启";
                detail.DetailInfo = "✅ WSL2 可流畅运行\n⚠️ VMware/VirtualBox 可能无法正常使用";
                detail.NeedsReboot = false;
            }
            else if (launchType == "off")
            {
                detail.HyperVState = HyperVState.Disabled;
                detail.BestMode = "VM";
                detail.Description = "Hyper-V 已关闭";
                detail.DetailInfo = "✅ VMware/VirtualBox 可流畅运行\n⚠️ WSL2 不可用（WSL1 仍可用）";
                detail.NeedsReboot = false;
            }
            else
            {
                detail.HyperVState = HyperVState.Unknown;
                detail.Description = "未能检测到 Hyper-V 配置";
                detail.DetailInfo = "请确保以管理员身份运行此应用";
            }

            return detail;
        }

        public static async Task<(bool Success, string Message)> SetHyperVEnabledAsync(bool enable)
        {
            return await Task.Run(() =>
            {
                try
                {
                    var arg = enable ? "auto" : "off";
                    var psi = new ProcessStartInfo
                    {
                        FileName = "bcdedit.exe",
                        Arguments = $"/set hypervisorlaunchtype {arg}",
                        UseShellExecute = true,
                        CreateNoWindow = true,
                        Verb = "runas"
                    };

                    using var process = Process.Start(psi);
                    if (process == null)
                        return (false, "无法启动 bcdedit，请确保以管理员身份运行");

                    process.WaitForExit();

                    if (process.ExitCode == 0)
                    {
                        var target = enable ? "开启" : "关闭";
                        return (true, $"Hyper-V 已设置为{target}，需要重启电脑才能生效");
                    }

                    return (false, $"bcdedit 执行失败，退出代码: {process.ExitCode}");
                }
                catch (Exception ex)
                {
                    return (false, $"操作失败: {ex.Message}");
                }
            });
        }

        private static string GetHypervisorLaunchType()
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "bcdedit.exe",
                    Arguments = "/enum {current}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                if (process == null) return "";

                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                var match = Regex.Match(output, @"hypervisorlaunchtype\s+(\w+)", RegexOptions.IgnoreCase);
                if (match.Success)
                    return match.Groups[1].Value.ToLower();

                var match2 = Regex.Match(output, @"hypervisorlaunchtype", RegexOptions.IgnoreCase);
                if (match2.Success)
                    return "auto";

                return "";
            }
            catch
            {
                return "";
            }
        }

        private static bool IsWindowsFeatureEnabled(string featureName)
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = $"-Command \"(Get-WindowsOptionalFeature -Online -FeatureName {featureName}).State -eq 'Enabled'\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                if (process == null) return false;

                var output = process.StandardOutput.ReadToEnd().Trim();
                process.WaitForExit();

                return output.Equals("True", StringComparison.OrdinalIgnoreCase);
            }
            catch
            {
                return false;
            }
        }

        public static bool IsRunningAsAdmin()
        {
            using var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
            var principal = new System.Security.Principal.WindowsPrincipal(identity);
            return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
        }
    }
}
