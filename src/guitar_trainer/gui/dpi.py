from __future__ import annotations

import os
import sys


def configure_windows_dpi_awareness() -> None:
    """Best-effort DPI awareness for Windows to avoid broken Tk scaling.

    Call this BEFORE creating Tk().
    Safe no-op on non-Windows.
    """
    if sys.platform != "win32":
        return

    if os.environ.get("GUITAR_TRAINER_DISABLE_DPI_FIX", "").strip() == "1":
        return

    try:
        import ctypes  # stdlib
    except Exception:
        return

    # Prefer the newest API (Windows 10+), then fall back.
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2 (Windows 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        # System DPI aware (Vista+)
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def apply_tk_scaling(root) -> None:
    """Apply Tk scaling based on actual DPI.

    Call this AFTER creating Tk(), but BEFORE building widgets.
    Safe no-op on non-Windows.
    """
    if sys.platform != "win32":
        return

    if os.environ.get("GUITAR_TRAINER_DISABLE_DPI_FIX", "").strip() == "1":
        return

    try:
        # pixels per inch
        dpi = float(root.winfo_fpixels("1i"))

        # Tk uses 72 points per inch baseline
        scaling = dpi / 72.0

        # Clamp to prevent extreme values on unusual setups
        scaling = max(1.0, min(2.5, scaling))

        root.tk.call("tk", "scaling", scaling)
    except Exception:
        # Keep Tk defaults if anything goes wrong
        return
