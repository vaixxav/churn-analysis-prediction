// ---------- radial gauge animation (predict result) ----------
function initGauge() {
  const ring = document.querySelector(".gauge-ring__fill");
  if (!ring) return;
  const pct = parseFloat(ring.dataset.pct || "0");
  const circumference = parseFloat(ring.dataset.circumference);
  const target = circumference * (1 - pct / 100);

  ring.style.strokeDashoffset = circumference;
  requestAnimationFrame(() => {
    ring.style.transition = "stroke-dashoffset 1.1s cubic-bezier(.16,.8,.3,1)";
    ring.style.strokeDashoffset = target;
  });
}

// ---------- hero signal wave (decorative, ambient) ----------
function initWave() {
  const svg = document.querySelector(".wave");
  if (!svg) return;
  const path = svg.querySelector("path");
  if (!path) return;

  const width = 400;
  const height = 90;
  const points = 40;
  let t = 0;

  function draw() {
    let d = `M0,${height / 2}`;
    for (let i = 0; i <= points; i++) {
      const x = (width / points) * i;
      const y =
        height / 2 +
        Math.sin(i * 0.5 + t) * 14 * Math.sin(i / points * Math.PI) +
        Math.sin(i * 0.9 + t * 1.4) * 6 * Math.sin(i / points * Math.PI);
      d += ` L${x},${y}`;
    }
    path.setAttribute("d", d);
    t += 0.025;
    requestAnimationFrame(draw);
  }
  draw();
}

// ---------- mobile nav toggle ----------
function initNavToggle() {
  const topbar = document.querySelector(".topbar__inner");
  const nav = document.querySelector(".nav");
  if (!topbar || !nav) return;
  if (window.innerWidth > 880) return;

  const toggle = document.createElement("button");
  toggle.className = "nav-toggle";
  toggle.setAttribute("aria-label", "Toggle navigation");
  toggle.innerHTML = "&#9776;";
  toggle.style.cssText =
    "background:none;border:1px solid var(--border-glass-strong);color:var(--text-primary);border-radius:8px;padding:8px 12px;font-size:1rem;cursor:pointer;";
  topbar.appendChild(toggle);

  nav.style.cssText =
    "display:none;position:absolute;top:100%;left:0;right:0;flex-direction:column;background:rgba(10,14,23,0.97);padding:12px 20px;border-bottom:1px solid var(--border-glass);";

  toggle.addEventListener("click", () => {
    nav.style.display = nav.style.display === "flex" ? "none" : "flex";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initGauge();
  initWave();
  initNavToggle();
});
