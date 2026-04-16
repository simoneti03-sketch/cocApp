import json
import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ============================================================
# Configuración y Rutas de Datos
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
STATIC_DATA_DIR = os.path.join(os.path.dirname(__file__), 'static', 'data')
MAPPING_PATH = os.path.join(STATIC_DATA_DIR, "mapping_id_to_name.json")
TRANSLATIONS_PATH = os.path.join(STATIC_DATA_DIR, "translations.json")
MIN_REQUIREMENTS_PATH = os.path.join(STATIC_DATA_DIR, "min_levels_per_th.json")
MAX_TH = 18

def _compute_max_level_per_th(levels, maps, max_th=MAX_TH):
    result = [0] * max_th
    for entry in levels:
        th = entry.get("TH")
        lvl = entry.get("level", 0)
        
        # Resolver TH desde otros requisitos si TH no está presente
        if th is None:
            if "LL" in entry: th = maps['LL'].get(entry["LL"])
            elif "HH" in entry: th = maps['HH'].get(entry["HH"])
            elif "PH" in entry: th = maps['PH'].get(entry["PH"])
        
        if th is None: th = 1
        th = max(1, th)

        if th <= max_th:
            for i in range(th - 1, max_th):
                if lvl > result[i]:
                    result[i] = lvl
    return result

