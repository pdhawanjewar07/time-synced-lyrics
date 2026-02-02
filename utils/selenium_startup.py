import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from config import CHROME_BINARY, DRIVER_PATH

log = logging.getLogger(__name__)

_driver = None

def get_driver():
    global _driver

    if _driver is None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = CHROME_BINARY
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        service = Service(executable_path=DRIVER_PATH)
        _driver = webdriver.Chrome(service=service, options=chrome_options)

        log.info("==== Selenium Chrome driver started ====")

    return _driver