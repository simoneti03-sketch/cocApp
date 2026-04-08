document.addEventListener('DOMContentLoaded', () => {
    const pasteBtn = document.getElementById('pasteDataBtn');
    const loader = document.getElementById('loader');
    const pasteError = document.getElementById('pasteError');
    const dashboardContent = document.getElementById('dashboardContent');

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
                
                let extraTags = '';
                if (inst.weapon > 0) extraTags += ` <span class="badge bg-danger ms-1" style="font-size: 0.70rem;">Arma ${inst.weapon}</span>`;
                if (inst.gear_up > 0) extraTags += ` <span class="badge bg-primary ms-1" style="font-size: 0.70rem;"><i class="bi bi-gear-wide-connected me-1"></i>Perfeccionada</span>`;

                instancesHtml += `
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary mb-1 flex-wrap">
                        <div class="d-flex align-items-center mb-1 mb-sm-0">
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

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card bg-dark glass-card item-card h-100 ${bClass} shadow-sm overflow-hidden ${hasDropdown ? 'accordion' : ''}" id="${accId}-parent">
                    <div class="card-body p-0">
                        <div class="accordion-item bg-transparent border-0">
                            <h2 class="accordion-header p-3 pb-0" id="heading-${accId}">
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
        if(items.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-secondary py-4"><i class="bi bi-inbox fs-1 d-block mb-2"></i>No se encontraron datos en esta categoría.</div>';
            return;
        }
        
        items.sort((a, b) => b.time_to_max - a.time_to_max);
        
        let html = '';
        items.forEach(group => {
            html += createAccordion(group, iconClass);
        });
        container.innerHTML = html;
    }

    pasteBtn.addEventListener('click', async () => {
        pasteError.classList.add('d-none');
        try {
            const text = await navigator.clipboard.readText();
            let jsonData;
            try {
                jsonData = JSON.parse(text);
            } catch (e) {
                pasteError.textContent = "El contenido del portapapeles no es JSON válido.";
                pasteError.classList.remove('d-none');
                return;
            }

            loader.classList.remove('d-none');
            pasteBtn.disabled = true;

            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonData)
            });

            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                const data = result.data;
                const hasBob = result.has_bob_hut;
                
                const bobIcon = document.getElementById('bobHutIcon');
                if(hasBob) {
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
                
                // Render cards
                renderSection('defensesContainer', data.defenses, 'bi bi-shield');
                renderSection('armyContainer', data.army, 'bi bi-crosshair');
                renderSection('resourcesContainer', data.resources, 'bi bi-box-seam');
                
                renderSection('trapsContainer', data.traps, 'bi bi-x-octagon');
                renderSection('helpersContainer', data.helpers, 'bi bi-hammer');
                
                renderSection('unitsContainer', data.units, 'bi bi-lightning-charge');
                renderSection('spellsContainer', data.spells, 'bi bi-magic');
                renderSection('siegeContainer', data.siege_machines, 'bi bi-truck');
                
                renderSection('heroesContainer', data.heroes, 'bi bi-person-bounding-box');
                renderSection('petsContainer', data.pets, 'bi bi-bug');
                renderSection('equipmentContainer', data.equipment, 'bi bi-shield-shaded');

                // Show dashboard
                dashboardContent.classList.remove('d-none');
                
                // Scroll to dashboard
                dashboardContent.scrollIntoView({ behavior: 'smooth', block: 'start' });

            } else {
                throw new Error(result.error || 'Error procesando los datos en el servidor.');
            }

        } catch (err) {
            console.error("Error reading clipboard or processing:", err);
            pasteError.textContent = "Error: " + err.message + ". (Es posible que debas conceder permiso para leer el portapapeles).";
            pasteError.classList.remove('d-none');
        } finally {
            loader.classList.add('d-none');
            pasteBtn.disabled = false;
        }
    });

});
