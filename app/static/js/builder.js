/**
 * Course Map Builder — plate-based drag-and-drop tile placement.
 *
 * Each plate is a 32×32 stud LEGO base plate. Tiles snap to stud positions.
 * Multiple plates act like pages in a document. MILS plates show a border zone.
 *
 * Globals expected from the template:
 *   window.COURSE_ID   — current course ID
 *   window.PLATE_TYPE  — 'mils' or 'standard'
 *   window.PLATE_STUDS — studs per side (32)
 *   window.API_BASE    — e.g. "/api/v1/"
 */

const COLOR_HEX = {
    G: '#229551', R: '#cb2129', B: '#0000ff', L: '#aed252',
    P: '#d166a7', V: '#9b78b5', Y: '#f9dc2a', T: '#1baaa3',
};

// ── Plate constants ─────────────────────────────────────────────────────────
const STUD_PX = 24;  // pixels per stud
const PLATE_PX = PLATE_STUDS * STUD_PX;  // 768px for 32 studs

// ── State ───────────────────────────────────────────────────────────────────
let allTiles = [];            // full tile catalog from API
let placedTiles = [];         // [{placementId, tileId, x, y, plateIndex, tile, el}]
let nextPlacementId = 1;
let currentCategory = null;
let searchQuery = '';
let isDirty = false;
let currentPlate = 0;         // active plate index (0-based)
let plateCount = 1;           // total number of plates

// ── DOM refs ────────────────────────────────────────────────────────────────
const canvas = document.getElementById('canvas');
const paletteTilesEl = document.getElementById('palette-tiles');
const paletteCatsEl = document.getElementById('palette-categories');
const paletteSearch = document.getElementById('palette-search');
const saveBtn = document.getElementById('save-btn');
const saveStatus = document.getElementById('save-status');
const prevPlateBtn = document.getElementById('prev-plate');
const nextPlateBtn = document.getElementById('next-plate');
const addPlateBtn = document.getElementById('add-plate');
const removePlateBtn = document.getElementById('remove-plate');
const plateIndicator = document.getElementById('plate-indicator');
const plateTypeLabel = document.getElementById('plate-type-label');

// ── Canvas setup ────────────────────────────────────────────────────────────
function initCanvas() {
    canvas.style.width = PLATE_PX + 'px';
    canvas.style.height = PLATE_PX + 'px';

    // Draw stud grid as SVG
    drawStudGrid();

    // Show MILS border if applicable
    if (PLATE_TYPE === 'mils') {
        const border = document.createElement('div');
        border.className = 'mils-border';
        border.style.setProperty('--stud-size', STUD_PX + 'px');
        canvas.appendChild(border);
    }

    // Plate type label in toolbar
    plateTypeLabel.textContent = PLATE_TYPE === 'mils' ? 'MILS 32×32' : 'Standard 32×32';
}

function drawStudGrid() {
    const existing = canvas.querySelector('.stud-grid');
    if (existing) existing.remove();

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('class', 'stud-grid');
    svg.setAttribute('width', PLATE_PX);
    svg.setAttribute('height', PLATE_PX);
    svg.style.position = 'absolute';
    svg.style.inset = '0';
    svg.style.pointerEvents = 'none';

    // Draw stud circles
    for (let row = 0; row < PLATE_STUDS; row++) {
        for (let col = 0; col < PLATE_STUDS; col++) {
            const cx = col * STUD_PX + STUD_PX / 2;
            const cy = row * STUD_PX + STUD_PX / 2;
            const circle = document.createElementNS(svgNS, 'circle');
            circle.setAttribute('cx', cx);
            circle.setAttribute('cy', cy);
            circle.setAttribute('r', 3);
            circle.setAttribute('fill', 'rgba(0,0,0,0.12)');
            svg.appendChild(circle);
        }
    }

    canvas.insertBefore(svg, canvas.firstChild);
}

// ── Barcode helpers ─────────────────────────────────────────────────────────
function renderMiniBarcode(code) {
    return code.split('').map(c =>
        `<div class="bar" style="background:${COLOR_HEX[c]}"></div>`
    ).join('');
}

function renderBarcode(code) {
    return code.split('').map(c =>
        `<div class="bar" style="background:${COLOR_HEX[c]}"></div>`
    ).join('');
}

// ── Snap to grid ────────────────────────────────────────────────────────────
function snapToGrid(px) {
    return Math.round(px / STUD_PX) * STUD_PX;
}

// ── Palette ─────────────────────────────────────────────────────────────────
async function loadTiles() {
    let page = 1;
    let tiles = [];
    while (true) {
        const resp = await fetch(`${API_BASE}tiles?per_page=100&page=${page}`);
        const data = await resp.json();
        tiles = tiles.concat(data.tiles);
        if (page >= data.pages) break;
        page++;
    }
    allTiles = tiles;
    renderCategories();
    renderPalette();
}

