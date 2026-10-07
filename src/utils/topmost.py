from src.platform import force_topmost as platform_force_topmost

def force_topmost(widget) -> None:
    """
    跨平台視窗置頂宣告。委派至作業系統專屬之平台轉接層處理。
    """
    platform_force_topmost(widget)
