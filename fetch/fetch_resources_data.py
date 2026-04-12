import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'resources')

# Mapeo de edificios de recursos y sus URLs
TARGETS = {
    "GoldMine": "https://clashofclans.fandom.com/wiki/Gold_Mine",
    "ElixirCollector": "https://clashofclans.fandom.com/wiki/Elixir_Collector",
    "DarkElixirDrill": "https://clashofclans.fandom.com/wiki/Dark_Elixir_Drill",
    "GoldStorage": "https://clashofclans.fandom.com/wiki/Gold_Storage",
    "ElixirStorage": "https://clashofclans.fandom.com/wiki/Elixir_Storage",
    "DarkElixirStorage": "https://clashofclans.fandom.com/wiki/Dark_Elixir_Storage",
    "ClanCastle": "https://clashofclans.fandom.com/wiki/Clan_Castle"
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
    print(f"Buscando recurso: {name}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al descargar {name}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', class_=['article-table', 'wikitable'])
    
    stats_table = None
    for table in tables:
        header_text = table.text.lower()
        # Buscamos la tabla de estadísticas de mejora
        if 'level' in header_text and ('upgrade cost' in header_text or 'build cost' in header_text or 'capacity' in header_text):
            # Evitamos tablas informativas de "cantidad por TH"
            if 'town hall level' not in header_text[:50]:
                stats_table = table
                break

    if not stats_table:
        return []

    rows = stats_table.find_all('tr')
    data_list = []
    
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) >= 4:
            try:
                # 1. Nivel
                lvl_raw = cols[0].text.strip().split('\n')[0].split('[')[0].strip()
                if not lvl_raw.isdigit(): continue
                level = int(lvl_raw)
                
                # 2. Moneda y Costo
                cost = 0
                currency = "gold"
                
                # Lógica de moneda para recursos:
                if "GoldMine" in name or "GoldStorage" in name:
                    currency = "elixir"
                elif "ElixirCollector" in name or "ElixirStorage" in name or "DarkElixirDrill" in name or "DarkElixirStorage" in name:
                    currency = "gold"
                elif "ClanCastle" in name:
                    currency = "gold"

                # Extraer número de costo
                for col in cols[1:5]:
                    c_text = col.text.strip().replace(',', '').replace(' ', '').replace('.', '')
                    nums = re.findall(r'\d+', c_text)
                    if nums and int(nums[0]) > 100:
                        cost = int(nums[0])
                        break
                    elif nums and int(nums[0]) == 0:
                        cost = 0
                        break

                # 3. Tiempo
                time_str = "0"
                for col in cols[1:6]:
                    t_text = col.text.strip().lower()
                    if any(unit in t_text for unit in ['d', 'h', 'm']):
                        time_str = t_text
                        break
                duration = parse_time_to_seconds(time_str)
                
                # 4. Ayuntamiento (TH)
                th_level = 1
                th_text = cols[-1].text.lower()
                th_match = re.search(r'(\d+)', th_text)
                if th_match:
                    th_level = int(th_match.group(1))

                item = {
                    "level": level,
                    "cost": cost,
                    "currency": currency,
                    "duration": duration,
                    "TH": th_level
                }
                
                if not data_list or data_list[-1]["level"] != level:
                    data_list.append(item)
            except:
                continue
                
    return data_list

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for name, url in TARGETS.items():
        data = fetch_and_parse(name, url)
        if data:
            filepath = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✓ Guardado: {name}.json ({len(data)} niveles)")
        else:
            print(f"✗ No se pudo encontrar la tabla para: {name}")

if __name__ == "__main__":
    main()