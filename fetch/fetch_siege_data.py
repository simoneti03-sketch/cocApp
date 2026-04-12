import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'siege')

# Mapeo de Máquinas de Asedio y sus URLs
TARGETS = {
    "WallWrecker": "https://clashofclans.fandom.com/wiki/Wall_Wrecker",
    "BattleBlimp": "https://clashofclans.fandom.com/wiki/Battle_Blimp",
    "StoneSlammer": "https://clashofclans.fandom.com/wiki/Stone_Slammer",
    "SiegeBarracks": "https://clashofclans.fandom.com/wiki/Siege_Barracks",
    "LogLauncher": "https://clashofclans.fandom.com/wiki/Log_Launcher",
    "FlameFlinger": "https://clashofclans.fandom.com/wiki/Flame_Flinger",
    "BattleDrill": "https://clashofclans.fandom.com/wiki/Battle_Drill",
    "TroopLauncher": "https://clashofclans.fandom.com/wiki/Troop_Launcher"
}

def parse_time_to_seconds(time_str):
    if not time_str or any(x in time_str.lower() for x in ['none', 'n/a', 'instan']):
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
    print(f"Buscando asedio: {name}...")
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
        # Buscamos la tabla de mejora del laboratorio
        if 'level' in header_text and ('upgrade cost' in header_text or 'research cost' in header_text):
            stats_table = table
            break

    if not stats_table:
        return []

    rows = stats_table.find_all('tr')
    data_list = []
    
    for row in rows[1:]:
        cols = row.find_all(['td', 'th'])
        if len(cols) >= 4:
            try:
                # 1. Nivel
                lvl_raw = cols[0].text.strip().split()[0]
                if not lvl_raw.isdigit(): continue
                level = int(lvl_raw)
                
                # 2. Costo (Oro para máquinas de asedio)
                cost = 0
                for col in cols[1:5]:
                    c_text = col.text.strip().replace(',', '').replace(' ', '').replace('.', '')
                    nums = re.findall(r'\d+', c_text)
                    if nums:
                        val = int(nums[0])
                        # Filtro: costos de asedio suelen ser > 1M (1.000.000)
                        if val > 1000: 
                            cost = val
                            break

                # 3. Tiempo
                time_str = "0"
                for col in cols[2:6]:
                    t_text = col.text.strip().lower()
                    if any(unit in t_text for unit in ['d', 'h', 'm']):
                        time_str = t_text
                        break
                duration = parse_time_to_seconds(time_str)
                
                # 4. Ayuntamiento (TH) requerido
                th_level = 12 # El asedio empieza en TH12
                row_text = row.text.lower()
                th_match = re.search(r'th\s*(\d+)', row_text)
                if th_match:
                    th_level = int(th_match.group(1))
                else:
                    # Si no lo encuentra, buscamos el nivel de laboratorio y sumamos
                    last_nums = re.findall(r'\d+', cols[-1].text)
                    if last_nums:
                        lab_lvl = int(last_nums[-1])
                        th_level = lab_lvl + 2 # Aproximación común

                item = {
                    "level": level,
                    "cost": cost,
                    "currency": "elixir", # Se mejoran con elixir (rosa) en el laboratorio
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
            print(f"✗ No se pudo procesar: {name}")

if __name__ == "__main__":
    main()