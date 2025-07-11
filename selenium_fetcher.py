from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_product_links_selenium(category_url, timeout=30):
    options = Options()
    options.binary_location = "/usr/bin/chromium"  # 👈 přímá cesta k Chromium
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36")

    # 💡 Nepoužíváme webdriver_manager – místo toho explicitní cesta k Chromedriveru
    service = Service(executable_path="/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, timeout)

    driver.get(category_url)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        consent_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cookie-accept-button")))
        driver.execute_script("arguments[0].click();", consent_button)
        time.sleep(1)
        driver.execute_script("document.querySelector('#cookie-bar')?.remove();")
        print("[INFO] Cookies tlačítko odstraněno.")
    except Exception:
        print("[INFO] Cookies tlačítko se neobjevilo — pokračujeme.")

    try:
        while True:
            load_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-loadMore")))
            driver.execute_script("arguments[0].scrollIntoView();", load_button)
            driver.execute_script("arguments[0].click();", load_button)
            time.sleep(2)
    except Exception:
        print("[INFO] Tlačítko 'Načíst vše' není dostupné nebo vše již načteno.")

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    links = []
    elements = driver.find_elements(By.CSS_SELECTOR, "a.item_link, div.item a[href*='/']")
    for el in elements:
        href = el.get_attribute("href")
        if href and not href.endswith("#") and "ajaxPage" not in href:
            links.append(href)

    if not links:
        print("[WARNING] Žádné produkty nalezeny na této stránce.")

    # with open("debug_last_page.html", "w", encoding="utf-8") as f:
    #     f.write(driver.page_source)

    driver.quit()
    return list(set(links))
