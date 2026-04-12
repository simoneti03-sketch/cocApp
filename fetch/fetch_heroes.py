import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'heroes')

TARGETS = {
    "BarbarianKing": "https://clashofclans.fandom.com/wiki/Barbarian_King",
    "ArcherQueen": "https://clashofclans.fandom.com/wiki/Archer_Queen",
    "GrandWarden": "https://clashofclans.fandom.com/wiki/Grand_Warden",
    "RoyalChampion": "https://clashofclans.fandom.com/wiki/Royal_Champion",
    "DragonDuke": "https://clashofclans.fandom.com/wiki/Dragon_Duke",
    "MinionPrince": "https://clashofclans.fandom.com/wiki/Minion_Prince"
}

def parse_time_to_seconds(time_str):
    if not time_str or any(x in time_str.lower() for x in ['none', 'n/a', 'instan', '—']):
        return 0
    days = hours = minutes = 0
    time_str = time_str.lower()
    if 'd' in time_str:
        match = re.search(r'(\d+)\s*d', time_str)
        if match: days = int(match.group(1))
    if 'h' in time_str:
        match = re.search(r'(\d+)\s*h', time_str)
        if match: hours = int(match.group(1))
    if 'm' in time_str:
        match = re.search(r'(\d+)\s*m', time_str)
        if match: minutes = int(match.group(1))
    return int((days * 86400) + (hours * 3600) + (minutes * 60))

def fetch_and_parse(name, url):
    print(f"Extrayendo datos de {name}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', class_=['article-table', 'wikitable'])
    
    stats_table = None
    for table in tables:
        txt = table.text.lower()
        if 'level' in txt and ('cost' in txt or 'upgrade' in txt or 'time' in txt):
            stats_table = table
            break

    if not stats_table: return []

    rows = stats_table.find_all('tr')
    data_list = []
    last_known_hh = 1 # Valor por defecto

    for row in rows:
        cols = row.find_all('td')
        if not cols: continue
        
        # 1. Nivel del Héroe (Primera columna)
        lvl_text = cols[0].get_text(strip=True)
        if not lvl_text.isdigit(): continue
        level = int(lvl_text)

        # 2. Buscar Costo (puede ser rCost o bCost según el héroe)
        td_cost = row.find('td', class_=re.compile(r'(rCost|bCost)'))
        cost = 0
        if td_cost:
            nums = re.findall(r'\d+', td_cost.get_text(strip=True).replace(',', ''))
            if nums: cost = int(nums[0])

        # 3. Buscar Tiempo (puede ser rTime o bTime)
        td_time = row.find('td', class_=re.compile(r'(rTime|bTime)'))
        duration = 0
        if td_time:
            duration = parse_time_to_seconds(td_time.get_text(strip=True))

        # 4. Hero Hall (HH) - Última columna (como subrayaste en la imagen)
        td_hh = cols[-1]
        hh_text = td_hh.get_text(strip=True)
        hh_nums = re.findall(r'\d+', hh_text)
        if hh_nums:
            last_known_hh = int(hh_nums[-1]) # Cogemos el último número de esa celda

        # Definir moneda
        currency = "darkelixir"
        if name == "GrandWarden":
            currency = "elixir"

        data_list.append({
            "level": level,
            "cost": cost,
            "currency": currency,
            "duration": duration,
            "HH": last_known_hh
        })
                
    return data_list

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, url in TARGETS.items():
        data = fetch_and_parse(name, url)
        if data:
            filepath = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✓ {name}.json generado con clave HH.")

if __name__ == "__main__":
    main()