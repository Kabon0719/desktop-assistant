import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_uint
    ]
    _user32.SetWindowPos.restype = wintypes.BOOL

    _HWND_TOPMOST = wintypes.HWND(-1)
    _SWP_NOSIZE = 0x0001
    _SWP_NOMOVE = 0x0002
    _SWP_NOACTIVATE = 0x0010
    _SWP_NOOWNERZORDER = 0x0200
    _FLAGS = _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOACTIVATE | _SWP_NOOWNERZORDER


def force_topmost(widget) -> None:
    """
    透過 Win32 SetWindowPos(HWND_TOPMOST) 重新把視窗拉回最上層。
    不移動、不改尺寸、不搶焦點；非 Windows 平台或視窗不可見時不做任何事。
    """
    if sys.platform != "win32" or widget is None or not widget.isVisible():
        return
    try:
        hwnd = int(widget.winId())
        if hwnd:
            _user32.SetWindowPos(hwnd, _HWND_TOPMOST, 0, 0, 0, 0, _FLAGS)
    except Exception as e:
        print(f"[TopMost] SetWindowPos failed: {e}")
