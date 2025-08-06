import re
import csv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.dom.minidom import Document
from selenium_fetcher import get_product_links_selenium
from concurrent.futures import ThreadPoolExecutor, as_completed
from ftplib import FTP
from datetime import datetime

# 🧱 Bezpečný výpis do konzole
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='ignore').decode())

# 📁 Bezpečný logovací soubor
log_path = "C:/Temp/cron_log.txt"
try:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log = open(log_path, "a", encoding="utf-8")
    log.write(f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S,%f')[:-3]}] Spouštím aunika.py \n")
except Exception as e:
    safe_print(f"[WARNING] Nelze otevřít logovací soubor: {e}")
    log = None

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_obrazky(soup, base_url):
    obrazky = set()
    for a in soup.find_all("a", rel="fancyboxGallery"):
        href = a.get("href")
        if href and href.startswith("http"):
            obrazky.add(href)
    item_img = soup.find("div", class_="itemImg")
    if item_img:
        for a in item_img.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                obrazky.add(urljoin(base_url, href))
    return list(obrazky)

def get_long_description(soup):
    html_parts = []
    for section_id in ['popis', 'funkce', 'technical']:
        section = soup.find('div', id=section_id)
        if section:
            h2 = section.find('h2')
            if h2:
                h2.decompose()
            html_parts.append(str(section.encode_contents().decode('utf-8')).strip())
    return '\n'.join(html_parts).strip()

def get_dostupnost(soup):
    div = soup.find('div', class_='positiveColor')
    text = div.get_text(strip=True).lower() if div else ''
    if 'skladem' in text:
        return '2'
    elif any(word in text for word in ['není', 'nedostupné', 'na dotaz']):
        return '0'
    elif text:
        return '1'
    return ''

def parse_product_page(url):
    try:
        if "#ajaxPage" in url or url.endswith("#"):
            return None

        r = requests.get(url, headers=HEADERS, timeout=10)
        if 'text/html' not in r.headers.get('Content-Type', ''):
            return None
        soup = BeautifulSoup(r.content, 'html.parser')
        full_text = soup.get_text(separator="\n")

        h1 = soup.find('h1')
        name = h1.get_text(strip=True) if h1 else ''
        if not name:
            safe_print(f"[WARNING] Produkt bez <h1>: {url}")
            if log:
                log.write(f"[WARNING] Produkt bez názvu: {url}\n")

        code_match = re.search(r"(Objednací číslo|Obj\. č\.):\s*(.+)", full_text, re.IGNORECASE)
        code = code_match.group(2).strip() if code_match else ''
        if not code:
            safe_print(f"[WARNING] Produkt bez kódu: {url}")
            if log:
                log.write(f"[WARNING] Produkt bez kódu: {url}\n")

        cena_match = re.search(r"(Cena bez DPH|MO cena bez DPH|MO cena s DPH):\s*([\d\s.,]+ Kč)", full_text, re.IGNORECASE)
        cena_raw = cena_match.group(2).strip() if cena_match else ''
        if not cena_raw:
            safe_print(f"[WARNING] Produkt bez ceny: {url}")
            if log:
                log.write(f"[WARNING] Produkt bez ceny: {url}\n")

        cena_num = ''
        if cena_raw:
            cena_num = cena_raw.replace('Kč', '').replace('\xa0', '').replace(',', '.').replace(' ', '')

        kratky = (soup.find('meta', attrs={'name': 'description'}) or {}).get('content', '')
        dlouhy = get_long_description(soup)
        dostupnost = get_dostupnost(soup)
        obrazky = get_obrazky(soup, url)

        vyr_match = re.search(r"Výrobce:\s*(.+)", full_text, re.IGNORECASE)
        vyrobce = vyr_match.group(1).strip() if vyr_match else ''

        return {
            'url': url,
            'nazev': name,
            'objednaci_cislo': code,
            'cena_bez_dph': cena_raw,
            'cena_num': cena_num,
            'vyrobce': vyrobce,
            'kratky_popis': kratky,
            'dlouhy_popis': dlouhy,
            'dostupnost': dostupnost,
            'obrazky': obrazky
        }

    except Exception as e:
        safe_print(f"[ERROR] Chyba u produktu: {url} -> {e}")
        if log:
            log.write(f"[ERROR] Produkt selhal: {url} -> {e}\n")
        return None

category_urls = [

    
    "https://www.aunika.com/Autohifi/1DIN-autoradia",
    "https://www.aunika.com/Multimedia/AV-jednotky",
    "https://www.aunika.com/Multimedia/Moduly-Apple-CarPlay-Android-Auto",
    "https://www.aunika.com/Autohifi/Komponentni-reproduktory",
    "https://www.aunika.com/Autohifi/Koaxialni-reproduktory",
    "https://www.aunika.com/Autohifi/OEM-reproduktory",
    "https://www.aunika.com/Autohifi/Aktivni-subwoofery",
    "https://www.aunika.com/Autohifi/Subwoofery",
    "https://www.aunika.com/Autohifi/Vysokotonove-repro",
    "https://www.aunika.com/Autohifi/Zesilovace",
    "https://www.aunika.com/Autohifi/DSP-procesory",
    "https://www.aunika.com/Prislusenstvi-pro-autohifi/STP-izolacni-a-tlumici-materialy",
    "https://www.aunika.com/Prislusenstvi-pro-autohifi/MDF-adaptery-repro",
    "https://www.aunika.com/Prislusenstvi-pro-autohifi/GF20-adaptery-repro",
    "https://www.aunika.com/Hands-free-sady-GSM-prislusenstvi/Magneticke-drzaky-pro-mobilni-telefony",
    "https://www.aunika.com/Hands-free-sady-GSM-prislusenstvi/Nabijecky-pro-mobilni-telefony/USB-nabijecky-do-CL-zasuvky",
    "https://www.aunika.com/Hands-free-sady-GSM-prislusenstvi/Inbay-bezdratove-nabijeni",
    "https://www.aunika.com/Elektronicke-systemy-do-automobilu/Tempomaty"

]

vsechny_produkty = []
for k in category_urls:
    try:
        urls = get_product_links_selenium(k)
        if not urls:
            safe_print(f"[WARNING] Žádné odkazy pro kategorii: {k}")
            if log:
                log.write(f"[WARNING] Žádné odkazy pro kategorii: {k}\n")
            continue
        safe_print(f"[INFO] Nalezeno {len(urls)} produktů z kategorie: {k}")
        if log:
            log.write(f"[INFO] {len(urls)} produktů z kategorie: {k}\n")
        vsechny_produkty.extend(urls)
    except Exception as e:
        safe_print(f"[ERROR] Selhalo načítání kategorie {k} -> {e}")
        if log:
            log.write(f"[ERROR] Kategorie selhala: {k} -> {e}\n")


parsed_products = []
with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_url = {executor.submit(parse_product_page, url): url for url in vsechny_produkty}
    for i, future in enumerate(as_completed(future_to_url), 1):
        result = future.result()
        if result:
            parsed_products.append(result)
        safe_print(f"[INFO] Produkt {i}/{len(vsechny_produkty)} zpracován.")

def c(tag, val, cdata=False):
    el = doc.createElement(tag)
    el.appendChild(doc.createCDATASection(val) if cdata else doc.createTextNode(val))
    return el

doc = Document()
root = doc.createElement('PRODUCTS')
root.setAttribute('version', '1.0')
doc.appendChild(root)

for data in parsed_products:
    product = doc.createElement('PRODUCT')
    root.appendChild(product)

    if data.get('objednaci_cislo'):
        product.appendChild(c('CODE', data['objednaci_cislo'], cdata=True))
    if data.get('vyrobce'):
        product.appendChild(c('MANUFACTURER', data['vyrobce'], cdata=True))

    descriptions = doc.createElement('DESCRIPTIONS')
    description = doc.createElement('DESCRIPTION')
    description.setAttribute('language', 'cz')
    description.appendChild(c('TITLE', data.get('nazev', ''), cdata=True))
    description.appendChild(c('SHORT_DESCRIPTION', data.get('kratky_popis', ''), cdata=True))
    description.appendChild(c('LONG_DESCRIPTION', data.get('dlouhy_popis', ''), cdata=True))
    descriptions.appendChild(description)
    product.appendChild(descriptions)

    vats = doc.createElement('VATS')
    vat = doc.createElement('VAT')
    vat.setAttribute('language', 'cz')
    vat.appendChild(doc.createCDATASection('21.00'))
    vats.appendChild(vat)
    product.appendChild(vats)

    if data.get('cena_num'):
        prices = doc.createElement('PRICES')
        price = doc.createElement('PRICE')
        price.setAttribute('language', 'cz')

        pricelists = doc.createElement('PRICELISTS')
        pricelist = doc.createElement('PRICELIST')
        pricelist.appendChild(c('NAME', 'Výchozí', cdata=True))
        pricelist.appendChild(c('PRICE_ORIGINAL', data['cena_num'], cdata=True))
        pricelists.appendChild(pricelist)

        price.appendChild(pricelists)
        price.appendChild(c('PRICE_COMMON', data['cena_num'], cdata=True))
        prices.appendChild(price)
        product.appendChild(prices)

    if data.get('obrazky'):
        images = doc.createElement('IMAGES')
        for idx, img_url in enumerate(data['obrazky']):
            image = doc.createElement('IMAGE')
            image.appendChild(c('URL', img_url, cdata=True))
            image.appendChild(c('MAIN_YN', '1' if idx == 0 else '0', cdata=True))
            image.appendChild(c('LIST_YN', '1' if idx == 0 else '0', cdata=True))
            images.appendChild(image)
        product.appendChild(images)

    stock_val = data.get('dostupnost')
    if stock_val:
        product.appendChild(c('STOCK', stock_val, cdata=True))

# 💾 Zápis XML
with open("test.xml", "w", encoding="utf-8") as f:
    f.write(doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))

