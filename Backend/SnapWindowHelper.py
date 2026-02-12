import subprocess
import time
import win32gui
import win32con
import win32process
import win32api

def snap_hwnd(hwnd, side='right'):
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)

    x = 0 if side == 'left' else screen_w // 2

    # 🔥 FORCE FOREGROUND
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_NOTOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )

    time.sleep(0.05)

    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x, 0,
        screen_w // 2,
        screen_h,
        win32con.SWP_SHOWWINDOW
    )

def find_any_visible_window(title_hint=None, timeout=6):
    """
    Find any visible window, with optional title hint.
    More flexible matching for user-installed apps.
    """
    end = time.time() + timeout
    while time.time() < end:
        def enum(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return
                
                # If no hint, accept any window with a title
                if title_hint is None:
                    result.append(hwnd)
                    return
                
                # Flexible matching - check if any word from hint is in title
                title_lower = title.lower()
                hint_lower = title_hint.lower()
                
                # Direct substring match
                if hint_lower in title_lower:
                    result.append(hwnd)
                    return
                
                # Word-by-word matching
                hint_words = set(hint_lower.split())
                title_words = set(title_lower.split())
                if hint_words & title_words:  # If any word matches
                    result.append(hwnd)
                    return

        result = []
        win32gui.EnumWindows(enum, result)
        if result:
            # Return the first match (usually most recently opened)
            return result[0]
        time.sleep(0.2)
    return None

def _find_window_by_pid(pid, timeout=5):
    """Wait until a visible window appears for the given PID"""
    end_time = time.time() + timeout
    hwnd_found = None

    def enum_handler(hwnd, _):
        nonlocal hwnd_found
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnd_found = hwnd

    while time.time() < end_time:
        win32gui.EnumWindows(enum_handler, None)
        if hwnd_found:
            return hwnd_found
        time.sleep(0.1)

    return None

def open_and_snap(command, snap="right", gui_hwnd=None, title_hint=None):
    """
    Open an app and snap it to the specified side.
    🆕 Returns the hwnd of the snapped window (or None if failed)
    Improved detection for user-installed apps.
    """
    proc = subprocess.Popen(command, shell=True)
    pid = proc.pid

    # Try to find by PID first
    hwnd = _find_window_by_pid(pid, timeout=3)

    # If not found by PID, try by title hint
    if not hwnd and title_hint:
        print(f"Searching by title hint: {title_hint}")
        hwnd = find_any_visible_window(title_hint, timeout=4)

    # Last resort - find ANY new visible window
    if not hwnd:
        print("Searching for any new window...")
        hwnd = find_any_visible_window(None, timeout=2)

    if not hwnd:
        print("❌ Could not find window to snap")
        return None

    # Found window - snap it
    try:
        window_title = win32gui.GetWindowText(hwnd)
        print(f"✅ Found window: {window_title}")
        snap_hwnd(hwnd, snap)
        
        if gui_hwnd:
            snap_hwnd(gui_hwnd, "left")
        
        return hwnd
    except Exception as e:
        print(f"Error snapping window: {e}")
        return None