def _load_game_data():
    master_db = {}
    
    # Pre-cargar mapas de resolución de TH para requisitos indirectos
    def _get_lvl_map(rel_path):
        p = os.path.join(DATA_DIR, rel_path)
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {e.get('level'): e.get('TH') for e in data if 'level' in e and 'TH' in e}
            except: return {}
        return {}

    resolution_maps = {
        'LL': _get_lvl_map('army/Laboratory.json'),
        'HH': _get_lvl_map('army/HeroHall.json'),
        'PH': _get_lvl_map('army/PetHouse.json')
    }

    mapping = {}
    if os.path.exists(MAPPING_PATH):
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            
    translations = {}
    if os.path.exists(TRANSLATIONS_PATH):
        with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
            translations = json.load(f)

    # Procesar todo desde el mapeo
    for rel_path, item_metadata in mapping.items():
        if not isinstance(item_metadata, list) or len(item_metadata) < 2:
            continue
            
        item_id, eng_name = item_metadata[0], item_metadata[1]
        item_id = str(item_id)
        translated_name = translations.get(eng_name, eng_name)
        
        file_path = os.path.join(DATA_DIR, rel_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                raw_info = json.load(f)
            
            levels = raw_info or []
            levels.sort(key=lambda x: x.get("level", 0))
            
            curr = levels[0].get("currency", "gold") if levels else "gold"
            if curr in ["darkelixir", "dark-elixir"]: curr = "dark_elixir"
            
            entry = {
                "id": item_id,
                "name": translated_name,
                "english_name": eng_name,
                "upgrade_times": [e.get("duration", 0) for e in levels],
                "price_per_lvl": [e.get("cost", 0) for e in levels],
                "currency": curr,
                "category": rel_path.split('/')[0],
                "max_level_per_th": _compute_max_level_per_th(levels, resolution_maps)
            }
            master_db[item_id] = entry
    return master_db

# Cargar base de datos maestra
game_data = _load_game_data()

# Cargar requisitos mínimos
min_requirements_db = {}
if os.path.exists(MIN_REQUIREMENTS_PATH):
    with open(MIN_REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
        min_requirements_db = json.load(f)

def calculate_min_requirements_gap(current_state_by_eng, th_level, master_db):
    th_key = f"TH{th_level}"
    requirements = min_requirements_db.get(th_key, {})
    if not requirements: return []

    gap = []
    name_to_id = {info['english_name']: tid for tid, info in master_db.items()}

    for eng_name, req in requirements.items():
        if eng_name == "Town Hall":
            continue
            
        req_count = req['count']
        req_level = req['level']
        
        user_info = current_state_by_eng.get(eng_name, {'count': 0, 'levels': []})
        user_levels = sorted(user_info['levels'], reverse=True)
        
        missing_count = max(0, req_count - len(user_levels))
        
        tid = name_to_id.get(eng_name)
        if not tid: continue
        
        ref = master_db[tid]
        prices = ref['price_per_lvl']
        times = ref['upgrade_times']
        
        m_cost = 0; m_time = 0
        # Faltan por construir
        for _ in range(missing_count):
            for l in range(1, req_level + 1):
                idx = l - 1
                if idx < len(prices): m_cost += prices[idx]
                if idx < len(times): m_time += times[idx]
        
        # Faltan por subir nivel
        for i in range(min(len(user_levels), req_count)):
            curl = user_levels[i]
            if curl < req_level:
                for l in range(curl + 1, req_level + 1):
                    idx = l - 1
                    if idx < len(prices): m_cost += prices[idx]
                    if idx < len(times): m_time += times[idx]
                    
        if m_cost > 0 or m_time > 0 or missing_count > 0:
            gap.append({
                'name': ref['name'],
                'english_name': eng_name,
                'item_id': tid,
                'requirement': f"{req_count} x Niv.{req_level}",
                'missing_count': missing_count,
                'total_cost': m_cost,
                'total_time': m_time,
                'currency': ref['currency']
            })
    return gap

def process_category(items, db, th_level):
    processed = {}; total_time_rem = 0; total_u = 0; done_u = 0
    total_time_done = 0; total_time_max = 0
    
    for item in items:
        tid = str(item.get('id', item.get('data', '')))
        ref = db.get(tid)
        if not ref: continue
        
        clvl = int(item.get('lvl', item.get('level', 0)))
        tleft = int(item.get('timer', item.get('timeLeft', 0)))
        cnt = int(item.get('cnt', 1))
        
        max_list = ref.get('max_level_per_th', [])
        mlvl = max_list[th_level-1] if len(max_list) >= th_level else (max_list[-1] if max_list else clvl)
        min_lvl = max_list[th_level-2] if th_level > 1 and len(max_list) >= th_level-1 else 0

        total_u += max(0, mlvl - min_lvl) * cnt
        done_u += (min(clvl, mlvl) - min_lvl) * cnt
        
        durations = ref.get('upgrade_times', [])
        
        # Global time progress for this TH max level
        item_max_time = sum(durations[:mlvl])
        item_done_time = sum(durations[:clvl])
        if tleft > 0 and clvl < mlvl:
            dur_next = durations[clvl] if clvl < len(durations) else 0
            item_done_time += max(0, dur_next - tleft)
        
        item_done_time = min(item_done_time, item_max_time)
        
        total_time_done += item_done_time * cnt
        total_time_max += item_max_time * cnt
        
        # Remaining time for active/pending upgrades
        i_time = 0; i_cost = 0
        if clvl < mlvl:
            if tleft > 0:
                i_time = tleft
                for l in range(clvl + 2, mlvl + 1):
                    idx = l-1
                    if idx < len(durations): i_time += durations[idx]
                    if idx < len(ref['price_per_lvl']): i_cost += ref['price_per_lvl'][idx]
            else:
                for l in range(clvl + 1, mlvl + 1):
                    idx = l-1
                    if idx < len(durations): i_time += durations[idx]
                    if idx < len(ref['price_per_lvl']): i_cost += ref['price_per_lvl'][idx]
        
        total_time_rem += i_time * cnt
        
        if tid not in processed:
            processed[tid] = {
                'id': tid, 'name': ref['name'], 'max_lvl': mlvl, 'currency': ref['currency'],
                'total_cnt': 0, 'is_fully_maxed': True, 'is_unlocked': False, 'total_time_to_max': 0, 'total_cost_to_max': 0,
                'time_done': 0, 'time_max': 0,
                'progress_sum': 0, 'instances': []
            }
        
        g = processed[tid]
        g['total_cnt'] += cnt
        g['total_time_to_max'] += i_time * cnt
        g['total_cost_to_max'] += i_cost * cnt
        g['time_done'] += item_done_time * cnt
        g['time_max'] += item_max_time * cnt
        if clvl < mlvl: g['is_fully_maxed'] = False
        if clvl > 0: g['is_unlocked'] = True
        
        g['instances'].append({
            'cnt': cnt, 'current_lvl': clvl, 'is_maxed': (clvl >= mlvl), 'is_upgrading': (tleft > 0),
            'time_left': tleft, 'time_to_max': i_time, 'cost_to_max': i_cost,
            'weapon': int(item.get('weapon', 0)), 'gear_up': int(item.get('gear_up', 0))
        })
        
    res_list = list(processed.values())
    for g in res_list:
        # Use time-based percentage for the group card
        g['progress_percentage'] = (g['time_done'] / g['time_max'] * 100) if g['time_max'] > 0 else 100
        
    return res_list, total_time_rem, total_u, done_u, total_time_done, total_time_max


@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_village():
    data = request.json
    if not data: return jsonify({'error': 'No data'}), 400
    
    th_level = 1; has_bob = False
    groups = {'defenses': [], 'army': [], 'resources': [], 'traps': [], 'heroes': []}
    
    for b in data.get('buildings', []):
        tid = str(b.get('data', ''))
        if tid == '1000001': th_level = int(b.get('lvl', 1))
        if tid == '1000064': has_bob = True
        
        ref = game_data.get(tid)
        if not ref: continue
        cat = ref['category']
        if tid == '1000001': groups['defenses'].append(b)
        elif tid in ['1000071', '1000068']: groups['army'].append(b)
        elif cat in groups: groups[cat].append(b)
        else: groups['defenses'].append(b)

    for b in data.get('buildings2', []):
        if str(b.get('data')) == '1000064': has_bob = True

    def_res, d_t, d_tot, d_don, d_dt, d_mt = process_category(groups['defenses'], game_data, th_level)
    arm_res, a_t, a_tot, a_don, a_dt, a_mt = process_category(groups['army'], game_data, th_level)
    res_res, r_t, r_tot, r_don, r_dt, r_mt = process_category(groups['resources'], game_data, th_level)
    trp_res, t_t, t_tot, t_don, t_dt, t_mt = process_category(data.get('traps', []), game_data, th_level)
    
    # Complementar con items no desbloqueados que deberían estar disponibles
    def _supplement_missing(items, cat_name):
        existing = {str(it.get('data', it.get('id', ''))) for it in items}
        for tid, ref in game_data.items():
            if ref['category'] == cat_name:
                max_list = ref.get('max_level_per_th', [])
                # mlvl actual
                mlvl = max_list[th_level-1] if len(max_list) >= th_level else 0
                
                # Si está disponible en este nivel y no lo tiene, se añade
                if mlvl > 0 and tid not in existing:
                    items.append({'id': tid, 'lvl': 0, 'cnt': 1})
        return items

    units_list = _supplement_missing(data.get('units', []), 'units')
    spells_list = _supplement_missing(data.get('spells', []), 'spells')
    siege_list = _supplement_missing(data.get('siege_machines', []), 'siege')
    heroes_list = _supplement_missing(data.get('heroes', []), 'heroes')
    pets_list = _supplement_missing(data.get('pets', []), 'pets')

    uni_res, u_t, u_tot, u_don, u_dt, u_mt = process_category(units_list, game_data, th_level)
    spl_res, s_t, s_tot, s_don, s_dt, s_mt = process_category(spells_list, game_data, th_level)
    sge_res, sm_t, sm_tot, sm_don, sm_dt, sm_mt = process_category(siege_list, game_data, th_level)
    
    hro_res, h_t, h_tot, h_don, h_dt, h_mt = process_category(heroes_list, game_data, th_level)
    pet_res, p_t, p_tot, p_don, p_dt, p_mt = process_category(pets_list, game_data, th_level)
    eqp_res, e_t, e_tot, e_don, e_dt, e_mt = process_category(data.get('equipment', []), game_data, th_level)

    village_state = {}
    def _collect(items):
        for it in items:
            tid = str(it.get('data', it.get('id', '')))
            ref = game_data.get(tid)
            if not ref: continue
            ename = ref['english_name']
            if ename not in village_state: village_state[ename] = {'count': 0, 'levels': []}
            cnt = int(it.get('cnt', 1))
            village_state[ename]['count'] += cnt
            for _ in range(cnt): village_state[ename]['levels'].append(int(it.get('lvl', it.get('level', 0))))

    _collect(groups['defenses'] + groups['army'] + groups['resources'])
    _collect(data.get('traps', []))
    _collect(data.get('heroes', []))

    gap = calculate_min_requirements_gap(village_state, th_level, game_data)
    gap_time = sum(i['total_time'] for i in gap)
    gap_costs = {}
    for i in gap: gap_costs[i['currency']] = gap_costs.get(i['currency'], 0) + i['total_cost']

    num_builders = 0
    for b in data.get('buildings', []):
        if str(b.get('data')) == '1000015': num_builders += int(b.get('cnt', 1))

    num_b = max(1, num_builders + (1 if has_bob else 0))
    total_b_work = d_t + a_t + r_t + t_t + h_t + e_t
    
    def _agg_cost(lists):
        c = {}
        for l in lists:
            for item in l:
                curr = item['currency']
                c[curr] = c.get(curr, 0) + item['total_cost_to_max']
        return c

    return jsonify({
        'status': 'success', 'has_bob_hut': has_bob,
        'data': {
            'defenses': def_res, 'army': arm_res, 'resources': res_res, 'traps': trp_res,
            'units_elixir': [x for x in uni_res if x['currency'] == 'elixir'],
            'units_dark': [x for x in uni_res if x['currency'] == 'dark_elixir'],
            'spells_elixir': [x for x in spl_res if x['currency'] == 'elixir'],
            'spells_dark': [x for x in spl_res if x['currency'] == 'dark_elixir'],
            'siege_machines': sge_res, 'heroes': hro_res, 'pets': pet_res, 'equipment': eqp_res,
            'min_requirements_gap': gap,
            'totals': {
                'builders_time': total_b_work / num_b,
                'laboratory_time': u_t + s_t + sm_t,
                'pets_time': p_t,
                'defenses_time': d_t / num_b, 'army_time': a_t / num_b, 'resources_time': r_t / num_b, 'traps_time': t_t / num_b, 'heroes_time': (h_t + e_t) / num_b,
                'builder_costs': _agg_cost([def_res, arm_res, res_res, trp_res, hro_res, eqp_res]),
                'lab_costs': _agg_cost([uni_res, spl_res, sge_res]),
                'pet_costs': _agg_cost([pet_res]),
                'min_requirements_total_time': gap_time,
                'min_requirements_total_costs': gap_costs,
                'upgrades': {
                    'builders': {
                        'total': d_tot+a_tot+r_tot+t_tot+h_tot+e_tot, 
                        'done': d_don+a_don+r_don+t_don+h_don+e_don,
                        'total_time': d_mt+a_mt+r_mt+t_mt+h_mt+e_mt,
                        'done_time': d_dt+a_dt+r_dt+t_dt+h_dt+e_dt
                    },
                    'lab': {
                        'total': u_tot+s_tot+sm_tot, 
                        'done': u_don+s_don+sm_don,
                        'total_time': u_mt+s_mt+sm_mt,
                        'done_time': u_dt+s_dt+sm_dt
                    },
                    'pets': {
                        'total': p_tot, 
                        'done': p_don,
                        'total_time': p_mt,
                        'done_time': p_dt
                    },
                    'defenses': {
                        'total': d_tot, 
                        'done': d_don,
                        'total_time': d_mt,
                        'done_time': d_dt
                    },
                    'army': {
                        'total': a_tot, 
                        'done': a_don,
                        'total_time': a_mt,
                        'done_time': a_dt
                    },
                    'resources': {
                        'total': r_tot, 
                        'done': r_don,
                        'total_time': r_mt,
                        'done_time': r_dt
                    },
                    'traps': {
                        'total': t_tot, 
                        'done': t_don,
                        'total_time': t_mt,
                        'done_time': t_dt
                    },
                    'heroes': {
                        'total': h_tot, 
                        'done': h_don,
                        'total_time': h_mt+e_mt,
                        'done_time': h_dt+e_dt
                    }
                }
            }
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