function renderCategories() {
    const cats = [...new Set(allTiles.map(t => t.category))].sort();

    let html = `<button class="cat-btn ${!currentCategory ? 'active' : ''}" data-cat="">All</button>`;
    cats.forEach(cat => {
        const label = cat.replace('_', ' ');
        html += `<button class="cat-btn ${currentCategory === cat ? 'active' : ''}" data-cat="${cat}">${label}</button>`;
    });
    paletteCatsEl.innerHTML = html;

    paletteCatsEl.querySelectorAll('.cat-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentCategory = btn.dataset.cat || null;
            renderCategories();
            renderPalette();
        });
    });
}

function renderPalette() {
    let filtered = allTiles;
    if (currentCategory) {
        filtered = filtered.filter(t => t.category === currentCategory);
    }
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(t =>
            t.label.toLowerCase().includes(q) || t.code.toLowerCase().includes(q)
        );
    }

    paletteTilesEl.innerHTML = filtered.map(t => `
        <div class="palette-tile" draggable="true" data-tile-id="${t.id}">
            <div class="mini-barcode">${renderMiniBarcode(t.code)}</div>
            <span class="tile-label">${t.label}</span>
        </div>
    `).join('');

    paletteTilesEl.querySelectorAll('.palette-tile').forEach(el => {
        el.addEventListener('dragstart', onPaletteDragStart);
    });
}

paletteSearch.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    renderPalette();
});

// ── Drag from Palette ───────────────────────────────────────────────────────
function onPaletteDragStart(e) {
    const tileId = parseInt(e.currentTarget.dataset.tileId);
    e.dataTransfer.setData('application/x-tile-id', tileId.toString());
    e.dataTransfer.effectAllowed = 'copy';
}

// ── Canvas Drop Zone ────────────────────────────────────────────────────────
canvas.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    canvas.classList.add('drag-over');
});

canvas.addEventListener('dragleave', () => {
    canvas.classList.remove('drag-over');
});

canvas.addEventListener('drop', (e) => {
    e.preventDefault();
    canvas.classList.remove('drag-over');

    const tileIdStr = e.dataTransfer.getData('application/x-tile-id');
    if (!tileIdStr) return;

    const tileId = parseInt(tileIdStr);
    const tile = allTiles.find(t => t.id === tileId);
    if (!tile) return;

    const rect = canvas.getBoundingClientRect();
    const rawX = e.clientX - rect.left + canvas.scrollLeft;
    const rawY = e.clientY - rect.top + canvas.scrollTop;

    // Snap to nearest stud position
    const x = snapToGrid(rawX - 30);
    const y = snapToGrid(rawY - 20);

    addPlacedTile(tile, x, y, currentPlate);
});

// ── Plate Navigation ────────────────────────────────────────────────────────
function updatePlateUI() {
    plateIndicator.textContent = `Plate ${currentPlate + 1} of ${plateCount}`;
    prevPlateBtn.disabled = currentPlate === 0;
    nextPlateBtn.disabled = currentPlate >= plateCount - 1;

    // Can't remove the last plate, or a plate that has tiles
    const tilesOnPlate = placedTiles.filter(p => p.plateIndex === currentPlate);
    removePlateBtn.disabled = plateCount <= 1 || tilesOnPlate.length > 0;

    // Show/hide tiles based on current plate
    placedTiles.forEach(p => {
        p.el.style.display = p.plateIndex === currentPlate ? '' : 'none';
    });
}

prevPlateBtn.addEventListener('click', () => {
    if (currentPlate > 0) {
        currentPlate--;
        updatePlateUI();
    }
});

nextPlateBtn.addEventListener('click', () => {
    if (currentPlate < plateCount - 1) {
        currentPlate++;
        updatePlateUI();
    }
});

addPlateBtn.addEventListener('click', () => {
    plateCount++;
    currentPlate = plateCount - 1;
    updatePlateUI();
    markDirty();
});

removePlateBtn.addEventListener('click', () => {
    if (plateCount <= 1) return;
    const tilesOnPlate = placedTiles.filter(p => p.plateIndex === currentPlate);
    if (tilesOnPlate.length > 0) return;

    // Shift down plate indices for plates after the removed one
    placedTiles.forEach(p => {
        if (p.plateIndex > currentPlate) {
            p.plateIndex--;
        }
    });

    plateCount--;
    if (currentPlate >= plateCount) {
        currentPlate = plateCount - 1;
    }
    updatePlateUI();
    markDirty();
});

