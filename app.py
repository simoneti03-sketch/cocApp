import json
import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ============================================================
# Cargar datos verificados directamente desde new_data/
# ============================================================
NEW_DATA_DIR = os.path.join(os.path.dirname(__file__), 'new_data')
MAX_TH = 17

# Mapeo: se cargará dinámicamente desde new_data/mapping_id_to_name.json

def _compute_max_level_per_th(levels, max_th=MAX_TH):
    """Genera array [max_lvl_en_TH1, ..., max_lvl_en_THn] desde los datos por nivel."""
    result = [0] * max_th
    for entry in levels:
        th = entry.get("TH", 1)
        lvl = entry.get("level", 0)
        if th <= max_th:
            for i in range(th - 1, max_th):
                if lvl > result[i]:
                    result[i] = lvl
    return result

def _compute_max_level_per_hh(levels, max_hh=12):
    """Genera array [max_lvl_en_HH1, ..., max_lvl_en_HHn] para héroes."""
    result = [0] * max_hh
    for entry in levels:
        hh = entry.get("HH", 1)
        lvl = entry.get("level", 0)
        if hh <= max_hh:
            for i in range(hh - 1, max_hh):
                if lvl > result[i]:
                    result[i] = lvl
    return result

def _compute_max_level_per_ph(levels, max_ph=12):
    """Genera array [max_lvl_en_PH1, ..., max_lvl_en_PHn] para mascotas."""
    result = [0] * max_ph
    for entry in levels:
        ph = entry.get("PH", 1)
        lvl = entry.get("level", 0)
        if ph <= max_ph:
            for i in range(ph - 1, max_ph):
                if lvl > result[i]:
                    result[i] = lvl
    return result

