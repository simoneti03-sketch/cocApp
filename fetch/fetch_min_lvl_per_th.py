import json
import re
import os
import cloudscraper
from bs4 import BeautifulSoup

def fetch_min_lvl_per_th():
    url = "https://clashofclans.fandom.com/wiki/User_blog:Yehor4k2007/Required_Upgrades_for_each_Town_Hall_Level_(Minimal_Requirements_to_upgrade_a_Town_Hall)"
    
    print(f"Fetching data from {url}...")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'darwin', 'desktop': True})
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table', class_=['article-table', 'wikitable'])
    
    if not tables:
        tables = soup.find_all('table')

    results = {}
    current_inventory = {}

    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            continue
        
        th_header = rows[0].get_text(strip=True)
        th_match = re.search(r'Town Hall Level\s*(\d+)', th_header)
        if not th_match:
            continue
            
        th_number = int(th_match.group(1))
        th_key = f"TH{th_number}"
        
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 2:
                continue
            
            row_text = row.get_text().lower()
            if "building" in row_text and "level" in row_text:
                continue
            if "town hall level" in row_text:
                continue

            # 1. Extract Building Name and Quantity
            name_raw = cols[0].get_text(strip=True)
            
            # Regex to handle patterns like "Name x25", "25x Name", "Name x 25", etc.
            # Case insensitive 'x'
            pattern1 = re.search(r'^(.*?)\s*x\s*(\d+)$', name_raw, re.I)
            pattern2 = re.search(r'^(\d+)\s*x\s*(.*?)$', name_raw, re.I)
            
            if pattern1:
                building_name = pattern1.group(1).strip()
                quantity = int(pattern1.group(2))
            elif pattern2:
                building_name = pattern2.group(2).strip()
                quantity = int(pattern2.group(1))
            else:
                building_name = name_raw
                quantity = 1
            
            # Clean name (remove trailing numbers if it's something like "Cannon 2" but keep "X-Bow")
            # But mostly we want to avoid "Wall x25" becoming "Wallx25"
            building_name = re.sub(r'[\(\)]', '', building_name).strip()
            
            if not building_name:
                continue

            # 2. Extract Level
            level_raw = cols[1].get_text(strip=True)
            if not level_raw or level_raw.lower() in ["free", "-", "none", ""]:
                level = 1
            else:
                lvl_match = re.search(r'(\d+)', level_raw)
                level = int(lvl_match.group(1)) if lvl_match else 1
            
            # 3. Update Inventory (Cumulative)
            if building_name not in current_inventory:
                current_inventory[building_name] = {'count': 0, 'level': 1}
            
            # Logical check for updates vs new buildings
            is_explicit_upgrade = False
            if level > current_inventory[building_name]['level'] and quantity == 1 and not (pattern1 or pattern2):
                is_explicit_upgrade = True

            # Merge rules definition
            MERGE_RULES = {
                "Ricochet Cannon": {"Cannon": 2},
                "Multi-Archer Tower": {"Archer Tower": 2},
                "Multi Archer Tower": {"Archer Tower": 2},
                "Super Wizard Tower": {"Wizard Tower": 2},
                "Multi-Wizard Tower": {"Wizard Tower": 2},
                "Multi Gear Tower": {"Cannon": 1, "Archer Tower": 1},
                "Multi-Gear Tower": {"Cannon": 1, "Archer Tower": 1}
            }

            if is_explicit_upgrade:
                current_inventory[building_name]['level'] = level
                if current_inventory[building_name]['count'] == 0:
                    current_inventory[building_name]['count'] = 1
            else:
                # Add new buildings
                current_inventory[building_name]['count'] += quantity
                # Always ensure level is at least what's specified
                if level > current_inventory[building_name]['level']:
                    current_inventory[building_name]['level'] = level
                
                # Apply merge rules: subtract components
                # Normalize building name for matching (lowercase, no hyphens)
                norm_name = building_name.lower().replace("-", " ").strip()
                for _ in range(quantity):
                    matched = False
                    for merge_name, rules in MERGE_RULES.items():
                        norm_merge = merge_name.lower().replace("-", " ").strip()
                        if norm_name == norm_merge:
                            for component, comp_qty in rules.items():
                                # Try matching component name with or without plural 's'
                                variants = [component, component + "s", component.replace(" Tower", " Towers")]
                                for v in variants:
                                    if v in current_inventory:
                                        current_inventory[v]['count'] = max(0, current_inventory[v]['count'] - comp_qty)
                                        break
                            matched = True
                            break # Avoid matching multiple synonyms for the same building
                    if matched:
                        continue

        results[th_key] = {name: dict(info) for name, info in current_inventory.items()}

    return results

if __name__ == "__main__":
    if os.path.basename(os.getcwd()) == 'fetch':
        base_path = '..'
    else:
        base_path = '.'

    min_requirements = fetch_min_lvl_per_th()
    
    if min_requirements:
        sorted_keys = sorted(min_requirements.keys(), key=lambda x: int(re.search(r'\d+', x).group()))
        final_output = {k: min_requirements[k] for k in sorted_keys}
        
        print(f"Successfully processed {len(final_output)} TH levels.")
        
        output_dir = os.path.join(base_path, "static", "data")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "min_levels_per_th.json")
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
        print(f"Results saved to {output_path}")
    else:
        print("Failed to extract requirements.")
