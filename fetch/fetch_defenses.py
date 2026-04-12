import os
import json
import cloudscraper
from bs4 import BeautifulSoup
import re
import time

# Directorio de salida
OUTPUT_DIR = os.path.join('..', 'data', 'defenses')

TARGETS = {
    "Cannon": "https://clashofclans.fandom.com/wiki/Cannon",
    "ArcherTower": "https://clashofclans.fandom.com/wiki/Archer_Tower",
    "Mortar": "https://clashofclans.fandom.com/wiki/Mortar",
    "AirDefense": "https://clashofclans.fandom.com/wiki/Air_Defense",
    "WizardTower": "https://clashofclans.fandom.com/wiki/Wizard_Tower",
    "AirSweeper": "https://clashofclans.fandom.com/wiki/Air_Sweeper",
    "HiddenTesla": "https://clashofclans.fandom.com/wiki/Hidden_Tesla",
    "BombTower": "https://clashofclans.fandom.com/wiki/Bomb_Tower",
    "XBow": "https://clashofclans.fandom.com/wiki/X-Bow",
    "InfernoTower": "https://clashofclans.fandom.com/wiki/Inferno_Tower",
    "EagleArtillery": "https://clashofclans.fandom.com/wiki/Eagle_Artillery",
    "Scattershot": "https://clashofclans.fandom.com/wiki/Scattershot",
    "BuildersHut": "https://clashofclans.fandom.com/wiki/Builder%27s_Hut",
    "SpellTower": "https://clashofclans.fandom.com/wiki/Spell_Tower",
    "Monolith": "https://clashofclans.fandom.com/wiki/Monolith",
    "MultiArcherTower": "https://clashofclans.fandom.com/wiki/Multi-Archer_Tower",
    "RicochetCannon": "https://clashofclans.fandom.com/wiki/Ricochet_Cannon",
    "InfernoArtillery": "https://clashofclans.fandom.com/wiki/Inferno_Artillery",
    "MultiGearTower": "https://clashofclans.fandom.com/wiki/Multi-Gear_Tower",
    "Firespitter": "https://clashofclans.fandom.com/wiki/Firespitter",
    "TownHall": "https://clashofclans.fandom.com/wiki/Town_Hall",
    "Wall": "https://clashofclans.fandom.com/wiki/Wall",
    "AirSweeper": "https://clashofclans.fandom.com/wiki/Air_Sweeper"
}

def parse_time_to_seconds(time_str):
    if not time_str or any(x in time_str.lower() for x in ['none', 'n/a', 'instan', '—']):
        return 0
    d = h = m = 0
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

def fetch_and_parse(name, url):
    print(f"Descargando datos para: {name}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"✗ Error al descargar {name}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', class_=['article-table', 'wikitable'])
    
    stats_table = None
    for table in tables:
        txt = table.text.lower()
        # Verificamos que sea una tabla de mejora, ignorando las tablas de "Cantidad disponible por TH"
        if 'level' in txt and ('build cost' in txt or 'upgrade cost' in txt or 'cost' in txt):
            if 'number available' not in txt:
                stats_table = table
                break

    if not stats_table:
        print(f"✗ No se encontró la tabla de estadísticas para {name}.")
        return []

    rows = stats_table.find_all('tr')
    data_list = []
    last_known_th = 1 

    for row in rows:
        cols = row.find_all('td')
        if not cols: continue
        
        # 1. Nivel
        lvl_text = cols[0].get_text(strip=True).split('[')[0] # Limpiar referencias [1]
        if not lvl_text.isdigit(): continue
        level = int(lvl_text)

        # 2. Costo (Busca específicamente la clase bCost o rCost de Fandom)
        td_cost = row.find('td', class_=re.compile(r'(bCost|rCost)'))
        cost = 0
        if td_cost:
            nums = re.findall(r'\d+', td_cost.get_text(strip=True).replace(',', '').replace('.', ''))
            if nums: cost = int(nums[0])

        # 3. Tiempo
        td_time = row.find('td', class_=re.compile(r'(bTime|rTime)'))
        duration = 0
        if td_time:
            duration = parse_time_to_seconds(td_time.get_text(strip=True))

        # 4. Town Hall (TH) - Última columna
        td_th = cols[-1]
        th_nums = re.findall(r'\d+', td_th.get_text(strip=True))
        if th_nums:
            current_th = int(th_nums[-1])
            # Validamos que sea un TH lógico (1 a 17)
            if 1 <= current_th <= 17:
                last_known_th = current_th

        # En el caso del Ayuntamiento (Town Hall), el TH requerido para mejorar al Nivel X es X-1
        # (Ej: Para mejorar a TH2, necesitas ser TH1)
        if name == "TownHall":
            last_known_th = max(1, level - 1)

        data_list.append({
            "level": level,
            "cost": cost,
            "currency": "gold", # Todas las defensas usan oro por defecto
            "duration": duration,
            "TH": last_known_th
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
            print(f"✓ {name}.json procesado ({len(data)} niveles)")
        else:
            print(f"✗ Fallo final para {name}")
        
        # Pequeña pausa para no saturar Fandom y evitar el Error 403 Forbidden
        time.sleep(1)

if __name__ == "__main__":
    main()