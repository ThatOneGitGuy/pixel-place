// ─── State ───────────────────────────────────────────────
let currentUser = null;
let currentPixelId = null;
let pixelData = {};
const GRID = 300;
const PIXEL_SIZE = 4;
let scale = 1;
let isDragging = false, dragStart = {x:0,y:0}, scrollStart = {x:0,y:0};

// ─── Canvas Setup ─────────────────────────────────────────
const canvas = document.getElementById('pixel-canvas');
const ctx = canvas.getContext('2d');
canvas.width = GRID * PIXEL_SIZE;
canvas.height = GRID * PIXEL_SIZE;

// Convert pixel ID "row-col" to x,y canvas coords
function pixelIdToXY(pid) {
    const parts = pid.split('-');
    if (parts.length !== 2) return null;
    const row = parseInt(parts[0]) - 1;
    const col = parseInt(parts[1]) - 1;
    if (isNaN(row) || isNaN(col)) return null;
    return { x: col, y: row };
}

// Convert canvas x,y to pixel ID
function xyToPixelId(x, y) {
    return `${y + 1}-${x + 1}`;
}

function drawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw all pixels
    for (let row = 0; row < GRID; row++) {
        for (let col = 0; col < GRID; col++) {
            const pid = `${row + 1}-${col + 1}`;
            const info = pixelData[pid];
            ctx.fillStyle = info ? info.color : '#1e1e1e';
            ctx.fillRect(col * PIXEL_SIZE, row * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
        }
    }

    // Faint grid lines
    ctx.strokeStyle = 'rgba(100,80,50,0.08)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= GRID; x++) {
        ctx.beginPath();
        ctx.moveTo(x * PIXEL_SIZE, 0);
        ctx.lineTo(x * PIXEL_SIZE, canvas.height);
        ctx.stroke();
    }
    for (let y = 0; y <= GRID; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * PIXEL_SIZE);
        ctx.lineTo(canvas.width, y * PIXEL_SIZE);
        ctx.stroke();
    }

    // Highlight owned pixel with a white border
    if (currentPixelId) {
        const pos = pixelIdToXY(currentPixelId);
        if (pos) {
            ctx.strokeStyle = '#2c1f0e';
            ctx.lineWidth = 2;
            ctx.strokeRect(
                pos.x * PIXEL_SIZE + 1,
                pos.y * PIXEL_SIZE + 1,
                PIXEL_SIZE - 2,
                PIXEL_SIZE - 2
            );
        }
    }
}

async function loadPixels() {
    const res = await fetch('/api/pixels');
    pixelData = await res.json();
    drawCanvas();
}

// ─── Zoom & Pan ───────────────────────────────────────────
const wrapper = document.getElementById('canvas-wrapper');
const outer = document.getElementById('canvas-outer');

function applyScale() {
    wrapper.style.transform = `scale(${scale})`;
    const w = canvas.width * scale;
    const h = canvas.height * scale;
    wrapper.style.width = w + 'px';
    wrapper.style.height = h + 'px';
}
function zoom(factor) {
    scale = Math.min(Math.max(scale * factor, 0.2), 10);
    applyScale();
}
function resetZoom() { scale = 1; applyScale(); outer.scrollTo(0, 0); }

// Mouse drag to pan
outer.addEventListener('mousedown', e => {
    isDragging = true;
    dragStart = { x: e.clientX, y: e.clientY };
    scrollStart = { x: outer.scrollLeft, y: outer.scrollTop };
});
window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    outer.scrollLeft = scrollStart.x - (e.clientX - dragStart.x);
    outer.scrollTop = scrollStart.y - (e.clientY - dragStart.y);
});
window.addEventListener('mouseup', () => isDragging = false);

// Touch drag to pan
outer.addEventListener('touchstart', e => {
    if (e.touches.length === 1) {
        isDragging = true;
        dragStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        scrollStart = { x: outer.scrollLeft, y: outer.scrollTop };
    }
}, { passive: true });
outer.addEventListener('touchmove', e => {
    if (!isDragging || e.touches.length !== 1) return;
    outer.scrollLeft = scrollStart.x - (e.touches[0].clientX - dragStart.x);
    outer.scrollTop = scrollStart.y - (e.touches[0].clientY - dragStart.y);
}, { passive: true });
outer.addEventListener('touchend', () => isDragging = false);

// Pinch to zoom
let lastPinchDist = null;
outer.addEventListener('touchmove', e => {
    if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (lastPinchDist) zoom(dist / lastPinchDist);
        lastPinchDist = dist;
    }
}, { passive: true });
outer.addEventListener('touchend', () => lastPinchDist = null);

// Mouse wheel zoom
outer.addEventListener('wheel', e => {
    e.preventDefault();
    zoom(e.deltaY < 0 ? 1.1 : 0.9);
}, { passive: false });

// Hover info
canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = Math.floor((e.clientX - rect.left) * scaleX / PIXEL_SIZE);
    const cy = Math.floor((e.clientY - rect.top) * scaleY / PIXEL_SIZE);
    if (cx >= 0 && cx < GRID && cy >= 0 && cy < GRID) {
        const pid = xyToPixelId(cx, cy);
        const info = pixelData[pid];
        const owner = info ? info.owner : 'unclaimed';
        document.getElementById('hover-info').textContent = `${pid} · ${owner}`;
    }
});

