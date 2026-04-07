/**
 * Course Map Builder — drag and drop tile placement on a free-form canvas.
 *
 * Globals expected from the template:
 *   window.COURSE_ID  — current course ID
 *   window.CANVAS_WIDTH / CANVAS_HEIGHT
 *   window.API_BASE — e.g. "/api/v1/"
 */

const COLOR_HEX = {
    G: '#229551', R: '#cb2129', B: '#0000ff', L: '#aed252',
    P: '#d166a7', V: '#9b78b5', Y: '#f9dc2a', T: '#1baaa3',
};

// ── State ──────────────────────────────────────────────────────────────────
let allTiles = [];            // full tile catalog from API
let placedTiles = [];         // [{placementId, tileId, x, y, tile, el}]
let nextPlacementId = 1;
let currentCategory = null;
let searchQuery = '';
let isDirty = false;

// ── DOM refs ───────────────────────────────────────────────────────────────
const canvas = document.getElementById('canvas');
const paletteTilesEl = document.getElementById('palette-tiles');
const paletteCatsEl = document.getElementById('palette-categories');
const paletteSearch = document.getElementById('palette-search');
const saveBtn = document.getElementById('save-btn');
const saveStatus = document.getElementById('save-status');

// ── Barcode helpers ────────────────────────────────────────────────────────
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

// ── Palette ────────────────────────────────────────────────────────────────
async function loadTiles() {
    // Fetch all tiles (paginate through if needed)
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

    // Attach drag events
    paletteTilesEl.querySelectorAll('.palette-tile').forEach(el => {
        el.addEventListener('dragstart', onPaletteDragStart);
    });
}

paletteSearch.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    renderPalette();
});

// ── Drag from Palette ──────────────────────────────────────────────────────
function onPaletteDragStart(e) {
    const tileId = parseInt(e.currentTarget.dataset.tileId);
    e.dataTransfer.setData('application/x-tile-id', tileId.toString());
    e.dataTransfer.effectAllowed = 'copy';
}

// ── Canvas Drop Zone ───────────────────────────────────────────────────────
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
    const x = e.clientX - rect.left + canvas.scrollLeft;
    const y = e.clientY - rect.top + canvas.scrollTop;

    addPlacedTile(tile, x - 30, y - 20);  // offset to center on cursor
});

// ── Placed Tiles ───────────────────────────────────────────────────────────
function addPlacedTile(tile, x, y, placementId) {
    // Clamp to canvas bounds
    x = Math.max(0, Math.min(x, CANVAS_WIDTH - 60));
    y = Math.max(0, Math.min(y, CANVAS_HEIGHT - 50));

    const id = placementId || nextPlacementId++;
    if (!placementId && id >= nextPlacementId) nextPlacementId = id + 1;

    const el = document.createElement('div');
    el.className = 'placed-tile';
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    el.dataset.placementId = id;

    el.innerHTML = `
        <div class="barcode">${renderBarcode(tile.code)}</div>
        <div class="label">${tile.label}</div>
        <button class="remove-btn" title="Remove">&times;</button>
    `;

    // Remove button
    el.querySelector('.remove-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        removePlacedTile(id);
    });

    // Drag to reposition
    makeDraggable(el, id);

    canvas.appendChild(el);

    const placement = { placementId: id, tileId: tile.id, x, y, tile, el };
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
}

// ── Drag to Reposition (pointer events) ────────────────────────────────────
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
        let newX = origLeft + dx;
        let newY = origTop + dy;

        // Clamp
        newX = Math.max(0, Math.min(newX, CANVAS_WIDTH - 60));
        newY = Math.max(0, Math.min(newY, CANVAS_HEIGHT - 50));

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

// ── Save / Load ────────────────────────────────────────────────────────────
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
    if (data.tiles) {
        data.tiles.forEach(tp => {
            const tile = tp.tile || allTiles.find(t => t.id === tp.tile_id);
            if (tile) {
                addPlacedTile(tile, tp.x, tp.y, nextPlacementId++);
            }
        });
    }
    isDirty = false;
    saveStatus.textContent = '';
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

// ── Init ───────────────────────────────────────────────────────────────────
async function init() {
    await loadTiles();
    await loadCourse();
}

init();