// ── Placed Tiles ────────────────────────────────────────────────────────────
function addPlacedTile(tile, x, y, plateIndex, placementId) {
    // Snap and clamp to plate bounds
    x = snapToGrid(x);
    y = snapToGrid(y);
    x = Math.max(0, Math.min(x, PLATE_PX - STUD_PX * 3));
    y = Math.max(0, Math.min(y, PLATE_PX - STUD_PX * 2));

    const id = placementId || nextPlacementId++;
    if (!placementId && id >= nextPlacementId) nextPlacementId = id + 1;

    const el = document.createElement('div');
    el.className = 'placed-tile';
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    el.dataset.placementId = id;

    // Hide if not on current plate
    if (plateIndex !== currentPlate) {
        el.style.display = 'none';
    }

    el.innerHTML = `
        <div class="barcode">${renderBarcode(tile.code)}</div>
        <div class="label">${tile.label}</div>
        <button class="remove-btn" title="Remove">&times;</button>
    `;

    el.querySelector('.remove-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        removePlacedTile(id);
    });

    makeDraggable(el, id);

    canvas.appendChild(el);

    const placement = { placementId: id, tileId: tile.id, x, y, plateIndex, tile, el };
    placedTiles.push(placement);
    markDirty();

    return placement;
}

function removePlacedTile(placementId) {
    const idx = placedTiles.findIndex(p => p.placementId === placementId);
    if (idx === -1) return;
    placedTiles[idx].el.remove();
    placedTiles.splice(idx, 1);
    markDirty();
    updatePlateUI();
}

// ── Drag to Reposition (pointer events, with snap) ──────────────────────────
function makeDraggable(el, placementId) {
    let startX, startY, origLeft, origTop;
    let dragging = false;

    el.addEventListener('pointerdown', (e) => {
        if (e.target.classList.contains('remove-btn')) return;
        e.preventDefault();
        dragging = true;
        startX = e.clientX;
        startY = e.clientY;
        origLeft = parseFloat(el.style.left);
        origTop = parseFloat(el.style.top);
        el.setPointerCapture(e.pointerId);
        el.style.zIndex = 1000;
    });

    el.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        let newX = snapToGrid(origLeft + dx);
        let newY = snapToGrid(origTop + dy);

        // Clamp to plate bounds
        newX = Math.max(0, Math.min(newX, PLATE_PX - STUD_PX * 3));
        newY = Math.max(0, Math.min(newY, PLATE_PX - STUD_PX * 2));

        el.style.left = newX + 'px';
        el.style.top = newY + 'px';
    });

    el.addEventListener('pointerup', (e) => {
        if (!dragging) return;
        dragging = false;
        el.style.zIndex = '';

        const placement = placedTiles.find(p => p.placementId === placementId);
        if (placement) {
            placement.x = parseFloat(el.style.left);
            placement.y = parseFloat(el.style.top);
            markDirty();
        }
    });
}

// ── Save / Load ─────────────────────────────────────────────────────────────
function markDirty() {
    isDirty = true;
    saveStatus.textContent = 'Unsaved changes';
}

saveBtn.addEventListener('click', saveCourse);

async function saveCourse() {
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    saveStatus.textContent = '';

    const tiles = placedTiles.map(p => ({
        tile_id: p.tileId,
        x: Math.round(p.x * 10) / 10,
        y: Math.round(p.y * 10) / 10,
        plate_index: p.plateIndex,
    }));

    try {
        const resp = await fetch(`${API_BASE}courses/${COURSE_ID}/tiles`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tiles }),
        });

        if (resp.ok) {
            isDirty = false;
            saveStatus.textContent = 'Saved!';
            setTimeout(() => {
                if (!isDirty) saveStatus.textContent = '';
            }, 2000);
        } else {
            const data = await resp.json();
            saveStatus.textContent = 'Error: ' + (data.error || 'Save failed');
        }
    } catch (err) {
        saveStatus.textContent = 'Error: ' + err.message;
    }

    saveBtn.disabled = false;
    saveBtn.textContent = 'Save';
}

async function loadCourse() {
    const resp = await fetch(`${API_BASE}courses/${COURSE_ID}`);
    if (!resp.ok) return;

    const data = await resp.json();
    if (data.tiles && data.tiles.length > 0) {
        // Determine how many plates we need
        const maxPlate = Math.max(...data.tiles.map(tp => tp.plate_index || 0));
        plateCount = Math.max(plateCount, maxPlate + 1);

        data.tiles.forEach(tp => {
            const tile = tp.tile || allTiles.find(t => t.id === tp.tile_id);
            if (tile) {
                addPlacedTile(tile, tp.x, tp.y, tp.plate_index || 0, nextPlacementId++);
            }
        });
    }
    isDirty = false;
    saveStatus.textContent = '';
    updatePlateUI();
}

// Warn on unsaved changes
window.addEventListener('beforeunload', (e) => {
    if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// Keyboard shortcut: Ctrl+S to save
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveCourse();
    }
});

// ── Init ────────────────────────────────────────────────────────────────────
async function init() {
    initCanvas();
    updatePlateUI();
    await loadTiles();
    await loadCourse();
}

init();
