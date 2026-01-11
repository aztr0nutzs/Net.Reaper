/* NETREAPER • Holographic WiFi Discovery Map
   - No external JS deps (portable/offline)
   - Renders a lightweight 3D-ish holographic graph on <canvas>
   - Pulls scan data from /api/networks/latest

   Data contract expected from API:
   {
     "generated_at":"2025-12-13T00:00:00Z",
     "iface":"wlan0",
     "backend":"nmcli"|"iw"|"...",
     "networks":[
        {"bssid":"AA:BB:..","ssid":"MyWiFi","channel":6,"freq_mhz":2437,"signal":72,"security":"WPA2"},
        ...
     ]
   }
*/

(() => {
  "use strict";

  const canvas = document.getElementById("c");
  const ctx = canvas.getContext("2d", { alpha: true });

  const elStatus = document.getElementById("status");
  const elSel = document.getElementById("sel");
  const btnReload = document.getElementById("btnReload");
  const chkAuto = document.getElementById("chkAuto");
  const inpInterval = document.getElementById("inpInterval");
  const btnFilterWPA2 = document.getElementById("btnFilterWPA2");
  const btnFilterOpen = document.getElementById("btnFilterOpen");
  const btnFilterAll = document.getElementById("btnFilterAll");
  const btnExport = document.getElementById("btnExport");
  const btnTheme = document.getElementById("btnTheme");
  const spinner = document.getElementById("spinner");

  // ---------- utilities ----------
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;

  function nowMs() { return performance.now(); }

  function fitCanvas() {
    const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    const w = Math.floor(canvas.clientWidth * dpr);
    const h = Math.floor(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    return { w, h, dpr };
  }

  function hash32(str) {
    // deterministic tiny hash for layout seeding
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function rand01(seed) {
    // xorshift32 -> [0,1)
    let x = seed >>> 0;
    x ^= x << 13; x >>>= 0;
    x ^= x >> 17; x >>>= 0;
    x ^= x << 5;  x >>>= 0;
    return (x >>> 0) / 4294967296;
  }

  function fmtSignal(n) {
    if (n == null) return "n/a";
    if (typeof n !== "number") return String(n);
    return `${Math.round(n)}`;
  }

  // ---------- camera / controls ----------
  const cam = {
    yaw: 0.55,
    pitch: -0.38,
    dist: 780,
    targetDist: 780,
    targetYaw: 0.55,
    targetPitch: -0.38,
    cx: 0,
    cy: 0,
  };

  function resetView() {
    cam.targetYaw = 0.55;
    cam.targetPitch = -0.38;
    cam.targetDist = 780;
  }

  let dragging = false;
  let lastX = 0, lastY = 0;

  canvas.addEventListener("pointerdown", (e) => {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointerup", (e) => {
    dragging = false;
    canvas.releasePointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    cam.targetYaw += dx * 0.005;
    cam.targetPitch += dy * 0.005;
    cam.targetPitch = clamp(cam.targetPitch, -1.2, 1.2);
  });

  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    cam.targetDist *= (1 + (e.deltaY > 0 ? 0.08 : -0.08));
    cam.targetDist = clamp(cam.targetDist, 260, 2200);
  }, { passive: false });

  window.addEventListener("keydown", (e) => {
    if (e.key === "r" || e.key === "R") resetView();
  });

  // ---------- graph state ----------
  const graph = {
    meta: { generated_at: "", iface: "", backend: "" },
    nodes: [],
    edges: [],
    selectedId: null,
    lastFetchOk: false,
    lastFetchAt: 0,
    filter: null, // 'wpa2', 'open', or null
  };

  function setStatus(msg) { elStatus.textContent = msg; }

  function nodeId(n) { return n.bssid || n.ssid || n.id; }

  function buildLayout(networks) {
    // Apply filter
    let filtered = networks;
    if (graph.filter === 'wpa2') {
      filtered = networks.filter(n => (n.security || '').toLowerCase().includes('wpa2'));
    } else if (graph.filter === 'open') {
      filtered = networks.filter(n => (n.security || '').toLowerCase() === 'open' || !n.security);
    }

    // Create 3D positions deterministically based on BSSID/SSID.
    // Layers: 2.4GHz (z=-120), 5GHz (z=+120), unknown z=0
    const nodes = [];
    const edges = [];

    // Scanner origin node (center)
    const origin = {
      id: "__scanner__",
      kind: "scanner",
      label: "Scanner",
      x: 0, y: 0, z: 0,
      size: 18,
      data: { role: "local" }
    };
    nodes.push(origin);

    const byChannel = new Map();
    for (const net of filtered) {
      const ch = Number(net.channel || 0) || 0;
      if (!byChannel.has(ch)) byChannel.set(ch, []);
      byChannel.get(ch).push(net);
    }

    const chans = [...byChannel.keys()].sort((a,b)=>a-b);
    const maxR = 360;
    const minR = 140;
    const ringStep = chans.length > 0 ? (maxR - minR) / Math.max(1, chans.length - 1) : 1;

    chans.forEach((ch, idx) => {
      const list = byChannel.get(ch);
      const r = minR + idx * ringStep;

      for (let i = 0; i < list.length; i++) {
        const net = list[i];
        const seed = hash32((net.bssid || "") + "|" + (net.ssid || "") + "|" + ch);
        const a0 = (idx / Math.max(1, chans.length)) * Math.PI * 2;
        const jitter = (rand01(seed) - 0.5) * 0.65;
        const angle = a0 + (i / Math.max(1, list.length)) * (Math.PI * 2 / Math.max(1, chans.length)) + jitter;

        const freq = Number(net.freq_mhz || 0) || 0;
        const z = freq >= 5000 ? 120 : (freq > 0 && freq < 3000 ? -120 : 0);

        // Signal influences height (y)
        const sig = Number(net.signal || 0);
        const y = -sig ? 0 : lerp(90, -90, clamp(sig / 100, 0, 1)); // nmcli gives 0..100; higher -> closer to viewer

        const x = Math.cos(angle) * r;
        const zz = Math.sin(angle) * r;

        const id = nodeId(net);
        nodes.push({
          id,
          kind: "ap",
          label: net.ssid || "(hidden)",
          x,
          y,
          z: z,
          size: 8 + clamp((Number(net.signal)||50)/100, 0, 1) * 8,
          data: net
        });

        edges.push({ a: origin.id, b: id, w: 1 });
      }
    });

    // Add soft "interference" links: same channel, close proximity
    for (let i = 1; i < nodes.length; i++) {
      const ni = nodes[i];
      const chi = Number(ni.data?.channel || 0) || 0;
      for (let j = i + 1; j < nodes.length; j++) {
        const nj = nodes[j];
        const chj = Number(nj.data?.channel || 0) || 0;
        if (chi !== chj || chi === 0) continue;
        const dx = ni.x - nj.x, dy = ni.y - nj.y, dz = ni.z - nj.z;
        const d2 = dx*dx + dy*dy + dz*dz;
        if (d2 < 220*220) edges.push({ a: ni.id, b: nj.id, w: 0.6, kind:"interf" });
      }
    }

    return { nodes, edges };
  }

  // ---------- 3D projection ----------
  function rotateY(x,z,yaw){
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    return { x: x*cy + z*sy, z: -x*sy + z*cy };
  }
  function rotateX(y,z,pitch){
    const cx = Math.cos(pitch), sx = Math.sin(pitch);
    return { y: y*cx - z*sx, z: y*sx + z*cx };
  }

  function project(pt, w, h) {
    const { x, y, z } = pt;
    // basic perspective
    const fov = 860;
    const s = fov / (fov + z);
    return {
      sx: w * 0.5 + x * s,
      sy: h * 0.5 + y * s,
      s,
    };
  }

  function toCameraSpace(node) {
    // world -> camera
    let x = node.x;
    let y = node.y;
    let z = node.z;

    // orbit camera by rotating world opposite direction
    const rY = rotateY(x, z, cam.yaw);
    x = rY.x; z = rY.z;
    const rX = rotateX(y, z, cam.pitch);
    y = rX.y; z = rX.z;

    z += cam.dist;
    return { x, y, z };
  }

  // ---------- picking ----------
  let pickList = []; // {id, x, y, r}

  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const dpr = canvas.width / rect.width;
    const mx = (e.clientX - rect.left) * dpr;
    const my = (e.clientY - rect.top) * dpr;

    let best = null;
    for (const p of pickList) {
      const dx = mx - p.x, dy = my - p.y;
      if (dx*dx + dy*dy <= p.r*p.r) {
        if (!best || p.r > best.r) best = p;
      }
    }
    if (best) {
      graph.selectedId = best.id;
      showSelection(best.id);
    }
  });

  function showSelection(id) {
    const n = graph.nodes.find(n => n.id === id);
    if (!n) {
      elSel.textContent = "Click a node…";
      return;
    }
    const d = n.data || {};
    const lines = [];
    if (n.kind === "scanner") {
      lines.push("Role: local scanner");
      lines.push(`Interface: ${graph.meta.iface || "n/a"}`);
      lines.push(`Backend: ${graph.meta.backend || "n/a"}`);
      lines.push(`Generated: ${graph.meta.generated_at || "n/a"}`);
    } else {
      lines.push(`SSID: ${d.ssid ?? "(hidden)"}`);
      lines.push(`BSSID: ${d.bssid ?? "n/a"}`);
      lines.push(`Channel: ${d.channel ?? "n/a"}`);
      lines.push(`Freq: ${d.freq_mhz ?? "n/a"} MHz`);
      lines.push(`Signal: ${fmtSignal(d.signal)}`);
      lines.push(`Security: ${d.security ?? "n/a"}`);
    }
    elSel.textContent = lines.join("\n");
  }

  // ---------- drawing ----------
  function drawGlowLine(x1,y1,x2,y2,alpha,thick){
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalAlpha = alpha;
    ctx.lineWidth = thick;
    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.lineTo(x2,y2);
    ctx.stroke();
  }

  function drawNode(x,y,r,kind,selected,phase){
    ctx.save();
    ctx.translate(x,y);
    ctx.globalCompositeOperation = "lighter";

    const pulse = 0.55 + 0.45 * Math.sin(phase);
    const base = r;

    // outer glow
    ctx.globalAlpha = 0.10 + (selected ? 0.14 : 0.0);
    ctx.beginPath();
    ctx.arc(0,0, base*3.2*pulse, 0, Math.PI*2);
    ctx.fill();

    // mid glow ring
    ctx.globalAlpha = 0.18 + (selected ? 0.12 : 0.0);
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(0,0, base*1.6*pulse, 0, Math.PI*2);
    ctx.stroke();

    // core
    ctx.globalAlpha = selected ? 0.9 : 0.72;
    ctx.beginPath();
    ctx.arc(0,0, base, 0, Math.PI*2);
    ctx.fill();

    // scanner special mark
    if (kind === "scanner") {
      ctx.globalAlpha = 0.7;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(0,0, base*1.15, 0, Math.PI*2);
      ctx.stroke();

      ctx.globalAlpha = 0.45;
      ctx.beginPath();
      ctx.arc(0,0, base*2.4, 0, Math.PI*2);
      ctx.stroke();
    }

    ctx.restore();
  }

  function drawGrid(w,h,t){
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.strokeStyle = "rgba(120,255,255,.25)";
    ctx.fillStyle = "rgba(120,255,255,.10)";
    ctx.lineWidth = 1;

    // plane at y=140 (screen-space-ish), but projected as a faux 3D grid
    const spacing = 60;
    const size = 900;
    const yPlane = 140;

    // animate a subtle grid drift
    const drift = (t * 0.02) % spacing;

    // build grid lines in world space and project
    const lines = [];
    for (let x = -size; x <= size; x += spacing) {
      lines.push([{x:x+drift, y:yPlane, z:-size},{x:x+drift, y:yPlane, z:size}]);
    }
    for (let z = -size; z <= size; z += spacing) {
      lines.push([{x:-size, y:yPlane, z:z+drift},{x:size, y:yPlane, z:z+drift}]);
    }

    ctx.beginPath();
    for (const [a,b] of lines) {
      const ca = toCameraSpace(a);
      const cb = toCameraSpace(b);
      // clip behind camera
      if (ca.z < 20 || cb.z < 20) continue;
      const pa = project(ca, w, h);
      const pb = project(cb, w, h);
      ctx.moveTo(pa.sx, pa.sy);
      ctx.lineTo(pb.sx, pb.sy);
    }
    ctx.stroke();

    // faint center circle
    ctx.globalAlpha = 0.18;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(w*0.5, h*0.5, 240 + 14*Math.sin(t*0.001), 0, Math.PI*2);
    ctx.stroke();

    ctx.restore();
  }

  function render(t) {
    const { w, h } = fitCanvas();
    cam.cx = w * 0.5;
    cam.cy = h * 0.5;

    // smooth camera
    cam.yaw = lerp(cam.yaw, cam.targetYaw, 0.12);
    cam.pitch = lerp(cam.pitch, cam.targetPitch, 0.12);
    cam.dist = lerp(cam.dist, cam.targetDist, 0.12);

    ctx.clearRect(0,0,w,h);

    // holographic palette
    ctx.fillStyle = "rgba(0,255,255,.85)";
    ctx.strokeStyle = "rgba(0,255,255,.55)";

    drawGrid(w,h,t);

    // project nodes
    const projected = [];
    pickList = [];

    for (const n of graph.nodes) {
      const c = toCameraSpace(n);
      if (c.z < 20) continue;
      const p = project(c, w, h);
      projected.push({ n, c, p });
    }

    // painter's algorithm by depth (far -> near)
    projected.sort((a,b) => b.c.z - a.c.z);

    // edges (draw behind nodes)
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (const e of graph.edges) {
      const a = projected.find(pp => pp.n.id === e.a);
      const b = projected.find(pp => pp.n.id === e.b);
      if (!a || !b) continue;

      const pulse = 0.45 + 0.55 * Math.sin(t*0.002 + hash32(e.a + e.b) * 0.00001);
      const baseA = e.kind === "interf" ? 0.08 : 0.12;
      const baseB = e.kind === "interf" ? 0.22 : 0.32;

      // glow layer
      ctx.strokeStyle = e.kind === "interf" ? "rgba(255,0,255,.45)" : "rgba(0,255,255,.45)";
      drawGlowLine(a.p.sx, a.p.sy, b.p.sx, b.p.sy, baseA * pulse, 6);

      // core
      ctx.strokeStyle = e.kind === "interf" ? "rgba(255,0,255,.75)" : "rgba(0,255,255,.75)";
      drawGlowLine(a.p.sx, a.p.sy, b.p.sx, b.p.sy, baseB * pulse, 1.5);
    }
    ctx.restore();

    // nodes
    for (const pp of projected) {
      const { n, p } = pp;
      const selected = (graph.selectedId === n.id);

      const r = (n.size || 10) * (0.75 + p.s * 0.45);
      const phase = t*0.003 + (hash32(n.id) % 1000) * 0.01;

      ctx.fillStyle = n.kind === "scanner" ? "rgba(0,255,255,.85)" : "rgba(0,255,255,.7)";
      if (n.kind !== "scanner") ctx.fillStyle = "rgba(0,255,255,.65)";
      if (selected) ctx.fillStyle = "rgba(255,0,255,.85)";

      ctx.strokeStyle = selected ? "rgba(255,0,255,.85)" : "rgba(0,255,255,.6)";

      drawNode(p.sx, p.sy, r, n.kind, selected, phase);

      // label
      if (p.s > 0.55 || selected) {
        ctx.save();
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = selected ? 0.92 : 0.65;
        ctx.fillStyle = selected ? "rgba(255,225,255,.92)" : "rgba(200,255,255,.8)";
        ctx.font = `${Math.max(11, Math.min(15, 12 * p.s))}px ui-sans-serif, system-ui`;
        ctx.textBaseline = "middle";
        ctx.fillText(n.label, p.sx + r + 10, p.sy);
        ctx.restore();
      }

      // register for picking
      pickList.push({ id: n.id, x: p.sx, y: p.sy, r: Math.max(12, r*1.2) });
    }

    requestAnimationFrame(render);
  }

  // ---------- networking ----------
  const API = "/api/networks/latest";

  async function fetchLatest() {
    spinner.style.display = 'block';
    const t0 = nowMs();
    try {
      const res = await fetch(API, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const networks = Array.isArray(data.networks) ? data.networks : [];
      graph.meta = {
        generated_at: data.generated_at || "",
        iface: data.iface || "",
        backend: data.backend || "",
      };

      const { nodes, edges } = buildLayout(networks);
      graph.nodes = nodes;
      graph.edges = edges;

      graph.lastFetchOk = true;
      graph.lastFetchAt = Date.now();

      if (graph.selectedId) showSelection(graph.selectedId);
      else showSelection("__scanner__");

      const ms = Math.round(nowMs() - t0);
      setStatus(`OK • ${networks.length} networks • ${graph.meta.iface || "iface?"} • ${ms}ms`);
    } catch (e) {
      graph.lastFetchOk = false;
      setStatus(`Waiting for scan data… (${String(e.message || e)})`);
    } finally {
      spinner.style.display = 'none';
    }
  }

  function startAuto() {
    const tick = async () => {
      if (chkAuto.checked) await fetchLatest();
      const sec = clamp(Number(inpInterval.value || 2), 1, 30);
      setTimeout(tick, sec * 1000);
    };
    tick();
  }

  btnReload.addEventListener("click", () => fetchLatest());

  // Filter buttons
  btnFilterWPA2.addEventListener("click", () => {
    graph.filter = 'wpa2';
    fetchLatest();
  });
  btnFilterOpen.addEventListener("click", () => {
    graph.filter = 'open';
    fetchLatest();
  });
  btnFilterAll.addEventListener("click", () => {
    graph.filter = null;
    fetchLatest();
  });

  // Export button
  btnExport.addEventListener("click", () => {
    const data = {
      meta: graph.meta,
      networks: graph.nodes.filter(n => n.kind === 'ap').map(n => n.data)
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wifi_scan_export.json';
    a.click();
    URL.revokeObjectURL(url);
  });

  // Theme toggle
  btnTheme.addEventListener("click", () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    html.setAttribute('data-theme', current === 'light' ? 'dark' : 'light');
  });

  // Accessibility: keyboard navigation
  window.addEventListener("keydown", (e) => {
    if (e.key === "r" || e.key === "R") resetView();
    if (e.key === "Tab") {
      e.preventDefault();
      const nodes = graph.nodes.filter(n => n.kind === 'ap');
      if (nodes.length === 0) return;
      const currentIndex = nodes.findIndex(n => n.id === graph.selectedId);
      const nextIndex = (currentIndex + 1) % nodes.length;
      graph.selectedId = nodes[nextIndex].id;
      showSelection(graph.selectedId);
    }
  });

  // ---------- boot ----------
  window.addEventListener("resize", () => fitCanvas());
  resetView();
  fitCanvas();

  // initial selection = scanner
  graph.selectedId = "__scanner__";
  showSelection("__scanner__");

  fetchLatest();
  startAuto();
  requestAnimationFrame(render);
})();
