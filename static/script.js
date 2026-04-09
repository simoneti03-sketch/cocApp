document.addEventListener('DOMContentLoaded', () => {
    const pasteBtn = document.getElementById('pasteDataBtn');
    const loader = document.getElementById('loader');
    const pasteError = document.getElementById('pasteError');
    const dashboardContent = document.getElementById('dashboardContent');
    const toggleRemaining = document.getElementById('toggleRemainingOnly');
    const villageSelector = document.getElementById('villageSelector');
    const villageSelectorContainer = document.getElementById('villageSelectorContainer');
    const addNewVillageBtn = document.getElementById('addNewVillageBtn');
    const updateVillageBtn = document.getElementById('updateVillageBtn');
    const deleteVillageBtn = document.getElementById('deleteVillageBtn');
    const expandAllBtn = document.getElementById('expandAllBtn');

    let state = {
        activeId: null,
        villages: {}
    };

    let isRemainingOnly = false;
    let isAllExpanded = false;

    function formatTime(seconds) {
        if (seconds <= 0) return 'Maxed!';
        const d = Math.floor(seconds / (3600 * 24));
        const h = Math.floor(seconds % (3600 * 24) / 3600);
        const m = Math.floor(seconds % 3600 / 60);

        let parts = [];
        if (d > 0) parts.push(`${d}d`);
        if (h > 0) parts.push(`${h}h`);
        if (m > 0) parts.push(`${m}m`);
        if (parts.length === 0) return '< 1m';
        return parts.join(' ');
    }

    const BUILDING_IMAGE_MAP = {
        // [Defences]
        '1000001': { cat: 'Defences', folder: 'TownHall', prefix: 'Town_Hall' },
        '1000008': { cat: 'Defences', folder: 'Cannon', prefix: 'Cannon', isComplexExt: true },
        '1000009': { cat: 'Defences', folder: 'ArcherTower', prefix: 'Archer_Tower' },
        '1000010': { cat: 'Defences', folder: 'Wall', prefix: 'Wall' },
        '1000011': { cat: 'Defences', folder: 'WizardTower', prefix: 'Wizard_Tower' },
        '1000012': { cat: 'Defences', folder: 'AirDefense', prefix: 'Air_Defense' },
        '1000013': { cat: 'Defences', folder: 'Mortar', prefix: 'Mortar', isComplexExt: true },
        '1000015': { cat: 'Defences', folder: 'BuilderHut', prefix: 'Builders_Hut', noLevelOne: true },
        '1000019': { cat: 'Defences', folder: 'HiddenTesla', prefix: 'Hidden_Tesla' },
        '1000021': { cat: 'Defences', folder: 'X-Bow', prefix: 'X-Bow', suffix: '_Ground' },
        '1000027': { cat: 'Defences', folder: 'InfernoTower', prefix: 'Inferno_Tower', suffix: '_Single' },
        '1000028': { cat: 'Defences', folder: 'AirSweeper', prefix: 'Air_Sweeper' },
        '1000031': { cat: 'Defences', folder: 'EagleArtillery', prefix: 'Eagle_Artillery' },
        '1000032': { cat: 'Defences', folder: 'BombTower', prefix: 'Bomb_Tower' },
        '1000067': { cat: 'Defences', folder: 'Scattershot', prefix: 'Scattershot' },
        '1000072': {
            cat: 'Defences', folder: 'SpellTower', prefix: 'Spell_Tower', dynamicSuffix: (lvl) => {
                const spells = { 1: '_Rage', 2: '_Poison', 3: '_Invisibility', 4: '_Earthquake' };
                return spells[lvl] || '';
            }
        },
        '1000077': { cat: 'Defences', folder: 'Monolith', prefix: 'Monolith' },

        // [Army]
        '1000000': { cat: 'Army', folder: 'ArmyCamp', prefix: 'Army_Camp' },
        '1000006': { cat: 'Army', folder: 'Barracks', prefix: 'Barracks' },
        '1000007': { cat: 'Army', folder: 'Laboratory', prefix: 'Laboratory' },
        '1000020': { cat: 'Army', folder: 'SpellFactory', prefix: 'Spell_Factory' },
        '1000026': { cat: 'Army', folder: 'DarkBarracks', prefix: 'Dark_Barracks' },
        '1000029': { cat: 'Army', folder: 'DarkSpellFactory', prefix: 'Dark_Spell_Factory' },
        '1000059': { cat: 'Army', folder: 'Workshop', prefix: 'Workshop' },
        '1000068': { cat: 'Army', folder: 'PetsHut', prefix: 'Pet_House' },
        '1000070': { cat: 'Army', folder: 'Blacksmith', prefix: 'Blacksmith' },
        '1000071': { cat: 'Army', folder: 'HeroHall', prefix: 'Hero_Hall' },

        // [Resources]
        '1000002': { cat: 'Resources', folder: 'GoldMine', prefix: 'Gold_Mine' },
        '1000003': { cat: 'Resources', folder: 'GoldStorage', prefix: 'Gold_Storage' },
        '1000004': { cat: 'Resources', folder: 'ElixirColector', prefix: 'Elixir_Collector' },
        '1000005': { cat: 'Resources', folder: 'ElixirStorage', prefix: 'Elixir_Storage' },
        '1000014': { cat: 'Resources', folder: 'ClanCastle', prefix: 'Clan_Castle' },
        '1000016': { cat: 'Resources', folder: 'DarkElixirDrill', prefix: 'Dark_Elixir_Drill' },
        '1000017': { cat: 'Resources', folder: 'DarkElixirStorage', prefix: 'Dark_Elixir_Storage' },

        // [Traps]
        '12000000': { cat: 'Traps', folder: 'Bomb',           prefix: 'Bomb' },
        '12000001': { cat: 'Traps', folder: 'SpringTrap',     prefix: 'Spring_Trap' },
        '12000002': { cat: 'Traps', folder: 'GiantBomb',      prefix: 'Giant_Bomb' },
        '12000005': { cat: 'Traps', folder: 'AirBomb',        prefix: 'Air_Bomb' },
        '12000006': { cat: 'Traps', folder: 'SeekingAirMine', prefix: 'Seeking_Air_Mine' },
        '12000008': { cat: 'Traps', folder: 'SkeletonTrap',   prefix: 'SkeletonTrap',     suffix: '_Ground' },
        '12000016': { cat: 'Traps', folder: 'TornadoTrap',    prefix: 'Tornado_Trap' },
        '12000020': { cat: 'Traps', folder: 'GigaBomb',       prefix: 'Giga_Bomb' }
    };

    const LABORATORY_IMAGE_MAP = {
        // [Units - Elixir]
        '4000000': { cat: 'Units/Elixir', prefix: 'Avatar_Barbarian' },
        '4000001': { cat: 'Units/Elixir', prefix: 'Avatar_Archer' },
        '4000002': { cat: 'Units/Elixir', prefix: 'Avatar_Goblin' },
        '4000003': { cat: 'Units/Elixir', prefix: 'Avatar_Giant' },
        '4000004': { cat: 'Units/Elixir', prefix: 'Avatar_Wall_Breaker' },
        '4000005': { cat: 'Units/Elixir', prefix: 'Avatar_Balloon' },
        '4000006': { cat: 'Units/Elixir', prefix: 'Avatar_Wizard' },
        '4000007': { cat: 'Units/Elixir', prefix: 'Avatar_Healer' },
        '4000008': { cat: 'Units/Elixir', prefix: 'Avatar_Dragon' },
        '4000009': { cat: 'Units/Elixir', prefix: 'Avatar_P.E.K.K.A' },
        '4000023': { cat: 'Units/Elixir', prefix: 'Avatar_Baby_Dragon' },
        '4000024': { cat: 'Units/Elixir', prefix: 'Avatar_Miner' },
        '4000053': { cat: 'Units/Elixir', prefix: 'Avatar_Yeti' },
        '4000059': { cat: 'Units/Elixir', prefix: 'Avatar_Electro_Dragon' },
        '4000065': { cat: 'Units/Elixir', prefix: 'Avatar_Dragon_Rider' },
        '4000095': { cat: 'Units/Elixir', prefix: 'Avatar_Electro_Titan' },
        '4000110': { cat: 'Units/Elixir', prefix: 'Avatar_Root_Rider' },
        '4000132': { cat: 'Units/Elixir', prefix: 'Avatar_Thrower' },
        '4000155': { cat: 'Units/Elixir', prefix: 'Avatar_Meteor_Golem' },

        // [Units - Dark]
        '4000010': { cat: 'Units/Dark', prefix: 'Avatar_Minion' },
        '4000011': { cat: 'Units/Dark', prefix: 'Avatar_Hog_Rider' },
        '4000012': { cat: 'Units/Dark', prefix: 'Avatar_Valkyrie' },
        '4000013': { cat: 'Units/Dark', prefix: 'Avatar_Golem' },
        '4000015': { cat: 'Units/Dark', prefix: 'Avatar_Witch' },
        '4000017': { cat: 'Units/Dark', prefix: 'Avatar_Lava_Hound' },
        '4000022': { cat: 'Units/Dark', prefix: 'Avatar_Bowler' },
        '4000058': { cat: 'Units/Dark', prefix: 'Avatar_Ice_Golem' },
        '4000082': { cat: 'Units/Dark', prefix: 'Avatar_Headhunter' },
        '4000097': { cat: 'Units/Dark', prefix: 'Avatar_Apprentice_Warden' },
        '4000123': { cat: 'Units/Dark', prefix: 'Avatar_Druid' },
        '4000150': { cat: 'Units/Dark', prefix: 'Avatar_Furnace' },

        // [Spells - Elixir]
        '26000000': { cat: 'Spells/Elixir', prefix: 'Lightning_Spell', suffix: '_info' },
        '26000001': { cat: 'Spells/Elixir', prefix: 'Healing_Spell',   suffix: '_info' },
        '26000002': { cat: 'Spells/Elixir', prefix: 'Rage_Spell',      suffix: '_info' },
        '26000003': { cat: 'Spells/Elixir', prefix: 'Jump_Spell',      suffix: '_info' },
        '26000005': { cat: 'Spells/Elixir', prefix: 'Freeze_Spell',    suffix: '_info' },
        '26000016': { cat: 'Spells/Elixir', prefix: 'Clone_Spell',     suffix: '_info' },
        '26000035': { cat: 'Spells/Elixir', prefix: 'Invisibility_Spell', suffix: '_info' },
        '26000053': { cat: 'Spells/Elixir', prefix: 'Recall_Spell',    suffix: '_info' },
        '26000098': { cat: 'Spells/Elixir', prefix: 'Revive_Spell',    suffix: '_info' },
        '26000114': { cat: 'Spells/Elixir', prefix: 'Totem_Spell',     suffix: '_info' },

        // [Spells - Dark]
        '26000009': { cat: 'Spells/Dark', prefix: 'Poison_Spell',     suffix: '_info' },
        '26000010': { cat: 'Spells/Dark', prefix: 'Earthquake_Spell', suffix: '_info' },
        '26000011': { cat: 'Spells/Dark', prefix: 'Haste_Spell',      suffix: '_info' },
        '26000017': { cat: 'Spells/Dark', prefix: 'Skeleton_Spell',   suffix: '_info' },
        '26000028': { cat: 'Spells/Dark', prefix: 'Bat_Spell',        suffix: '_info' },
        '26000070': { cat: 'Spells/Dark', prefix: 'Overgrowth_Spell', suffix: '_info' },
        '26000109': { cat: 'Spells/Dark', prefix: 'Ice_Block_Spell',  suffix: '_info' },

        // [Siege Machines]
        '4000051': { cat: 'SiegeMachines', prefix: 'Avatar_Wall_Wrecker' },
        '4000052': { cat: 'SiegeMachines', prefix: 'Avatar_Battle_Blimp' },
        '4000062': { cat: 'SiegeMachines', prefix: 'Avatar_Stone_Slammer' },
        '4000075': { cat: 'SiegeMachines', prefix: 'Avatar_Siege_Barracks' },
        '4000087': { cat: 'SiegeMachines', prefix: 'Avatar_Log_Launcher' },
        '4000091': { cat: 'SiegeMachines', prefix: 'Avatar_Flame_Flinger' },
        '4000092': { cat: 'SiegeMachines', prefix: 'Avatar_Battle_Drill' },
        '4000135': { cat: 'SiegeMachines', prefix: 'Avatar_Troop_Launcher' },

        // [Pets]
        '73000000': { cat: 'Pets', prefix: 'Avatar_L.A.S.S.I' },
        '73000001': { cat: 'Pets', prefix: 'Avatar_Electro_Owl' },
        '73000002': { cat: 'Pets', prefix: 'Avatar_Mighty_Yak' },
        '73000003': { cat: 'Pets', prefix: 'Avatar_Unicorn' },
        '73000004': { cat: 'Pets', prefix: 'Avatar_Phoenix' },
        '73000007': { cat: 'Pets', prefix: 'Avatar_Poison_Lizard' },
        '73000008': { cat: 'Pets', prefix: 'Avatar_Diggy' },
        '73000009': { cat: 'Pets', prefix: 'Avatar_Frosty' },
        '73000010': { cat: 'Pets', prefix: 'Avatar_Spirit_Fox' },
        '73000011': { cat: 'Pets', prefix: 'Avatar_Angry_Jelly' },
        '73000016': { cat: 'Pets', prefix: 'Avatar_Sneezy' },
        '73000017': { cat: 'Pets', prefix: 'Avatar_Greedy_Raven' }
    };

    function getItemImage(group, level) {
        // 1. Buscar en Edificios (tienen niveles individuales)
        let config = BUILDING_IMAGE_MAP[group.id];
        if (config) {
            let ext = '.webp';
            if (config.isComplexExt && level >= 8) ext = '.wep.webp';
            const displayLevel = (config.noLevelOne && level === 1) ? '' : level;
            const sfx = config.dynamicSuffix ? config.dynamicSuffix(level) : (config.suffix || '');
            return `/static/images/${config.cat}/${config.folder}/${config.prefix}${displayLevel}${sfx}${ext}`;
        }

        // 2. Buscar en Laboratorio/Mascotas (son imágenes estáticas)
        config = LABORATORY_IMAGE_MAP[group.id];
        if (config) {
            const sfx = config.suffix || '';
            const ext = '.webp';
            return `/static/images/${config.cat}/${config.prefix}${sfx}${ext}`;
        }

        return null;
    }

    function createAccordion(group, iconClass) {
        let isMax = group.is_fully_maxed;
        let pColor = isMax ? 'bg-info' : '';
        let bClass = isMax ? 'border-info' : 'border-0';
        let statusText = isMax ? `Máximos para Ayuntamiento` : `Queda: ${formatTime(group.total_time_to_max)}`;
        let accId = 'acc-' + group.id;

        let headerWidth = group.progress_percentage;
        let hasDropdown = group.total_cnt > 1;

        // Render instances (only relevant if it has a dropdown)
        let instancesHtml = '';
        if (hasDropdown) {
            group.instances.forEach((inst, idx) => {
                let instMax = inst.is_maxed && !inst.is_upgrading;
                let instText = instMax ? 'Al Máximo' : (inst.is_upgrading ? `Mejorando a Lvl ${inst.current_lvl + 1}` : `Quedan ${formatTime(inst.time_to_max)}`);
                let instColor = instMax ? 'text-info fw-bold' : (inst.is_upgrading ? 'text-warning' : 'text-secondary');

                let itemImg = getItemImage(group, inst.current_lvl);
                let imgHtml = itemImg ? `<img src="${itemImg}" class="me-2 rounded shadow-sm" style="width:50px; height:50px; object-fit:contain; background: rgba(0,0,0,0.1);">` : '';

                let extraTags = '';
                if (inst.weapon > 0) extraTags += ` <span class="badge bg-danger ms-1" style="font-size: 0.70rem;">Arma ${inst.weapon}</span>`;
                if (inst.gear_up > 0) extraTags += ` <span class="badge bg-primary ms-1" style="font-size: 0.70rem;"><i class="bi bi-gear-wide-connected me-1"></i>Perfeccionada</span>`;

                instancesHtml += `
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary mb-1 flex-wrap">
                        <div class="d-flex align-items-center mb-1 mb-sm-0">
                            ${imgHtml}
                            <span class="badge bg-secondary me-2">x${inst.cnt}</span>
                            <span>Nivel ${inst.current_lvl}</span>${extraTags}
                        </div>
                        <span class="fs-6 ${instColor}" style="font-size: 0.85rem !important;">${instText}</span>
                    </div>
                `;
            });
        }

        let extraTagsTop = '';
        if (!hasDropdown) {
            if (group.instances[0].weapon > 0) extraTagsTop += ` <span class="badge bg-danger ms-1">Arma ${group.instances[0].weapon}</span>`;
            if (group.instances[0].gear_up > 0) extraTagsTop += ` <span class="badge bg-primary ms-1" title="Defensa perfeccionada"><i class="bi bi-gear-wide-connected"></i> Perf.</span>`;
        }

        let topBadgeHtml = hasDropdown
            ? `<span class="badge bg-secondary">Total: ${group.total_cnt}</span>`
            : `<span class="level-badge small">Lvl ${group.instances[0].current_lvl} / ${group.max_lvl}${extraTagsTop}</span>`;

        let statusRowHtml = '';
        if (hasDropdown) {
            statusRowHtml = `
                <div class="d-flex justify-content-between align-items-center time-text mt-1 mx-1 mb-2">
                    <span class="${isMax ? 'text-info fw-bold' : ''}">${statusText}</span>
                    <button class="btn btn-sm btn-outline-secondary text-light p-1 px-2 collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${accId}" aria-expanded="false" aria-controls="${accId}" style="font-size: 0.75rem;">
                        Desplegar <i class="bi bi-chevron-down ms-1"></i>
                    </button>
                </div>
            `;
        } else {
            let inst = group.instances[0];
            let instText = inst.is_maxed && !inst.is_upgrading ? `Máx. para Ayuntamiento` : (inst.is_upgrading ? `Mejorando a Lvl ${inst.current_lvl + 1}` : `Queda: ${formatTime(inst.time_to_max)}`);
            let instColor = inst.is_maxed && !inst.is_upgrading ? 'text-info fw-bold' : (inst.is_upgrading ? 'text-warning' : '');
            statusRowHtml = `
                <div class="d-flex justify-content-between align-items-center time-text mt-1 mx-1 mb-2">
                    <span>Estado:</span>
                    <span class="${instColor}">${instText}</span>
                </div>
            `;
        }

        let dropdownHtml = hasDropdown ? `
            <div id="${accId}" class="accordion-collapse collapse" aria-labelledby="heading-${accId}" data-bs-parent="#${accId}-parent">
                <div class="accordion-body pt-0 px-3 pb-3">
                    ${instancesHtml}
                </div>
            </div>
        ` : '';

        let mainImg = !hasDropdown ? getItemImage(group, group.instances[0].current_lvl) : null;
        let mainImgHtml = mainImg ? `<div class="text-center mb-2"><img src="${mainImg}" class="rounded shadow-sm" style="width:50px; height:50px; object-fit:contain; background: rgba(0,0,0,0.1);"></div>` : '';

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card bg-dark glass-card item-card h-100 ${bClass} shadow-sm overflow-hidden ${hasDropdown ? 'accordion' : ''}" id="${accId}-parent">
                    <div class="card-body p-0">
                        <div class="accordion-item bg-transparent border-0">
                            <h2 class="accordion-header p-3 pb-0" id="heading-${accId}">
                                ${mainImgHtml}
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <div class="d-flex align-items-center gap-2">
                                        <i class="${iconClass} fs-4 text-warning"></i>
                                        <span class="item-title">${group.name}</span>
                                    </div>
                                    ${topBadgeHtml}
                                </div>
                                
                                <div class="progress-dark mb-2 mx-1" style="height: 6px;">
                                    <div class="progress-bar progress-bar-custom ${pColor}" role="progressbar" style="width: ${headerWidth}%" aria-valuenow="${headerWidth}" aria-valuemin="0" aria-valuemax="100"></div>
                                </div>
                                
                                ${statusRowHtml}
                            </h2>
                            ${dropdownHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function renderSection(containerId, items, iconClass) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        let displayItems = items;
        if (isRemainingOnly) {
            displayItems = items.filter(group => !group.is_fully_maxed);
        }

        if (displayItems.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-secondary py-4"><i class="bi bi-inbox fs-1 d-block mb-2"></i>No hay mejoras pendientes en esta categoría.</div>';
            return;
        }

        displayItems.sort((a, b) => b.total_time_to_max - a.total_time_to_max);

        let html = '';
        displayItems.forEach(group => {
            html += createAccordion(group, iconClass);
        });
        container.innerHTML = html;
    }

    function renderAllSections(data) {
        // Render cards
        renderSection('defensesContainer', data.defenses, 'bi bi-shield');
        renderSection('armyContainer', data.army, 'bi bi-crosshair');
        renderSection('resourcesContainer', data.resources, 'bi bi-box-seam');

        renderSection('trapsContainer', data.traps, 'bi bi-x-octagon');
        renderSection('helpersContainer', data.helpers, 'bi bi-hammer');

        renderSection('unitsElixirContainer', data.units_elixir, 'bi bi-lightning-charge');
        renderSection('unitsDarkContainer', data.units_dark, 'bi bi-lightning-charge');
        renderSection('spellsElixirContainer', data.spells_elixir, 'bi bi-magic');
        renderSection('spellsDarkContainer', data.spells_dark, 'bi bi-magic');
        renderSection('siegeContainer', data.siege_machines, 'bi bi-truck');

        renderSection('heroesContainer', data.heroes, 'bi bi-person-bounding-box');
        renderSection('petsContainer', data.pets, 'bi bi-bug');
        renderSection('equipmentContainer', data.equipment, 'bi bi-shield-shaded');
    }

    function saveState() {
        localStorage.setItem('cocTrackerState', JSON.stringify(state));
    }

    function loadState() {
        const saved = localStorage.getItem('cocTrackerState');
        if (saved) {
            try {
                state = JSON.parse(saved);
                renderVillageSelector();
                if (state.activeId && state.villages[state.activeId]) {
                    displayVillage(state.activeId);
                }
            } catch (e) {
                console.error("Error loading state:", e);
            }
        }
    }

    function renderVillageSelector() {
        const ids = Object.keys(state.villages);
        if (ids.length === 0) {
            villageSelectorContainer.classList.add('d-none');
            return;
        }

        villageSelectorContainer.classList.remove('d-none');
        villageSelector.innerHTML = '';
        ids.forEach(id => {
            const v = state.villages[id];
            const option = document.createElement('option');
            option.value = id;
            option.textContent = v.name;
            option.selected = (id === state.activeId);
            villageSelector.appendChild(option);
        });
    }

    function displayVillage(id) {
        const v = state.villages[id];
        if (!v) return;

        state.activeId = id;
        const data = v.processed;

        const bobIcon = document.getElementById('bobHutIcon');
        if (v.hasBob) {
            bobIcon.className = 'bi bi-check-circle-fill text-success fs-5';
        } else {
            bobIcon.className = 'bi bi-x-circle-fill text-danger fs-5';
        }

        // Update totals
        document.getElementById('totalBuildersTime').textContent = formatTime(data.totals.builders_time);
        document.getElementById('totalUnitsTime').textContent = formatTime(data.totals.laboratory_time);
        document.getElementById('totalPetsTime').textContent = formatTime(data.totals.pets_time);

        document.getElementById('totalDefensesTime').textContent = formatTime(data.totals.defenses_time);
        document.getElementById('totalArmyTime').textContent = formatTime(data.totals.army_time);
        document.getElementById('totalResourcesTime').textContent = formatTime(data.totals.resources_time);
        document.getElementById('totalTrapsTime').textContent = formatTime(data.totals.traps_time);
        document.getElementById('totalHeroesTime').textContent = formatTime(data.totals.heroes_time);

        renderAllSections(data);

        // UI state
        dashboardContent.classList.remove('d-none');
        document.querySelector('.hero-section').classList.add('py-3');
        document.querySelector('.hero-section').classList.replace('mb-5', 'mb-3');
        document.querySelector('.hero-section h1').classList.replace('display-4', 'h3');
        document.querySelector('.hero-section p').classList.add('d-none');
        pasteBtn.classList.replace('btn-lg', 'btn-sm');
        pasteBtn.innerHTML = '<i class="bi bi-plus-lg"></i> Añadir otra aldea';
    }

    async function processAndSave(jsonData, isUpdate = false) {
        loader.classList.remove('d-none');
        pasteBtn.disabled = true;
        pasteError.classList.add('d-none');

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonData)
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                const id = isUpdate && state.activeId ? state.activeId : 'v-' + Date.now();
                const name = isUpdate && state.activeId ? state.villages[state.activeId].name : prompt("Nombre de la aldea:", "Mi Aldea") || "Aldea";

                state.villages[id] = {
                    id: id,
                    name: name,
                    raw: jsonData,
                    processed: result.data,
                    hasBob: result.has_bob_hut,
                    timestamp: Date.now()
                };
                state.activeId = id;

                saveState();
                renderVillageSelector();
                displayVillage(id);

                dashboardContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                throw new Error(result.error || 'Error procesando los datos.');
            }
        } catch (err) {
            console.error(err);
            pasteError.textContent = "Error: " + err.message;
            pasteError.classList.remove('d-none');
        } finally {
            loader.classList.add('d-none');
            pasteBtn.disabled = false;
        }
    }

    if (toggleRemaining) {
        toggleRemaining.addEventListener('click', () => {
            isRemainingOnly = !isRemainingOnly;

            if (isRemainingOnly) {
                toggleRemaining.classList.replace('btn-dark', 'btn-warning');
                toggleRemaining.classList.replace('text-secondary', 'text-dark');
            } else {
                toggleRemaining.classList.replace('btn-warning', 'btn-dark');
                toggleRemaining.classList.replace('text-dark', 'text-secondary');
            }

            if (state.activeId && state.villages[state.activeId]) {
                renderAllSections(state.villages[state.activeId].processed);
            }
        });
    }

    if (expandAllBtn) {
        expandAllBtn.addEventListener('click', () => {
            isAllExpanded = !isAllExpanded;
            const collapses = document.querySelectorAll('.accordion-collapse');

            collapses.forEach(el => {
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
                if (isAllExpanded) {
                    bsCollapse.show();
                } else {
                    bsCollapse.hide();
                }
            });

            // Visual feedback
            if (isAllExpanded) {
                expandAllBtn.classList.replace('btn-dark', 'btn-warning');
                expandAllBtn.classList.replace('text-secondary', 'text-dark');
                expandAllBtn.innerHTML = '<i class="bi bi-arrows-collapse"></i> Replegar todo';
            } else {
                expandAllBtn.classList.replace('btn-warning', 'btn-dark');
                expandAllBtn.classList.replace('text-dark', 'text-secondary');
                expandAllBtn.innerHTML = '<i class="bi bi-arrows-expand"></i> Desplegar todo';
            }
        });
    }

    villageSelector.addEventListener('change', (e) => {
        // Reset expand state on village switch
        isAllExpanded = false;
        if (expandAllBtn) {
            expandAllBtn.classList.replace('btn-warning', 'btn-dark');
            expandAllBtn.classList.replace('text-dark', 'text-secondary');
            expandAllBtn.innerHTML = '<i class="bi bi-arrows-expand"></i> Desplegar todo';
        }

        displayVillage(e.target.value);
        saveState();
    });

    addNewVillageBtn.addEventListener('click', () => {
        pasteBtn.click();
    });

    updateVillageBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            const jsonData = JSON.parse(text);
            await processAndSave(jsonData, true);
        } catch (e) {
            alert("Error al actualizar: Asegúrate de tener el JSON en el portapapeles.");
        }
    });

    deleteVillageBtn.addEventListener('click', () => {
        if (!state.activeId) return;
        if (confirm(`¿Estás seguro de que quieres eliminar la aldea "${state.villages[state.activeId].name}"?`)) {
            delete state.villages[state.activeId];
            const remainingIds = Object.keys(state.villages);
            state.activeId = remainingIds.length > 0 ? remainingIds[0] : null;

            saveState();
            if (state.activeId) {
                renderVillageSelector();
                displayVillage(state.activeId);
            } else {
                location.reload(); // Reset to initial state
            }
        }
    });

    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            const jsonData = JSON.parse(text);
            await processAndSave(jsonData);
        } catch (err) {
            pasteError.textContent = "Error: Portapapeles no contiene JSON válido.";
            pasteError.classList.remove('d-none');
        }
    });

    // Cargar estado inicial
    loadState();

});