# 📊 CSV export
with open("export.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ['url', 'objednaci_cislo', 'nazev', 'vyrobce', 'cena_bez_dph', 'dostupnost']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for d in parsed_products:
        writer.writerow({
            'url': d.get('url', ''),
            'objednaci_cislo': d.get('objednaci_cislo', ''),
            'nazev': d.get('nazev', ''),
            'vyrobce': d.get('vyrobce', ''),
            'cena_bez_dph': d.get('cena_bez_dph', ''),
            'dostupnost': d.get('dostupnost', '')
        })

# 📤 FTP upload
def upload_to_upgates(file_path):
    try:
        ftp = FTP()
        ftp.connect(host='ftp.s32.upgates.com', port=21)
        ftp.login(user='project_connections_23436', passwd='5dqjqfuu')

        with open(file_path, 'rb') as f:
            ftp.storbinary('STOR test.xml', f)

        ftp.quit()
        safe_print("[OK] test.xml byl nahrán na FTP.")
        if log:
            log.write("[OK] test.xml byl nahrán na FTP.\n")
    except Exception as e:
        safe_print(f"[ERROR] FTP upload selhal: {e}")
        if log:
            log.write(f"[ERROR] FTP upload selhal: {e}\n")

upload_to_upgates("test.xml")

if log:
    log.write(f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S,%f')[:-3]}] Hotovo.\n\n")
    log.close()