// ─── Auth ─────────────────────────────────────────────────
function openAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    switchModal(mode);
}
function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}
function switchModal(mode) {
    const isLogin = mode === 'login';
    document.getElementById('modal-login-form').style.display = isLogin ? 'block' : 'none';
    document.getElementById('modal-reg-form').style.display = isLogin ? 'none' : 'block';
    document.getElementById('modal-login-tab').classList.toggle('active', isLogin);
    document.getElementById('modal-reg-tab').classList.toggle('active', !isLogin);
}

async function doLogin() {
    const username = document.getElementById('login-user').value.trim();
    const password = document.getElementById('login-pass').value.trim();
    const res = await fetch('/api/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
        currentUser = data.username;
        currentPixelId = data.pixel_id;
        closeAuth();
        updateAuthUI();
        refreshMyPixelPanel();
        drawCanvas();
    } else {
        document.getElementById('login-error').textContent = data.error;
    }
}

async function doRegister() {
    const username = document.getElementById('reg-user').value.trim();
    const password = document.getElementById('reg-pass').value.trim();
    const res = await fetch('/api/register', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
        currentUser = data.username;
        currentPixelId = null;
        closeAuth();
        updateAuthUI();
        refreshMyPixelPanel();
    } else {
        document.getElementById('reg-error').textContent = data.error;
    }
}

async function doLogout() {
    await fetch('/api/logout', { method: 'POST' });
    currentUser = null;
    currentPixelId = null;
    updateAuthUI();
    refreshMyPixelPanel();
    drawCanvas();
}

function updateAuthUI() {
    const label = document.getElementById('user-label');
    const authBtn = document.getElementById('auth-btn');
    const logoutBtn = document.getElementById('logout-btn');
    if (currentUser) {
        label.textContent = currentUser;
        authBtn.style.display = 'none';
        logoutBtn.style.display = '';
    } else {
        label.textContent = '';
        authBtn.style.display = '';
        logoutBtn.style.display = 'none';
    }
}

// ─── My Pixel Panel ───────────────────────────────────────
function refreshMyPixelPanel() {
    const noLogin = document.getElementById('no-login-msg');
    const noPixel = document.getElementById('no-pixel-msg');
    const hasPixel = document.getElementById('has-pixel-msg');

    if (!currentUser) {
        noLogin.style.display = ''; noPixel.style.display = 'none'; hasPixel.style.display = 'none';
    } else if (!currentPixelId) {
        noLogin.style.display = 'none'; noPixel.style.display = ''; hasPixel.style.display = 'none';
    } else {
        noLogin.style.display = 'none'; noPixel.style.display = 'none'; hasPixel.style.display = '';
        document.getElementById('owned-pixel-id').textContent = currentPixelId;
        const info = pixelData[currentPixelId];
        const color = info ? info.color : '#8b5e3c';
        document.getElementById('pixel-preview').style.background = color;
        document.getElementById('update-color').value = color;
    }
}

async function claimPixel() {
    const pixelIdInput = document.getElementById('pixel-id-input').value.trim();
    const color = document.getElementById('claim-color').value;
    const res = await fetch('/api/claim', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pixel_id: pixelIdInput, color })
    });
    const data = await res.json();
    if (data.success) {
        currentPixelId = data.pixel_id;
        pixelData[currentPixelId] = { owner: currentUser, color: data.color };
        refreshMyPixelPanel();
        drawCanvas();
        document.getElementById('claim-error').textContent = '';
    } else {
        document.getElementById('claim-error').textContent = data.error;
    }
}

async function claimRandom() {
    const color = document.getElementById('claim-color').value;
    const res = await fetch('/api/claim', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ random: true, color })
    });
    const data = await res.json();
    if (data.success) {
        currentPixelId = data.pixel_id;
        pixelData[currentPixelId] = { owner: currentUser, color: data.color };
        refreshMyPixelPanel();
        drawCanvas();
    } else {
        document.getElementById('claim-error').textContent = data.error;
    }
}

async function updateColor() {
    const color = document.getElementById('update-color').value;
    const res = await fetch('/api/update_color', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ color })
    });
    const data = await res.json();
    if (data.success) {
        pixelData[currentPixelId] = { owner: currentUser, color };
        document.getElementById('pixel-preview').style.background = color;
        document.getElementById('update-msg').textContent = 'Color updated!';
        setTimeout(() => document.getElementById('update-msg').textContent = '', 2000);
        drawCanvas();
    }
}

// ─── Tab Switching ────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + tab).classList.add('active');
        if (tab === 'my-pixel') refreshMyPixelPanel();
    });
});

// ─── Init ─────────────────────────────────────────────────
async function init() {
    const res = await fetch('/api/me');
    const data = await res.json();
    if (data.logged_in) {
        currentUser = data.username;
        currentPixelId = data.pixel_id;
        updateAuthUI();
    }
    await loadPixels();
    applyScale();
}

init();