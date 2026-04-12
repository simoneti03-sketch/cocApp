import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'pets')

TARGETS = {
    "Lassi": "https://clashofclans.fandom.com/wiki/L.A.S.S.I",
    "ElectroOwl": "https://clashofclans.fandom.com/wiki/Electro_Owl",
    "MightyYak": "https://clashofclans.fandom.com/wiki/Mighty_Yak",
    "Unicorn": "https://clashofclans.fandom.com/wiki/Unicorn",
    "Frosty": "https://clashofclans.fandom.com/wiki/Frosty",
    "Diggy": "https://clashofclans.fandom.com/wiki/Diggy",
    "PoisonLizard": "https://clashofclans.fandom.com/wiki/Poison_Lizard",
    "Phoenix": "https://clashofclans.fandom.com/wiki/Phoenix",
    "SpiritFox": "https://clashofclans.fandom.com/wiki/Spirit_Fox",
    "AngryJelly": "https://clashofclans.fandom.com/wiki/Angry_Jelly",
    "Sneezy": "https://clashofclans.fandom.com/wiki/Sneezy",
    "GreedyRaven": "https://clashofclans.fandom.com/wiki/Greedy_Raven"
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
    print(f"Analizando {name}...")
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
        if 'level' in txt and ('cost' in txt or 'upgrade' in txt):
            stats_table = table
            break

    if not stats_table: return []

    rows = stats_table.find_all('tr')
    data_list = []
    
    # Variable para arrastrar el nivel de PH si las celdas vienen vacías
    last_known_ph = 0

    # Mapeo inicial de seguridad por si la primera fila falla
    mapping = {"Lassi":1,"ElectroOwl":2,"MightyYak":3,"Unicorn":4,"Frosty":5,"Diggy":6,"PoisonLizard":7,"Phoenix":8,"SpiritFox":9,"AngryJelly":10,"Sneezy":11,"GreedyRaven":12}
    last_known_ph = mapping.get(name, 1)

    for row in rows:
        cols = row.find_all('td')
        if not cols: continue
        
        # 1. Nivel de Mascota
        lvl_text = cols[0].get_text(strip=True)
        if not lvl_text.isdigit(): continue
        level = int(lvl_text)

        # 2. Costo y Tiempo usando las clases que vimos en tu imagen
        td_cost = row.find('td', class_=re.compile(r'rCost'))
        td_time = row.find('td', class_=re.compile(r'rTime'))
        
        # 3. PH: Buscamos la celda 'change-highlight' o la última columna
        td_ph = row.find('td', class_='change-highlight')
        if not td_ph:
            # Si no tiene la clase, probamos por posición (suele ser la última)
            td_ph = cols[-1]

        # Extraer PH
        ph_text = td_ph.get_text(strip=True)
        ph_nums = re.findall(r'\d+', ph_text)
        
        if ph_nums:
            current_ph = int(ph_nums[0])
            # Si el número es razonable para PH (1-15), lo actualizamos
            if 1 <= current_ph <= 15:
                last_known_ph = current_ph

        # Extraer Costo
        cost = 0
        if td_cost:
            nums = re.findall(r'\d+', td_cost.get_text(strip=True).replace(',', ''))
            if nums: cost = int(nums[0])
        
        # Extraer Tiempo
        duration = 0
        if td_time:
            duration = parse_time_to_seconds(td_time.get_text(strip=True))

        data_list.append({
            "level": level,
            "cost": cost,
            "currency": "darkelixir",
            "duration": duration,
            "PH": last_known_ph
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
            print(f"✓ {name}.json actualizado.")

if __name__ == "__main__":
    main()