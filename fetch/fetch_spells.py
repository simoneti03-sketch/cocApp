import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re

# Directorio base (sube a cocApp/data1/spells)
BASE_DIR = os.path.join('..', 'data', 'spells')

TARGETS = {
    "elixir": {
        "Lightning": "https://clashofclans.fandom.com/wiki/Lightning_Spell",
        "Healing": "https://clashofclans.fandom.com/wiki/Healing_Spell",
        "Rage": "https://clashofclans.fandom.com/wiki/Rage_Spell",
        "Jump": "https://clashofclans.fandom.com/wiki/Jump_Spell",
        "Freeze": "https://clashofclans.fandom.com/wiki/Freeze_Spell",
        "Clone": "https://clashofclans.fandom.com/wiki/Clone_Spell",
        "Invisibility": "https://clashofclans.fandom.com/wiki/Invisibility_Spell",
        "Recall": "https://clashofclans.fandom.com/wiki/Recall_Spell",
        "Revive": "https://clashofclans.fandom.com/wiki/Revive_Spell",
        "Totem": "https://clashofclans.fandom.com/wiki/Totem_Spell"
    },
    "dark": {
        "Poison": "https://clashofclans.fandom.com/wiki/Poison_Spell",
        "Earthquake": "https://clashofclans.fandom.com/wiki/Earthquake_Spell",
        "Haste": "https://clashofclans.fandom.com/wiki/Haste_Spell",
        "Skeleton": "https://clashofclans.fandom.com/wiki/Skeleton_Spell",
        "Bat": "https://clashofclans.fandom.com/wiki/Bat_Spell",
        "Overgrowth": "https://clashofclans.fandom.com/wiki/Overgrowth_Spell",
        "IceBlock": "https://clashofclans.fandom.com/wiki/Ice_Block_Spell"
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

def fetch_and_parse(name, url, spell_type):
    print(f"Analizando hechizo: {name}...")
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

        # Buscar Costo y Tiempo por clases de rCost/bCost y rTime/bTime
        td_cost = row.find('td', class_=re.compile(r'(rCost|bCost)'))
        td_time = row.find('td', class_=re.compile(r'(rTime|bTime)'))
        
        # El nivel de Laboratorio (LL) es la última columna
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
            "currency": "darkelixir" if spell_type == "dark" else "elixir",
            "duration": duration,
            "LL": last_known_ll
        })
                
    return data_list

def main():
    # El diccionario TARGETS ahora separa por 'elixir' y 'dark'
    # 'dark' se guardará en data1/spells/Dark y 'elixir' en data1/spells/Elixir
    for s_type, spells in TARGETS.items():
        # Capitalizamos la carpeta (Dark/Elixir) para mantener tu estructura original
        folder_name = s_type.capitalize()
        folder_path = os.path.join(BASE_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        for name, url in spells.items():
            data = fetch_and_parse(name, url, s_type)
            if data:
                filepath = os.path.join(folder_path, f"{name}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"✓ {name}.json guardado en {folder_name}")

if __name__ == "__main__":
    main()