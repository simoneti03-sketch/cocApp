import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorios de salida
BASE_DIR = os.path.join('..', 'data', 'units')

# Diccionario unificado: puedes poner todas aquí
TARGETS = {
    "elixir": {
        "Barbarian": "https://clashofclans.fandom.com/wiki/Barbarian",
        "Archer": "https://clashofclans.fandom.com/wiki/Archer",
        "Giant": "https://clashofclans.fandom.com/wiki/Giant",
        "Goblin": "https://clashofclans.fandom.com/wiki/Goblin",
        "Wallbreaker": "https://clashofclans.fandom.com/wiki/Wall_Breaker",
        "Ballon": "https://clashofclans.fandom.com/wiki/Balloon",
        "Wizard": "https://clashofclans.fandom.com/wiki/Wizard",
        "Healer": "https://clashofclans.fandom.com/wiki/Healer",
        "Dragon": "https://clashofclans.fandom.com/wiki/Dragon",
        "Pekka": "https://clashofclans.fandom.com/wiki/P.E.K.K.A",
        "BabyDragon": "https://clashofclans.fandom.com/wiki/Baby_Dragon",
        "Miner": "https://clashofclans.fandom.com/wiki/Miner",
        "ElectroDragon": "https://clashofclans.fandom.com/wiki/Electro_Dragon",
        "Yeti": "https://clashofclans.fandom.com/wiki/Yeti",
        "DragonRider": "https://clashofclans.fandom.com/wiki/Dragon_Rider",
        "ElectroTitan": "https://clashofclans.fandom.com/wiki/Electro_Titan",
        "RootRider": "https://clashofclans.fandom.com/wiki/Root_Rider",
        "MeteorGolem": "https://clashofclans.fandom.com/wiki/Meteor_Golem",
        "Thrower": "https://clashofclans.fandom.com/wiki/Thrower"
    },
    "dark": {
        "Minion": "https://clashofclans.fandom.com/wiki/Minion",
        "HogRider": "https://clashofclans.fandom.com/wiki/Hog_Rider",
        "Valkyrie": "https://clashofclans.fandom.com/wiki/Valkyrie",
        "Golem": "https://clashofclans.fandom.com/wiki/Golem",
        "Witch": "https://clashofclans.fandom.com/wiki/Witch",
        "LavaHound": "https://clashofclans.fandom.com/wiki/Lava_Hound",
        "Bowler": "https://clashofclans.fandom.com/wiki/Bowler",
        "IceGolem": "https://clashofclans.fandom.com/wiki/Ice_Golem",
        "Headhunter": "https://clashofclans.fandom.com/wiki/Headhunter",
        "ApprenticeWarden": "https://clashofclans.fandom.com/wiki/Apprentice_Warden",
        "Druid": "https://clashofclans.fandom.com/wiki/Druid",
        "Furnace": "https://clashofclans.fandom.com/wiki/Furnace"
    }
}

def parse_time_to_seconds(time_str):
    if not time_str or any(x in time_str.lower() for x in ['none', 'n/a', 'instan', '—']):
        return 0
    d=h=m=0
    time_str = time_str.lower()
    if 'd' in time_str:
        match = re.search(r'(\d+)\s*d', time_str)
        if match: d = int(match.group(1))
    if 'h' in time_str:
        match = re.search(r'(\d+)\s*h', time_str)
        if match: h = int(match.group(1))
    if 'm' in time_str:
        match = re.search(r'(\d+)\s*m', time_str)
        if match: m = int(match.group(1))
    return int((d * 86400) + (h * 3600) + (m * 60))

def fetch_and_parse(name, url, currency_type):
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
        if 'level' in txt and ('upgrade cost' in txt or 'research cost' in txt):
            stats_table = table
            break

    if not stats_table: return []

    rows = stats_table.find_all('tr')
    data_list = []
    last_known_ll = 1 

    for row in rows:
        cols = row.find_all('td')
        if not cols: continue
        
        lvl_text = cols[0].get_text(strip=True)
        if not lvl_text.isdigit(): continue
        level = int(lvl_text)

        # Buscar por clases dinámicas (rCost/bCost y rTime/bTime)
        td_cost = row.find('td', class_=re.compile(r'(rCost|bCost)'))
        td_time = row.find('td', class_=re.compile(r'(rTime|bTime)'))
        
        # LL es la última columna
        td_ll = cols[-1]
        ll_nums = re.findall(r'\d+', td_ll.get_text(strip=True))
        if ll_nums:
            last_known_ll = int(ll_nums[-1])

        cost = 0
        if td_cost:
            nums = re.findall(r'\d+', td_cost.get_text(strip=True).replace(',', ''))
            if nums: cost = int(nums[0])

        duration = 0
        if td_time:
            duration = parse_time_to_seconds(td_time.get_text(strip=True))

        data_list.append({
            "level": level,
            "cost": cost,
            "currency": "darkelixir" if currency_type == "dark" else "elixir",
            "duration": duration,
            "LL": last_known_ll
        })

    # Post-procesamiento: si el nivel 1 tiene LL 1 por defecto, usar el LL del nivel 2
    if len(data_list) >= 2:
        if data_list[0]['level'] == 1 and data_list[0].get('LL', 0) <= 1:
            data_list[0]['LL'] = data_list[1].get('LL', 1)
                
    return data_list

def main():
    for c_type, units in TARGETS.items():
        folder = os.path.join(BASE_DIR, c_type)
        os.makedirs(folder, exist_ok=True)
        for name, url in units.items():
            data = fetch_and_parse(name, url, c_type)
            if data:
                filepath = os.path.join(folder, f"{name}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"✓ {name}.json guardado en {c_type}")

if __name__ == "__main__":
    main()