def _load_new_data():
    """Lee todos los JSON de new_data/ y construye el diccionario maestro."""
    master_db = {}
    
    # Cargar el mapeo de IDs a nombres desde el archivo JSON
    mapping_path = os.path.join(NEW_DATA_DIR, "mapping_id_to_name.json")
    file_to_id = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as fm:
            file_to_id = json.load(fm)
            
    # Leer archivo de traducciones
    translations = {}
    trans_path = os.path.join(NEW_DATA_DIR, 'translations.json')
    if os.path.exists(trans_path):
        with open(trans_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            
    for rel_path, mapping_info in file_to_id.items():
        # Recuperar (id_in_game, nombre_bonito) usando mapping_info que es un Array
        item_id, name = mapping_info
        
        full_path = os.path.join(NEW_DATA_DIR, rel_path)
        if not os.path.exists(full_path):
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            levels = json.load(f)
        
        levels.sort(key=lambda x: x.get("level", 0))
        
        is_hero = rel_path.startswith("heroes/")
        is_pet = rel_path.startswith("pets/")
        
        translated_name = translations.get(name, name)
        
        entry = {
            "name": translated_name,
            "category": rel_path.split('/')[0],
            "currency": levels[0].get("currency", "gold") if levels else "gold",
            "upgrade_times": [e.get("duration", 0) for e in levels],
            "price_per_lvl": [e.get("cost", 0) for e in levels],
        }
        
        if is_hero:
            entry["max_level_per_hh"] = _compute_max_level_per_hh(levels)
        elif is_pet:
            entry["max_level_per_ph"] = _compute_max_level_per_ph(levels)
        else:
            entry["max_level_per_th"] = _compute_max_level_per_th(levels)
        
        master_db[item_id] = entry
    
    return master_db

# Cargar todo al arrancar
game_data = _load_new_data()
print(f"✅ Cargados {len(game_data)} ítems desde new_data/")

@app.route('/')
def index():
    return render_template('index.html')

def process_category(items, db_category, th_level=1, hh_level=0, ph_level=0):
    processed_groups = {}
    total_time = 0
    
    # Si el usuario pasa un diccionario de id -> data en lugar de un arreglo de objetos
    if isinstance(items, dict):
        new_items = []
        for k, v in items.items():
            if isinstance(v, dict):
                if 'id' not in v:
                    v['id'] = k
                new_items.append(v)
            elif isinstance(v, (int, float)):
                new_items.append({'id': k, 'lvl': v})
        items = new_items
        
    for item in items:
        item_id = str(item.get('id', item.get('tag', item.get('data', ''))))
        if not item_id: continue
        
        current_lvl = int(item.get('lvl', item.get('level', 0)))
        time_left = int(item.get('time_left', item.get('timeLeft', item.get('timer', 0))))
        cnt = int(item.get('cnt', 1))
        
        default_name = item_id
        name = item.get('name', default_name)
        
        ref = db_category.get(item_id)
        if not ref:
            for k, v in db_category.items():
                if v.get('name', '').lower() == name.lower() and name.lower() != "":
                    ref = v
                    item_id = k
                    break
        
        max_lvl = current_lvl
        times = []
        is_maxed = False
        
        if ref:
            name = ref.get('name', default_name) or default_name
            times = ref.get('upgrade_times', [])
            
            # Si el ítem tiene max_level_per_hh (héroes), usar hh_level
            hh_max_list = ref.get('max_level_per_hh')
            ph_max_list = ref.get('max_level_per_ph')
            th_max_list = ref.get('max_level_per_th')
            
            if hh_max_list and hh_level > 0 and len(hh_max_list) >= hh_level:
                max_lvl = hh_max_list[hh_level - 1]
            elif ph_max_list and ph_level > 0 and len(ph_max_list) >= ph_level:
                max_lvl = ph_max_list[ph_level - 1]
            elif th_max_list and len(th_max_list) >= th_level:
                max_lvl = th_max_list[th_level - 1]
            else:
                max_lvl = ref.get('max_level', current_lvl)
            
            if current_lvl > max_lvl and max_lvl > 0:
                current_lvl = max_lvl
                
            is_maxed = (current_lvl >= max_lvl and max_lvl > 0)
            
        instance_time_to_max = 0
        is_upgrading = (time_left > 0)
        
        if not is_maxed:
            if is_upgrading:
                instance_time_to_max += time_left
                for l in range(current_lvl + 2, max_lvl + 1):
                    idx = l - 1
                    if idx >= 0 and idx < len(times):
                        instance_time_to_max += times[idx]
            else:
                for l in range(current_lvl + 1, max_lvl + 1):
                    idx = l - 1
                    if idx >= 0 and idx < len(times):
                        instance_time_to_max += times[idx]
        
        total_instance_time = instance_time_to_max * cnt
        
        if item_id not in processed_groups:
            processed_groups[item_id] = {
                'id': item_id,
                'name': name,
                'max_lvl': max_lvl,
                'currency': ref.get('currency', 'gold') if ref else 'gold',
                'total_cnt': 0,
                'is_fully_maxed': True,
                'total_time_to_max': 0,
                'progress_sum': 0,
                'instances': []
            }
            
        group = processed_groups[item_id]
        group['total_cnt'] += cnt
        group['total_time_to_max'] += total_instance_time
        
        prog = (current_lvl / max_lvl) * 100 if max_lvl > 0 else 100
        group['progress_sum'] += (prog * cnt)
        
        if not is_maxed:
            group['is_fully_maxed'] = False
            
        group['instances'].append({
            'cnt': cnt,
            'current_lvl': current_lvl,
            'is_maxed': is_maxed,
            'is_upgrading': is_upgrading,
            'time_left': time_left,
            'time_to_max': instance_time_to_max,
            'weapon': int(item.get('weapon', 0)),
            'gear_up': int(item.get('gear_up', 0)),
            'raw_data': None
        })
        
        total_time += total_instance_time

    processed_list = []
    for g in processed_groups.values():
        if g['total_cnt'] > 0:
            g['progress_percentage'] = g['progress_sum'] / g['total_cnt']
            # Para evitar que una categoría de %100 se sobrepase si el JSON arroja un nivel inflado temporalmente
            if g['progress_percentage'] > 100: g['progress_percentage'] = 100
        else:
            g['progress_percentage'] = 100
        processed_list.append(g)
        
    return processed_list, total_time

@app.route('/api/process', methods=['POST'])
def process_village():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    # game_data ya es un diccionario plano id → datos
    master_db = game_data
            
    # Filtrar edificios y detectar TH, HH, Bob's Hut y Helper Hut
    th_level = 1
    hh_level = 0
    ph_level = 0
    has_bob = False
    
    army_buildings = []
    resources_buildings = []
    defenses_buildings = []
    
    for b in data.get('buildings', []):
        id_str = str(b.get('data'))
        if id_str == '1000001':
            th_level = int(b.get('lvl', 1))
            defenses_buildings.append(b) # TownHall goes to defenses
        elif id_str == '1000071':
            hh_level = int(b.get('lvl', 0))
            army_buildings.append(b) # HeroHall usually army
        elif id_str == '1000068': # Pet House
            ph_level = int(b.get('lvl', 0))
            army_buildings.append(b)
        elif id_str == '1000093': # HelperHut
            defenses_buildings.append(b)
        elif id_str == '1000064': # Bob's Hut
            has_bob = True
        else:
            ref = master_db.get(id_str)
            cat = ref.get('category', 'defenses') if ref else 'defenses'
            if cat == 'army':
                army_buildings.append(b)
            elif cat == 'resources':
                resources_buildings.append(b)
            else:
                defenses_buildings.append(b)

    for b in data.get('buildings2', []):
        d_val = str(b.get('data'))
        if d_val == '1000064':
            has_bob = True

    # Procesar todo individualmente pasando el th_level
    defenses_res, d_time = process_category(defenses_buildings, master_db, th_level)
    army_res, a_time = process_category(army_buildings, master_db, th_level)
    resources_res, r_time = process_category(resources_buildings, master_db, th_level)
    
    traps_res, t_time = process_category(data.get('traps', []), master_db, th_level)
    
    units_res, u_time = process_category(data.get('units', []), master_db, th_level)
    spells_res, s_time = process_category(data.get('spells', []), master_db, th_level)
    siege_res, sm_time = process_category(data.get('siege_machines', []), master_db, th_level)
    
    heroes_res, h_time = process_category(data.get('heroes', []), master_db, th_level, hh_level=hh_level)
    pets_res, p_time = process_category(data.get('pets', []), master_db, th_level, ph_level=ph_level)
    equip_res, e_time = process_category(data.get('equipment', []), master_db, th_level)
    
    # Sumas de las categorías padre
    total_defenses = d_time
    total_army = a_time
    total_resources = r_time
    total_traps = t_time
    total_laboratory = u_time + s_time + sm_time
    total_heroes = h_time + e_time
    total_pets = p_time
    
    # Calculo especial de tiempo de constructores
    # Incluye: Defensas, Ejército, Recursos, Trampas, Héroes
    total_builders_work = total_defenses + total_army + total_resources + total_traps + total_heroes
    num_builders = 6 if has_bob else 5
    builders_time = total_builders_work / num_builders
    
    return jsonify({
        'status': 'success',
        'has_bob_hut': has_bob,
        'data': {
            'defenses': defenses_res,
            'army': army_res,
            'resources': resources_res,
            'traps': traps_res,
            'units_elixir': [u for u in units_res if u.get('currency') == 'elixir'],
            'units_dark': [u for u in units_res if u.get('currency') == 'dark_elixir'],
            'spells_elixir': [s for s in spells_res if s.get('currency') == 'elixir'],
            'spells_dark': [s for s in spells_res if s.get('currency') == 'dark_elixir'],
            'siege_machines': siege_res,
            'heroes': heroes_res,
            'pets': pets_res,
            'equipment': equip_res,
            'totals': {
                'builders_time': builders_time,
                'laboratory_time': total_laboratory,
                'pets_time': total_pets,
                'defenses_time': total_defenses,
                'army_time': total_army,
                'resources_time': total_resources,
                'traps_time': total_traps,
                'heroes_time': total_heroes
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
