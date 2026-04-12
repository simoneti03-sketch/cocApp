import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'army')

# Lista de edificios de ejército y sus URLs
TARGETS = {
    "ArmyCamp": "https://clashofclans.fandom.com/wiki/Army_Camp",
    "Barracks": "https://clashofclans.fandom.com/wiki/Barracks",
    "Blacksmith": "https://clashofclans.fandom.com/wiki/Blacksmith",
    "DarkBarracks": "https://clashofclans.fandom.com/wiki/Dark_Barracks",
    "DarkSpellFactory": "https://clashofclans.fandom.com/wiki/Dark_Spell_Factory",
    "HeroHall": "https://clashofclans.fandom.com/wiki/Hero_Hall",
    "Laboratory": "https://clashofclans.fandom.com/wiki/Laboratory",
    "PetHouse": "https://clashofclans.fandom.com/wiki/Pet_House",
    "SpellFactory": "https://clashofclans.fandom.com/wiki/Spell_Factory",
    "Workshop": "https://clashofclans.fandom.com/wiki/Workshop"
}

def parse_time_to_seconds(time_str):
    if not time_str or any(x in time_str.lower() for x in ['none', 'n/a', 'instan']):
        return 0
    days = hours = minutes = seconds = 0
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
    if 's' in time_str:
        match = re.search(r'(\d+)\s*s', time_str)
        if match: seconds = int(match.group(1))
    return int((days * 86400) + (hours * 3600) + (minutes * 60) + seconds)

def fetch_and_parse(name, url):
    print(f"Buscando {name}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al descargar {name}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    
    stats_table = None
    for table in tables:
        text = table.text.lower()
        # Buscamos la tabla que contiene los niveles de mejora
        if 'level' in text and ('build cost' in text or 'upgrade cost' in text or 'cost' in text):
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
                
                # 2. Costo y Moneda
                cost = 0
                currency = "elixir" # Por defecto para edificios de ejército
                
                # Buscar moneda y valor en las columnas
                row_html = str(row).lower()
                if 'darkelixir' in row_html.replace(' ', ''):
                    currency = "dark_elixir"
                elif 'gold' in row_html:
                    currency = "gold"
                
                # Extraer el número de costo (buscando el primer número grande en columnas 1 a 4)
                for col in cols[1:5]:
                    c_text = col.text.strip().replace(',', '').replace(' ', '').replace('.', '')
                    nums = re.findall(r'\d+', c_text)
                    if nums and int(nums[0]) > 100:
                        cost = int(nums[0])
                        break

                # 3. Tiempo
                time_str = "0"
                for col in cols[2:7]:
                    t_text = col.text.strip().lower()
                    if any(unit in t_text for unit in ['d', 'h', 'm', 's']):
                        time_str = t_text
                        break
                duration = parse_time_to_seconds(time_str)
                
                # 4. Ayuntamiento (TH) - Suele ser la última columna
                th_text = cols[-1].text.strip()
                th_match = re.search(r'\d+', th_text)
                th_level = int(th_match.group()) if th_match else 1
                
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
            print(f"✗ No se pudo procesar: {name}")

if __name__ == "__main__":
    main()