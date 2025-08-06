from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_product_links_selenium(category_url, timeout=30):
    options = Options()
    options.binary_location = "/usr/bin/chromium"
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

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(timeout)
    driver.get(category_url)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


    # 🍪 Cookies
    try:
        cookie_button = driver.find_element(By.CSS_SELECTOR, ".cookie-accept-button")
        driver.execute_script("arguments[0].click();", cookie_button)
        time.sleep(1)
        driver.execute_script("document.querySelector('#cookie-bar')?.remove();")
    except Exception:
        pass

    # 🔄 Scroll dolů opakovaně pro vykreslení tlačítka
    found_button = False
    for i in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        try:
            candidates = driver.find_elements(By.XPATH, "//*[contains(text(), 'Načíst vše')]")
            for el in candidates:
                if el.is_displayed() and el.tag_name.lower() in ['button', 'div', 'span']:
                    driver.execute_script("arguments[0].scrollIntoView();", el)
                    driver.execute_script("arguments[0].click();", el)
                    print("[INFO] Tlačítko 'Načíst vše' úspěšně kliknuto.")
                    # ⏳ Čekání na načtení produktů
                    WebDriverWait(driver, 20).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "a.item_link, div.item a[href*='/']")) > 10
                    )
                    found_button = True
                    break
            if found_button:
                break
        except Exception:
            continue

    if not found_button:
        print("[WARNING] Tlačítko 'Načíst vše' nebylo nalezeno ani po scrollování.")

    # 🕵️‍♂️ Načtení odkazů
    links = []
    elements = driver.find_elements(By.CSS_SELECTOR, "a.item_link, div.item a[href*='/']")
    for el in elements:
        href = el.get_attribute("href")
        if href and not href.endswith("#") and "ajaxPage" not in href:
            links.append(href)

    driver.quit()
    return list(set(links))
