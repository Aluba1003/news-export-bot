# modules/browser_manager.py
from playwright.sync_api import sync_playwright, Error as PlaywrightError
import threading

class BrowserManager:
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._owner_thread = threading.current_thread()  # 記錄建立者 thread
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self._closed = False
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = BrowserManager()
        return cls._instance

    def new_page(self):
        # 僅允許在建立者 thread 建立/操作 Playwright
        if threading.current_thread() is not self._owner_thread:
            raise RuntimeError("BrowserManager.new_page() called from non-owner thread")
        return self.context.new_page()

    def close(self):
        with self._lock:
            if self._closed:
                return  # 已關閉過，避免重複關閉

            if threading.current_thread() is not self._owner_thread:
                raise RuntimeError("BrowserManager.close() called from non-owner thread")

            try:
                if self.context:
                    self.context.close()
                    self.context = None
                if self.browser:
                    self.browser.close()
                    self.browser = None
                if self.playwright:
                    self.playwright.stop()
                    self.playwright = None
                print("BrowserManager closed successfully")
            except PlaywrightError as e:
                print(f"Playwright error during close: {e}")
            except Exception as e:
                print(f"BrowserManager close failed: {e}")
            finally:
                self._closed = True
                BrowserManager._instance = None
