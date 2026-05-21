#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          PIXELPROTECH SOLUTIONS — DRIVE MANAGER             ║
║          IT Support · Computer Repairs · Gauteng            ║
║          076 645 9348 · pixelprotechsolutions@gmail.com     ║
╚══════════════════════════════════════════════════════════════╝

PixelProTech_DriveManager.py
Version: 1.0.0
Purpose: Detect, inspect, label, clean, format and eject
         removable drives (USB, SD cards, external HDDs)
Platform: Windows / Linux / macOS
"""

import os
import sys
import platform
import subprocess
import shutil
import time
import threading
from datetime import datetime

# ── Dependency bootstrap ────────────────────────────────────────
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import psutil
except ImportError:
    print("[PPT] Installing required dependency: psutil...")
    install("psutil")
    import psutil

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
except ImportError:
    print("[ERROR] tkinter not found. Install python3-tk and retry.")
    sys.exit(1)

# ── Constants ────────────────────────────────────────────────────
OS = platform.system()  # 'Windows', 'Linux', 'Darwin'

BRAND = "PIXELPROTECH SOLUTIONS"
VERSION = "v1.0.0"
CONTACT = "076 645 9348  |  pixelprotechsolutions@gmail.com"
LOCATION = "Johannesburg & Pretoria, Gauteng"

# Colours — PixelProTech brand (dark tech / purple-pixel aesthetic)
BG_MAIN    = "#0A0A0F"
BG_PANEL   = "#111118"
BG_CARD    = "#16161F"
ACCENT     = "#7B4FFF"   # purple pixel accent
ACCENT2    = "#00E5FF"   # cyan highlight
TEXT_PRI   = "#EEEEF5"
TEXT_SEC   = "#8888AA"
TEXT_DIM   = "#444460"
SUCCESS    = "#22DD88"
WARNING    = "#FFB020"
DANGER     = "#FF4455"
BORDER     = "#2A2A3A"

FONT_MONO  = ("Courier New", 10)
FONT_HEAD  = ("Courier New", 13, "bold")
FONT_SMALL = ("Courier New", 9)
FONT_LABEL = ("Courier New", 10)

# ── Utility helpers ──────────────────────────────────────────────

def fmt_size(bytes_val):
    """Format bytes to human-readable string."""
    if bytes_val is None:
        return "—"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def get_removable_drives():
    """Return list of dicts describing removable/external drives."""
    drives = []
    for part in psutil.disk_partitions(all=False):
        opts = part.opts.lower()
        # Heuristics for removable media across platforms
        is_removable = False
        if OS == "Windows":
            is_removable = "removable" in opts
        elif OS == "Linux":
            mp = part.mountpoint
            is_removable = (
                mp.startswith("/media/") or
                mp.startswith("/mnt/") or
                mp.startswith("/run/media/")
            )
        elif OS == "Darwin":
            is_removable = part.mountpoint.startswith("/Volumes/") and part.mountpoint != "/Volumes/Macintosh HD"

        if not is_removable:
            continue

        try:
            usage = psutil.disk_usage(part.mountpoint)
            total = usage.total
            used  = usage.used
            free  = usage.free
            pct   = usage.percent
        except PermissionError:
            total = used = free = pct = None

        drives.append({
            "device":     part.device,
            "mountpoint": part.mountpoint,
            "fstype":     part.fstype or "Unknown",
            "opts":       part.opts,
            "total":      total,
            "used":       used,
            "free":       free,
            "pct":        pct,
            "label":      _get_label(part.device, part.mountpoint),
        })
    return drives


def _get_label(device, mountpoint):
    """Best-effort drive label retrieval."""
    try:
        if OS == "Windows":
            import ctypes
            vol_name = ctypes.create_unicode_buffer(261)
            ctypes.windll.kernel32.GetVolumeInformationW(
                device + "\\", vol_name, 261, None, None, None, None, 0
            )
            return vol_name.value if vol_name.value else "NO LABEL"
        elif OS == "Linux":
            result = subprocess.run(
                ["lsblk", "-no", "LABEL", device],
                capture_output=True, text=True
            )
            label = result.stdout.strip()
            return label if label else "NO LABEL"
        elif OS == "Darwin":
            name = os.path.basename(mountpoint)
            return name if name else "NO LABEL"
    except Exception:
        pass
    return "NO LABEL"


def rename_drive(device, mountpoint, new_label):
    """Rename / relabel a drive."""
    new_label = new_label.strip().upper()[:11]  # FAT32 max 11 chars
    try:
        if OS == "Windows":
            subprocess.run(["label", device.replace("\\", ""), new_label], shell=True, check=True)
        elif OS == "Linux":
            fstype = _get_fstype(device)
            if "fat" in fstype.lower() or "vfat" in fstype.lower():
                subprocess.run(["sudo", "fatlabel", device, new_label], check=True)
            elif "ntfs" in fstype.lower():
                subprocess.run(["sudo", "ntfslabel", device, new_label], check=True)
            elif "exfat" in fstype.lower():
                subprocess.run(["sudo", "exfatlabel", device, new_label], check=True)
            else:
                return False, f"Unsupported filesystem: {fstype}"
        elif OS == "Darwin":
            subprocess.run(["diskutil", "rename", mountpoint, new_label], check=True)
        return True, f"Drive labelled: {new_label}"
    except subprocess.CalledProcessError as e:
        return False, str(e)


def _get_fstype(device):
    try:
        r = subprocess.run(["lsblk", "-no", "FSTYPE", device], capture_output=True, text=True)
        return r.stdout.strip()
    except Exception:
        return ""


def clean_drive(mountpoint):
    """Delete all files and folders on the drive (not format)."""
    deleted = 0
    errors  = []
    for item in os.listdir(mountpoint):
        item_path = os.path.join(mountpoint, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
                deleted += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                deleted += 1
        except Exception as e:
            errors.append(str(e))
    return deleted, errors


def format_drive(device, mountpoint, fstype="FAT32", label="PIXELTECH"):
    """Format a drive. Requires elevated privileges on Linux/macOS."""
    label = label.strip().upper()[:11]
    try:
        if OS == "Windows":
            cmd = f'format {device.replace(chr(92),"")} /FS:{fstype} /V:{label} /Q /Y'
            subprocess.run(cmd, shell=True, check=True)
        elif OS == "Linux":
            # Unmount first
            subprocess.run(["sudo", "umount", mountpoint], check=True)
            if fstype.upper() == "FAT32":
                subprocess.run(["sudo", "mkfs.vfat", "-F", "32", "-n", label, device], check=True)
            elif fstype.upper() == "NTFS":
                subprocess.run(["sudo", "mkfs.ntfs", "-Q", "-L", label, device], check=True)
            elif fstype.upper() == "EXFAT":
                subprocess.run(["sudo", "mkfs.exfat", "-n", label, device], check=True)
            # Remount
            subprocess.run(["sudo", "mount", device, mountpoint])
        elif OS == "Darwin":
            subprocess.run(["diskutil", "eraseDisk", fstype, label, device], check=True)
        return True, f"Formatted as {fstype} with label {label}"
    except subprocess.CalledProcessError as e:
        return False, str(e)


def eject_drive(device, mountpoint):
    """Safely eject a drive."""
    try:
        if OS == "Windows":
            # Use PowerShell to eject
            ps = f'(New-Object -comObject Shell.Application).Namespace(17).ParseName("{device}\\").InvokeVerb("Eject")'
            subprocess.run(["powershell", "-Command", ps], check=True)
        elif OS == "Linux":
            subprocess.run(["udisksctl", "unmount", "-b", device], check=True)
            subprocess.run(["udisksctl", "power-off", "-b", device])
        elif OS == "Darwin":
            subprocess.run(["diskutil", "eject", mountpoint], check=True)
        return True, "Drive ejected safely."
    except subprocess.CalledProcessError as e:
        return False, str(e)


# ── GUI Application ──────────────────────────────────────────────

class DriveManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"PixelProTech Drive Manager {VERSION}")
        self.geometry("820x640")
        self.minsize(780, 580)
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)

        self._drives = []
        self._selected_idx = None
        self._scan_running = False

        self._build_ui()
        self._scan_drives()
        self._auto_refresh()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_PANEL, pady=10)
        hdr.pack(fill="x")

        tk.Label(hdr, text="▮▮ PIXELPROTECH SOLUTIONS", font=("Courier New", 14, "bold"),
                 bg=BG_PANEL, fg=ACCENT).pack(side="left", padx=18)
        tk.Label(hdr, text=f"DRIVE MANAGER {VERSION}", font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SEC).pack(side="left", padx=4)
        tk.Label(hdr, text=f"[ {OS.upper()} ]", font=FONT_SMALL,
                 bg=BG_PANEL, fg=ACCENT2).pack(side="right", padx=18)

        # Status bar (below header)
        self._status_var = tk.StringVar(value=f"[{timestamp()}] System ready. Click SCAN to detect drives.")
        status_bar = tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                              bg=BG_CARD, fg=TEXT_SEC, anchor="w", padx=10, pady=4)
        status_bar.pack(fill="x")

        # Main body
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # Left — drive list
        left = tk.Frame(body, bg=BG_MAIN, width=260)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        tk.Label(left, text="// DETECTED DRIVES", font=FONT_SMALL,
                 bg=BG_MAIN, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))

        list_frame = tk.Frame(left, bg=BORDER, bd=1)
        list_frame.pack(fill="both", expand=True)

        self._listbox = tk.Listbox(
            list_frame,
            bg=BG_PANEL, fg=TEXT_PRI,
            selectbackground=ACCENT, selectforeground="#FFFFFF",
            font=FONT_MONO, bd=0, highlightthickness=0,
            activestyle="none", cursor="hand2"
        )
        self._listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        scan_btn = tk.Button(
            left, text="⟳  SCAN DRIVES", font=("Courier New", 10, "bold"),
            bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT2, activeforeground=BG_MAIN,
            bd=0, pady=8, cursor="hand2", command=self._scan_drives
        )
        scan_btn.pack(fill="x", pady=(6, 0))

        # Right — detail + actions
        right = tk.Frame(body, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        # Drive info card
        tk.Label(right, text="// DRIVE DETAILS", font=FONT_SMALL,
                 bg=BG_MAIN, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))

        info_frame = tk.Frame(right, bg=BG_CARD, bd=0, pady=14, padx=16)
        info_frame.pack(fill="x")

        self._info_vars = {}
        fields = [
            ("LABEL",       "label"),
            ("DEVICE",      "device"),
            ("MOUNT POINT", "mountpoint"),
            ("FILE SYSTEM", "fstype"),
            ("TOTAL SIZE",  "total_fmt"),
            ("USED",        "used_fmt"),
            ("FREE",        "free_fmt"),
            ("USAGE",       "pct_fmt"),
        ]
        for i, (display, key) in enumerate(fields):
            row = tk.Frame(info_frame, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{display}:", font=FONT_SMALL, width=13,
                     bg=BG_CARD, fg=TEXT_SEC, anchor="w").pack(side="left")
            var = tk.StringVar(value="—")
            self._info_vars[key] = var
            tk.Label(row, textvariable=var, font=FONT_MONO,
                     bg=BG_CARD, fg=TEXT_PRI, anchor="w").pack(side="left")

        # Usage bar
        self._bar_frame = tk.Frame(right, bg=BG_CARD, padx=16, pady=8)
        self._bar_frame.pack(fill="x")
        tk.Label(self._bar_frame, text="STORAGE USAGE", font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")
        self._canvas_bar = tk.Canvas(self._bar_frame, height=16, bg=BG_PANEL,
                                     highlightthickness=0)
        self._canvas_bar.pack(fill="x", pady=4)

        # Actions
        tk.Label(right, text="// ACTIONS", font=FONT_SMALL,
                 bg=BG_MAIN, fg=TEXT_DIM).pack(anchor="w", pady=(10, 4))

        actions_frame = tk.Frame(right, bg=BG_MAIN)
        actions_frame.pack(fill="x")

        btn_cfg = [
            ("[E]  RENAME LABEL",  self._action_rename,  ACCENT,   "#FFF"),
            ("[X]  CLEAN DRIVE",   self._action_clean,   WARNING,  BG_MAIN),
            ("[F]  FORMAT DRIVE",  self._action_format,  DANGER,   "#FFF"),
            ("[>]  EJECT SAFELY",  self._action_eject,   SUCCESS,  BG_MAIN),
        ]
        for i, (label, cmd, bg, fg) in enumerate(btn_cfg):
            btn = tk.Button(
                actions_frame, text=label, font=("Courier New", 10, "bold"),
                bg=bg, fg=fg, activebackground=ACCENT2, activeforeground=BG_MAIN,
                bd=0, pady=10, padx=8, cursor="hand2", command=cmd, width=18
            )
            btn.grid(row=i//2, column=i%2, padx=4, pady=4, sticky="ew")
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        # Log
        tk.Label(right, text="// OPERATION LOG", font=FONT_SMALL,
                 bg=BG_MAIN, fg=TEXT_DIM).pack(anchor="w", pady=(10, 4))

        log_frame = tk.Frame(right, bg=BORDER, bd=1)
        log_frame.pack(fill="both", expand=True)

        self._log = tk.Text(
            log_frame, bg=BG_PANEL, fg=ACCENT2, font=FONT_SMALL,
            bd=0, highlightthickness=0, state="disabled", wrap="word",
            padx=8, pady=6
        )
        self._log.pack(fill="both", expand=True, padx=1, pady=1)

        sb = ttk.Scrollbar(log_frame, command=self._log.yview)
        self._log.configure(yscrollcommand=sb.set)

        # Footer
        footer = tk.Frame(self, bg=BG_PANEL, pady=6)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text=f"{BRAND}  ·  {CONTACT}  ·  {LOCATION}",
                 font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM).pack()

    # ── Drive Scanning ───────────────────────────────────────────

    def _scan_drives(self):
        if self._scan_running:
            return
        self._scan_running = True
        self._set_status("Scanning for removable drives...")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        drives = get_removable_drives()
        self.after(0, lambda: self._populate_list(drives))

    def _populate_list(self, drives):
        self._drives = drives
        self._listbox.delete(0, "end")
        if not drives:
            self._listbox.insert("end", "  No drives found")
            self._set_status("No removable drives detected. Insert a drive and scan again.")
        else:
            for d in drives:
                label = d["label"] or "NO LABEL"
                size  = fmt_size(d["total"]) if d["total"] else "?"
                entry = f"  {label:<12} {size:>8}"
                self._listbox.insert("end", entry)
            self._set_status(f"[{timestamp()}] Found {len(drives)} removable drive(s).")
        self._scan_running = False

    # ── Selection ────────────────────────────────────────────────

    def _on_select(self, event):
        sel = self._listbox.curselection()
        if not sel or not self._drives:
            return
        idx = sel[0]
        if idx >= len(self._drives):
            return
        self._selected_idx = idx
        d = self._drives[idx]
        self._info_vars["label"].set(d["label"])
        self._info_vars["device"].set(d["device"])
        self._info_vars["mountpoint"].set(d["mountpoint"])
        self._info_vars["fstype"].set(d["fstype"])
        self._info_vars["total_fmt"].set(fmt_size(d["total"]))
        self._info_vars["used_fmt"].set(fmt_size(d["used"]))
        self._info_vars["free_fmt"].set(fmt_size(d["free"]))
        pct = d["pct"]
        self._info_vars["pct_fmt"].set(f"{pct:.1f}%" if pct is not None else "—")
        self._draw_bar(pct)
        self._log_msg(f"Selected: {d['label']} @ {d['mountpoint']}")

    def _draw_bar(self, pct):
        self._canvas_bar.update_idletasks()
        w = self._canvas_bar.winfo_width()
        self._canvas_bar.delete("all")
        self._canvas_bar.create_rectangle(0, 0, w, 16, fill=BG_PANEL, outline="")
        if pct is not None:
            fill_w = int(w * pct / 100)
            color = SUCCESS if pct < 70 else WARNING if pct < 90 else DANGER
            self._canvas_bar.create_rectangle(0, 0, fill_w, 16, fill=color, outline="")
        self._canvas_bar.create_text(w//2, 8, text=f"{pct:.0f}%" if pct else "—",
                                      fill=TEXT_PRI, font=FONT_SMALL)

    # ── Actions ──────────────────────────────────────────────────

    def _get_selected(self):
        if self._selected_idx is None or self._selected_idx >= len(self._drives):
            messagebox.showwarning("No Drive Selected", "Please select a drive from the list first.")
            return None
        return self._drives[self._selected_idx]

    def _action_rename(self):
        d = self._get_selected()
        if not d:
            return
        new_label = simpledialog.askstring(
            "Rename Drive",
            f"Enter new label for {d['device']}\n(max 11 characters, FAT32 limit):",
            initialvalue=d["label"]
        )
        if not new_label:
            return
        ok, msg = rename_drive(d["device"], d["mountpoint"], new_label)
        self._log_msg(f"RENAME: {msg}", ok)
        if ok:
            self._scan_drives()

    def _action_clean(self):
        d = self._get_selected()
        if not d:
            return
        confirm = messagebox.askyesno(
            "⚠ CLEAN DRIVE",
            f"Delete ALL files on {d['label']} ({d['mountpoint']})?\n\nThis cannot be undone.",
            icon="warning"
        )
        if not confirm:
            return
        self._set_status("Cleaning drive — please wait...")
        def do_clean():
            deleted, errors = clean_drive(d["mountpoint"])
            self.after(0, lambda: self._clean_done(deleted, errors))
        threading.Thread(target=do_clean, daemon=True).start()

    def _clean_done(self, deleted, errors):
        msg = f"CLEAN: Deleted {deleted} item(s)."
        if errors:
            msg += f" {len(errors)} error(s)."
        self._log_msg(msg, not errors)
        self._scan_drives()

    def _action_format(self):
        d = self._get_selected()
        if not d:
            return

        # Format options dialog
        dlg = tk.Toplevel(self)
        dlg.title("Format Drive")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("340x220")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="⚠ FORMAT DRIVE", font=FONT_HEAD,
                 bg=BG_PANEL, fg=DANGER).pack(pady=(16, 4))
        tk.Label(dlg, text=f"Device: {d['device']}\nAll data will be PERMANENTLY deleted.",
                 font=FONT_SMALL, bg=BG_PANEL, fg=WARNING, justify="center").pack()

        fs_var = tk.StringVar(value="FAT32")
        lbl_var = tk.StringVar(value="PIXELTECH")

        row1 = tk.Frame(dlg, bg=BG_PANEL)
        row1.pack(pady=6)
        tk.Label(row1, text="File System:", font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_SEC).pack(side="left", padx=6)
        fs_menu = ttk.Combobox(row1, textvariable=fs_var, values=["FAT32", "NTFS", "EXFAT"], width=10, state="readonly")
        fs_menu.pack(side="left")

        row2 = tk.Frame(dlg, bg=BG_PANEL)
        row2.pack(pady=4)
        tk.Label(row2, text="Label:", font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_SEC).pack(side="left", padx=6)
        tk.Entry(row2, textvariable=lbl_var, font=FONT_MONO, bg=BG_CARD, fg=TEXT_PRI,
                 insertbackground=TEXT_PRI, bd=0, width=14).pack(side="left")

        def do_format():
            dlg.destroy()
            self._set_status(f"Formatting {d['device']} as {fs_var.get()}...")
            def _fmt():
                ok, msg = format_drive(d["device"], d["mountpoint"], fs_var.get(), lbl_var.get())
                self.after(0, lambda: self._log_msg(f"FORMAT: {msg}", ok))
                self.after(500, self._scan_drives)
            threading.Thread(target=_fmt, daemon=True).start()

        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="CANCEL", font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC,
                  bd=0, padx=12, pady=6, command=dlg.destroy).pack(side="left", padx=6)
        tk.Button(btn_row, text="FORMAT", font=("Courier New", 10, "bold"), bg=DANGER, fg="#FFF",
                  bd=0, padx=12, pady=6, command=do_format).pack(side="left", padx=6)

    def _action_eject(self):
        d = self._get_selected()
        if not d:
            return
        ok, msg = eject_drive(d["device"], d["mountpoint"])
        self._log_msg(f"EJECT: {msg}", ok)
        if ok:
            self._scan_drives()

    # ── Helpers ──────────────────────────────────────────────────

    def _log_msg(self, msg, success=True):
        color = SUCCESS if success else DANGER
        self._log.configure(state="normal")
        self._log.insert("end", f"[{timestamp()}] ", "dim")
        self._log.insert("end", msg + "\n", "colored")
        self._log.tag_config("dim", foreground=TEXT_DIM)
        self._log.tag_config("colored", foreground=color)
        self._log.see("end")
        self._log.configure(state="disabled")
        self._set_status(f"[{timestamp()}] {msg}")

    def _set_status(self, msg):
        self._status_var.set(msg)

    def _auto_refresh(self):
        """Auto-refresh drive list every 8 seconds."""
        self._scan_drives()
        self.after(8000, self._auto_refresh)


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║       PIXELPROTECH SOLUTIONS — DRIVE MANAGER        ║
║       {VERSION}  ·  {OS.upper():<8}                         ║
║       {CONTACT}       ║
╚══════════════════════════════════════════════════════╝
Starting UI...
""")
    app = DriveManagerApp()
    app.mainloop()
