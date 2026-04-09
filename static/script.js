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
        const d = Math.floor(seconds / (3600*24));
        const h = Math.floor(seconds % (3600*24) / 3600);
        const m = Math.floor(seconds % 3600 / 60);
        
        let parts = [];
        if (d > 0) parts.push(`${d}d`);
        if (h > 0) parts.push(`${h}h`);
        if (m > 0) parts.push(`${m}m`);
        if (parts.length === 0) return '< 1m';
        return parts.join(' ');
    }

    const DEFENSE_IMAGE_MAP = {
        '1000001': { folder: 'TownHall',      prefix: 'Town_Hall' },
        '1000008': { folder: 'Cannon',        prefix: 'Cannon',         isComplexExt: true },
        '1000009': { folder: 'ArcherTower',   prefix: 'Archer_Tower' },
        '1000010': { folder: 'Wall',          prefix: 'Wall' },
        '1000011': { folder: 'WizardTower',   prefix: 'Wizard_Tower' },
        '1000012': { folder: 'AirDefense',    prefix: 'Air_Defense' },
        '1000013': { folder: 'Mortar',        prefix: 'Mortar',         isComplexExt: true },
        '1000015': { folder: 'BuilderHut',    prefix: 'Builders_Hut',   noLevelOne: true },
        '1000019': { folder: 'HiddenTesla',   prefix: 'Hidden_Tesla' },
        '1000021': { folder: 'X-Bow',         prefix: 'X-Bow',          suffix: '_Ground' },
        '1000027': { folder: 'InfernoTower',   prefix: 'Inferno_Tower',  suffix: '_Single' },
        '1000028': { folder: 'AirSweeper',    prefix: 'Air_Sweeper' },
        '1000031': { folder: 'EagleArtillery', prefix: 'Eagle_Artillery' },
        '1000032': { folder: 'BombTower',     prefix: 'Bomb_Tower' },
        '1000067': { folder: 'Scattershot',    prefix: 'Scattershot' },
        '1000072': { folder: 'SpellTower',    prefix: 'Spell_Tower',    dynamicSuffix: (lvl) => {
            const spells = { 1: '_Rage', 2: '_Poison', 3: '_Invisibility', 4: '_Earthquake' };
            return spells[lvl] || '';
        }},
        '1000077': { folder: 'Monolith',      prefix: 'Monolith' }
    };

    function getItemImage(group, level) {
        const config = DEFENSE_IMAGE_MAP[group.id];
        if (!config) return null;

        let ext = '.webp';
        // Especial para Cañones y Morteros (Nivel 8+ usan .wep.webp)
        if (config.isComplexExt && level >= 8) {
            ext = '.wep.webp';
        }

        // Casos donde el nivel 1 no tiene número (ej: Builders_Hut.webp)
        const displayLevel = (config.noLevelOne && level === 1) ? '' : level;
        
        const suffix = config.dynamicSuffix ? config.dynamicSuffix(level) : (config.suffix || '');
        return `/static/images/Defences/${config.folder}/${config.prefix}${displayLevel}${suffix}${ext}`;
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

        if(displayItems.length === 0) {
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
        if(v.hasBob) {
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
