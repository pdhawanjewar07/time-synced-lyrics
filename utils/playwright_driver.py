from playwright.sync_api import sync_playwright
from pathlib import Path
from typing import Optional, List
import logging
import shutil

log = logging.getLogger(__name__)

class PlaywrightDriver:
    def __init__(
        self,
        user_data_dir: str = "playwright_profile",
        headless: bool = True,
        args: Optional[List[str]] = None,
        timeout_ms: int = 30_000,
    ):
        self._playwright = sync_playwright().start()

        Path(user_data_dir).mkdir(parents=True, exist_ok=True)

        chromium_args = args or [
            "--disable-dev-shm-usage",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-extensions",
            "--disable-component-update",
            "--disable-features=TranslateUI",
        ]

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            args=chromium_args,
        )

        self.page = self._context.pages[0]
        self.page.set_default_timeout(timeout_ms)
        self.page.set_default_navigation_timeout(timeout_ms)
        log.info("==== Playwright Driver was started ====")

    def get(self, url: str):
        self.page.goto(url)

    def close(self):
        self._context.close()
        self._playwright.stop()
        log.info("==== Playwright Driver was closed ====")


def clear_profile_cache():
    PROFILE = Path("playwright_profile")
    SAFE_TO_DELETE = [
        "component_crx_cache",
        "Crashpad",
        "Default/Cache",
        "Default/Code Cache",
        "Default/DawnGraphiteCache",
        "Default/DawnWebGPUCache",
        "Default/GPUCache",
        "extensions_crx_cache",
        "GraphiteDawnCache",
        "GrShaderCache",
        "ShaderCache"
    ]
    for name in SAFE_TO_DELETE:
        path = PROFILE / name
        if path.exists():
            shutil.rmtree(path)
            # print(f"Deleted {path}")
    log.info("==== Playwright Profile Cache was safely cleared! ====")
    return True



