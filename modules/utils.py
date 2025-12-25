# modules/utils.py
import threading

def call_on_main_thread(func, *args, **kwargs):
    """
    確保函式在主執行緒執行。
    Playwright 或 Tkinter 等需要在主執行緒執行的程式碼，
    可以透過這個工具避免在子執行緒出錯。
    """
    if threading.current_thread() is threading.main_thread():
        return func(*args, **kwargs)
    else:
        print("⚠️ call_on_main_thread skipped: not on main thread")
        return None