import subprocess
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import os
import threading
from threading import Thread
import traceback

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

COLORS = {
    "bg":          "#F0F2F5",
    "card":        "#FFFFFF",
    "text_dark":   "#1A1A2E",
    "text_gray":   "#666666",
    "text_light":  "#555555",
    "enabled":     "#4CAF50",
    "disabled":    "#FF9800",
    "wsl_grad1":   "#009688",
    "wsl_grad2":   "#00786B",
    "vm_grad1":    "#FF7042",
    "vm_grad2":    "#E65100",
    "unknown":     "#78909C",
    "reboot_bg":   "#FFF3E0",
    "reboot_text": "#E65100",
    "reboot_sub":  "#BF360C",
    "white":       "#FFFFFF",
    "btn_blue":    "#42A5F5",
    "btn_blue_h":  "#1E88E5",
    "btn_orange":  "#FF9800",
    "btn_orange_h":"#E68900",
    "btn_gray":    "#999999",
    "restart_btn": "#4CAF50",
    "restart_h":   "#388E3C",
}


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_cmd(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1


def get_hypervisor_launch_type():
    stdout, stderr, code = run_cmd('bcdedit /enum {current}')
    if code != 0:
        return ""
    for line in stdout.splitlines():
        line_lower = line.lower()
        if "hypervisorlaunchtype" in line_lower:
            parts = line.strip().split()
            if len(parts) >= 2:
                return parts[-1].lower()
            return "auto"
    return ""


def set_hypervisor_launch_type(enable: bool):
    val = "auto" if enable else "off"
    stdout, stderr, code = run_cmd(f'bcdedit /set hypervisorlaunchtype {val}')
    return code == 0, stderr if stderr else stdout


class HyperVSwitchApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hyper-V 切换助手")
        self.root.geometry("520x460")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])
        self._center_window()

        self.reboot_pending = False
        self.current_state = None

        self._build_ui()
        self._refresh_status()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 520, 460
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # ── Title Card ──
        self.card_top = tk.Frame(outer, bg=COLORS["card"], highlightthickness=0)
        self.card_top.pack(fill=tk.X, pady=(0, 10))

        tk.Frame(self.card_top, bg=COLORS["card"], height=14).pack()

        top_row = tk.Frame(self.card_top, bg=COLORS["card"])
        top_row.pack(fill=tk.X, padx=16)

        self.status_dot = tk.Canvas(top_row, width=40, height=40,
                                    bg=COLORS["card"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 12))
        self._dot_id = self.status_dot.create_oval(4, 4, 36, 36, fill=COLORS["unknown"], outline="")

        title_col = tk.Frame(top_row, bg=COLORS["card"])
        title_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_title = tk.Label(title_col, text="检测中...", font=("Microsoft YaHei UI", 18, "bold"),
                                   fg=COLORS["text_dark"], bg=COLORS["card"], anchor="w")
        self.lbl_title.pack(fill=tk.X)
        self.lbl_desc = tk.Label(title_col, text="", font=("Microsoft YaHei UI", 11),
                                  fg=COLORS["text_gray"], bg=COLORS["card"], anchor="w")
        self.lbl_desc.pack(fill=tk.X)

        tk.Frame(self.card_top, bg=COLORS["card"], height=14).pack()

        # ── Detail Card ──
        self.card_mid = tk.Frame(outer, bg=COLORS["card"], highlightthickness=0)
        self.card_mid.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Frame(self.card_mid, bg=COLORS["card"], height=14).pack()

        # Mode badge (gradient canvas)
        self.mode_frame = tk.Frame(self.card_mid, bg=COLORS["card"])
        self.mode_frame.pack(fill=tk.X, padx=16)
        self.mode_canvas = tk.Canvas(self.mode_frame, height=86,
                                      bg=COLORS["card"], highlightthickness=0)
        self.mode_canvas.pack(fill=tk.X)

        tk.Frame(self.card_mid, bg=COLORS["card"], height=14).pack()

        # Detail text
        detail_header = tk.Frame(self.card_mid, bg=COLORS["card"])
        detail_header.pack(fill=tk.X, padx=16)
        tk.Label(detail_header, text="兼容性状态", font=("Microsoft YaHei UI", 12, "bold"),
                 fg="#333333", bg=COLORS["card"]).pack(anchor="w")

        self.lbl_detail = tk.Label(self.card_mid, text="",
                                    font=("Microsoft YaHei UI", 11),
                                    fg=COLORS["text_light"], bg=COLORS["card"],
                                    justify="left", anchor="w", wraplength=460)
        self.lbl_detail.pack(fill=tk.BOTH, padx=20, pady=(2, 14))

        # ── Bottom Card ──
        self.card_bot = tk.Frame(outer, bg=COLORS["card"], highlightthickness=0)
        self.card_bot.pack(fill=tk.X)

        tk.Frame(self.card_bot, bg=COLORS["card"], height=14).pack()

        # Reboot banner (hidden initially)
        self.reboot_banner = tk.Frame(self.card_bot, bg=COLORS["reboot_bg"])
        self.reboot_banner_inner = tk.Frame(self.reboot_banner, bg=COLORS["reboot_bg"])
        self.reboot_banner_inner.pack(fill=tk.X, padx=12, pady=10)

        warn_frame = tk.Frame(self.reboot_banner_inner, bg=COLORS["reboot_bg"])
        warn_frame.pack(side=tk.LEFT, anchor="n", padx=(0, 6))
        self.lbl_warn_icon = tk.Label(warn_frame, text="⚠️", font=("Microsoft YaHei UI", 14),
                                       fg=COLORS["reboot_text"], bg=COLORS["reboot_bg"])
        self.lbl_warn_icon.pack()

        warn_text = tk.Frame(self.reboot_banner_inner, bg=COLORS["reboot_bg"])
        warn_text.pack(side=tk.LEFT)
        tk.Label(warn_text, text="需要重启电脑才能生效",
                 font=("Microsoft YaHei UI", 12, "bold"),
                 fg=COLORS["reboot_text"], bg=COLORS["reboot_bg"]).pack(anchor="w")
        tk.Label(warn_text, text="已成功更改 Hyper-V 配置，重启后新设置将生效",
                 font=("Microsoft YaHei UI", 10),
                 fg=COLORS["reboot_sub"], bg=COLORS["reboot_bg"]).pack(anchor="w")

        # Buttons
        self.btn_frame = tk.Frame(self.card_bot, bg=COLORS["card"])
        self.btn_frame.pack(fill=tk.X, padx=16, pady=(10, 14))

        self.btn_toggle = tk.Button(self.btn_frame, text="切换", font=("Microsoft YaHei UI", 13, "bold"),
                                     fg=COLORS["white"], borderwidth=0, cursor="hand2",
                                     activeforeground=COLORS["white"],
                                     command=self._on_toggle)
        self.btn_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        self.btn_restart = tk.Button(self.btn_frame, text="🔄 立即重启",
                                      font=("Microsoft YaHei UI", 13, "bold"),
                                      fg=COLORS["white"], bg=COLORS["restart_btn"],
                                      activebackground=COLORS["restart_h"],
                                      activeforeground=COLORS["white"],
                                      borderwidth=0, cursor="hand2",
                                      command=self._on_restart)
        tk.Frame(self.btn_frame, width=10, bg=COLORS["card"]).pack(side=tk.LEFT)
        self.btn_restart.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        self.btn_restart.pack_forget()

        # Admin warning
        self.admin_warn = tk.Label(self.card_bot, text="⚠️ 需要以管理员身份运行才能切换 Hyper-V",
                                    font=("Microsoft YaHei UI", 10),
                                    fg="#E65100", bg=COLORS["card"])
        self.admin_warn.pack(pady=(0, 14))

    def _draw_mode_badge(self, text, emoji, grad1, grad2):
        self.mode_canvas.delete("all")
        w = self.mode_canvas.winfo_width()
        h = 86
        if w < 10:
            w = 470

        for i in range(w):
            t = i / max(w - 1, 1)
            r = int(grad1[0] + (grad2[0] - grad1[0]) * t)
            g = int(grad1[1] + (grad2[1] - grad1[1]) * t)
            b = int(grad1[2] + (grad2[2] - grad1[2]) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.mode_canvas.create_line(i, 0, i, h, fill=color, width=1)

        self.mode_canvas.create_rectangle(8, 0, w - 8, h, outline="",
                                           fill="", stipple="") 

        self.mode_canvas.create_text(24, 20, text="当前模式", anchor="nw",
                                      font=("Microsoft YaHei UI", 10),
                                      fill="#FFFFFF")
        self.mode_canvas.create_text(24, 38, text=text, anchor="nw",
                                      font=("Microsoft YaHei UI", 24, "bold"),
                                      fill=COLORS["white"])
        self.mode_canvas.create_text(w - 20, h // 2, text=emoji, anchor="e",
                                      font=("Microsoft YaHei UI", 42),
                                      fill=COLORS["white"])

    def _refresh_status(self):
        Thread(target=self._do_refresh).start()

    def _do_refresh(self):
        try:
            launch_type = get_hypervisor_launch_type()
            self.current_state = launch_type
        except Exception:
            launch_type = ""
        self.root.after(0, self._update_ui, launch_type)

    def _update_ui(self, launch_type):
        is_adm = is_admin()
        self.admin_warn.pack_forget() if is_adm else self.admin_warn.pack(pady=(0, 14))

        if not is_adm:
            self.lbl_title.config(text="需要管理员权限")
            self.lbl_desc.config(text="请以管理员身份重新运行此应用")
            self._set_dot_color(COLORS["unknown"])
            self._draw_mode_badge("未知", "❓", self._hex_to_rgb(COLORS["unknown"]),
                                  self._hex_to_rgb("#546E7A"))
            self.lbl_detail.config(text="请右键 → 以管理员身份运行")
            self.btn_toggle.config(text="请以管理员身份重新运行",
                                    bg=COLORS["btn_gray"],
                                    activebackground="#757575")
            self.btn_toggle.config(state="disabled")
            return

        if launch_type == "auto":
            # Hyper-V ENABLED
            self._set_dot_color(COLORS["enabled"])
            self.lbl_title.config(text="Hyper-V 虚拟化已开启")
            self.lbl_desc.config(text="适合运行 WSL2、Docker、Android 模拟器")
            self._draw_mode_badge("WSL 模式", "🐧",
                                  self._hex_to_rgb(COLORS["wsl_grad1"]),
                                  self._hex_to_rgb(COLORS["wsl_grad2"]))
            self.lbl_detail.config(text="✅ WSL2 可流畅运行\n✅ Docker Desktop 可用\n⚠️ VMware / VirtualBox 可能无法正常使用")
            self.btn_toggle.config(text="🔧 切换到 VM 模式 (关闭 Hyper-V)",
                                    bg=COLORS["btn_orange"],
                                    activebackground=COLORS["btn_orange_h"])
            self.btn_toggle.config(state="normal")
        elif launch_type == "off":
            # Hyper-V DISABLED
            self._set_dot_color(COLORS["disabled"])
            self.lbl_title.config(text="Hyper-V 虚拟化已关闭")
            self.lbl_desc.config(text="适合运行 VMware、VirtualBox 等虚拟机")
            self._draw_mode_badge("VM 模式", "💻",
                                  self._hex_to_rgb(COLORS["vm_grad1"]),
                                  self._hex_to_rgb(COLORS["vm_grad2"]))
            self.lbl_detail.config(text="✅ VMware / VirtualBox 可流畅运行\n✅ 其他第三方虚拟机正常工作\n⚠️ WSL2 不可用 (WSL1 仍可用)")
            self.btn_toggle.config(text="🔧 切换到 WSL 模式 (开启 Hyper-V)",
                                    bg=COLORS["btn_blue"],
                                    activebackground=COLORS["btn_blue_h"])
            self.btn_toggle.config(state="normal")
        else:
            self._set_dot_color(COLORS["unknown"])
            self.lbl_title.config(text="未能检测到 Hyper-V 配置")
            self.lbl_desc.config(text="请确保以管理员身份运行此应用")
            self._draw_mode_badge("未知", "❓", self._hex_to_rgb(COLORS["unknown"]),
                                  self._hex_to_rgb("#546E7A"))
            self.lbl_detail.config(text="无法读取 bcdedit 配置\n请以管理员身份运行")
            self.btn_toggle.config(text="请以管理员身份重新运行",
                                    bg=COLORS["btn_gray"],
                                    activebackground="#757575")
            self.btn_toggle.config(state="disabled")

    def _on_toggle(self):
        if self.current_state == "auto":
            target = False
            msg = ("确定要关闭 Hyper-V 吗？\n\n"
                   "关闭后：\n"
                   "✅ VMware / VirtualBox 可以流畅运行\n"
                   "⚠️ WSL2 将不可用（WSL1 仍可使用）\n"
                   "⚠️ 需要重启电脑")
        elif self.current_state == "off":
            target = True
            msg = ("确定要开启 Hyper-V 吗？\n\n"
                   "开启后：\n"
                   "✅ WSL2 可以流畅运行\n"
                   "⚠️ VMware / VirtualBox 可能无法正常使用\n"
                   "⚠️ 需要重启电脑")
        else:
            messagebox.showwarning("检测失败", "无法检测到当前 Hyper-V 状态，请以管理员身份运行此应用。")
            return

        if not messagebox.askyesno("确认切换", msg):
            return

        self.btn_toggle.config(state="disabled", text="正在执行...")

        Thread(target=self._do_toggle, args=(target,)).start()

    def _do_toggle(self, enable):
        success, msg = set_hypervisor_launch_type(enable)
        self.root.after(0, self._on_toggle_done, success, enable, msg)

    def _on_toggle_done(self, success, enable, msg):
        if not success:
            messagebox.showerror("操作失败", f"操作失败：{msg}")
            self.btn_toggle.config(state="normal")
            self._refresh_status()
            return

        self.reboot_pending = True

        if enable:
            self._set_dot_color("#66BB6A")
            self.lbl_title.config(text="Hyper-V 将开启（待重启）")
            self.lbl_desc.config(text="重启后 WSL2 将可正常使用")
            self._draw_mode_badge("WSL 模式 (待重启)", "🐧⏳",
                                  self._hex_to_rgb(COLORS["wsl_grad1"]),
                                  self._hex_to_rgb(COLORS["wsl_grad2"]))
            self.lbl_detail.config(text="✅ 已设置开启 Hyper-V\n⏳ 请重启电脑以完成切换\n重启后 WSL2 即可正常使用")
        else:
            self._set_dot_color("#FFA726")
            self.lbl_title.config(text="Hyper-V 将关闭（待重启）")
            self.lbl_desc.config(text="重启后 VMware/VirtualBox 将可正常使用")
            self._draw_mode_badge("VM 模式 (待重启)", "💻⏳",
                                  self._hex_to_rgb(COLORS["vm_grad1"]),
                                  self._hex_to_rgb(COLORS["vm_grad2"]))
            self.lbl_detail.config(text="✅ 已设置关闭 Hyper-V\n⏳ 请重启电脑以完成切换\n重启后 VMware/VirtualBox 即可正常使用")

        self.btn_toggle.config(text="✅ 已设置，等待重启",
                                bg=COLORS["btn_gray"],
                                activebackground="#757575",
                                state="disabled")

        self.reboot_banner.pack(before=self.btn_frame, fill=tk.X,
                                 padx=16, pady=(14, 4))

        self.btn_restart.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        tk.Frame(self.btn_frame, width=10, bg=COLORS["card"]).pack(
            side=tk.LEFT, after=self.btn_restart)
        self.btn_restart.lift()

        self.root.geometry("520x520")

    def _on_restart(self):
        if messagebox.askyesno("确认重启", "确定要立即重启电脑吗？\n\n请确保已保存所有工作。",
                               icon="warning"):
            os.system("shutdown /r /t 10 /c \"Hyper-V 切换助手将在 10 秒后重启电脑\"")

    def _set_dot_color(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(6, 6, 34, 34, fill=color, outline="")

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def run(self):
        self.root.mainloop()


def main():
    try:
        if not is_admin():
            script = os.path.abspath(sys.argv[0])
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                f'"{script}" {params}', None, 1
            )
            sys.exit(0)

        app = HyperVSwitchApp()
        app.run()
    except Exception:
        err = traceback.format_exc()
        try:
            messagebox.showerror("程序异常", f"发生错误：\n\n{err}")
        except Exception:
            import tempfile
            log_path = os.path.join(tempfile.gettempdir(), "hyperv_switch_error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err)
            os.system(f'start notepad "{log_path}"')


if __name__ == "__main__":
    main()
