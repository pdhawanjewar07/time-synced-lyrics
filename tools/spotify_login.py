from utils.playwright_driver import PlaywrightDriver



driver = PlaywrightDriver(headless=False)
driver.page.goto("https://accounts.spotify.com")

input("Log in manually, then press Enter...")
driver.close()

# Necessary for - better song matching