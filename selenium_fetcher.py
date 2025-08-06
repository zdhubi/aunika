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

    # 🧲 Opakované klikání na tlačítko „Načíst vše“
try:
    wait = WebDriverWait(driver, 15)
    while True:
        try:
            load_all_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Načíst vše')]")))
            driver.execute_script("arguments[0].scrollIntoView();", load_all_button)
            time.sleep(1)
            load_all_button.click()
            print("[INFO] Kliknuto na 'Načíst vše'")
            time.sleep(3)
        except:
            print("[INFO] Žádné další tlačítko 'Načíst vše'")
            break
except Exception as e:
    print(f"[WARNING] Chyba při pokusu o načtení všech produktů: {e}")



    # 🕵️‍♂️ Načtení odkazů
    links = []
    elements = driver.find_elements(By.CSS_SELECTOR, "a.item_link, div.item a[href*='/']")
    for el in elements:
        href = el.get_attribute("href")
        if href and not href.endswith("#") and "ajaxPage" not in href:
            links.append(href)

    driver.quit()
    return list(set(links))
