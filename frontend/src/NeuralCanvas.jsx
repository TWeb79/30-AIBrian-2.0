import React, { useEffect, useRef } from 'react';
import { REGIONS } from './constants';

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v));
}

// A compact "brain map" layout: each region is a lobe/sector blob.
function makeRegionLayout(w, h) {
  const cx = w * 0.50;
  const cy = h * 0.50;
  const sx = Math.min(w, h) * 0.42;
  const sy = Math.min(w, h) * 0.34;

  // Normalize to a 0..1-ish space around brain ellipse.
  // Indices correspond to REGIONS ordering.
  const anchors = [
    // sensory, feature, association, predictive, concept
    { x: -0.35, y: -0.10, rx: 0.26, ry: 0.18 },
    { x: -0.15, y: -0.25, rx: 0.24, ry: 0.16 },
    { x:  0.00, y:  0.00, rx: 0.34, ry: 0.24 },
    { x:  0.25, y: -0.10, rx: 0.26, ry: 0.18 },
    { x:  0.10, y:  0.18, rx: 0.18, ry: 0.14 },

    // meta_control, working_memory, cerebellum, brainstem, reflex_arc
    { x:  0.28, y:  0.18, rx: 0.22, ry: 0.15 },
    { x: -0.05, y:  0.22, rx: 0.26, ry: 0.16 },
    { x: -0.35, y:  0.28, rx: 0.22, ry: 0.15 },
    { x:  0.05, y:  0.34, rx: 0.18, ry: 0.12 },
    { x:  0.40, y:  0.32, rx: 0.20, ry: 0.12 },
  ];

  return REGIONS.map((r, i) => {
    const a = anchors[i] || { x: 0, y: 0, rx: 0.22, ry: 0.16 };
    return {
      id: r.id,
      label: r.label,
      color: r.color,
      cx: cx + a.x * sx,
      cy: cy + a.y * sy,
      rx: a.rx * sx,
      ry: a.ry * sy,
    };
  });
}

function drawBrainSilhouette(ctx, w, h) {
  // Deep dark background
  ctx.fillStyle = '#05060a';
  ctx.fillRect(0, 0, w, h);

  const cx = w * 0.5;
  const cy = h * 0.52;
  const rx = Math.min(w, h) * 0.46;
  const ry = Math.min(w, h) * 0.36;

  // Outer glow
  const glow = ctx.createRadialGradient(cx, cy, 10, cx, cy, Math.max(rx, ry) * 1.25);
  glow.addColorStop(0.0, 'rgba(34,211,238,0.10)');
  glow.addColorStop(0.6, 'rgba(34,211,238,0.04)');
  glow.addColorStop(1.0, 'rgba(0,0,0,0)');
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx * 1.05, ry * 1.10, 0, 0, Math.PI * 2);
  ctx.fill();

  // Brain body
  const bodyGrad = ctx.createLinearGradient(0, cy - ry, 0, cy + ry);
  bodyGrad.addColorStop(0.0, 'rgba(18,24,35,0.95)');
  bodyGrad.addColorStop(1.0, 'rgba(7,10,18,0.98)');
  ctx.fillStyle = bodyGrad;
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Subtle folds (gyri)
  ctx.save();
  ctx.globalAlpha = 0.10;
  ctx.strokeStyle = 'rgba(148,163,184,0.35)';
  ctx.lineWidth = 1;
  for (let i = 0; i < 8; i++) {
    const t = i / 7;
    ctx.beginPath();
    ctx.ellipse(cx - rx * 0.05, cy, rx * (0.85 - t * 0.22), ry * (0.75 - t * 0.18), 0, Math.PI * 0.12, Math.PI * 1.85);
    ctx.stroke();
  }
  ctx.restore();
}

function drawRegionBlob(ctx, region, activityPct, gain, t) {
  const { r, g, b } = hexToRgb(region.color);

  // Normalize activity to 0..1 (UI is ~0..60%)
  const a = clamp((activityPct || 0) / 60, 0, 1);
  const pulse = 0.5 + 0.5 * Math.sin(t * 0.02 + (region.cx + region.cy) * 0.002);
  const hot = clamp(a * (0.7 + 0.6 * (gain - 1) / 4) + 0.20 * pulse * a, 0, 1);

  // Base fill
  ctx.save();
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = `rgba(${r},${g},${b},${0.08 + 0.12 * a})`;
  ctx.beginPath();
  ctx.ellipse(region.cx, region.cy, region.rx, region.ry, 0, 0, Math.PI * 2);
  ctx.fill();

  // Shiny highlight glow (additive)
  ctx.globalCompositeOperation = 'lighter';
  const glow = ctx.createRadialGradient(region.cx, region.cy, 1, region.cx, region.cy, Math.max(region.rx, region.ry) * 1.2);
  glow.addColorStop(0.0, `rgba(${r},${g},${b},${0.20 + 0.55 * hot})`);
  glow.addColorStop(0.45, `rgba(${r},${g},${b},${0.06 + 0.22 * hot})`);
  glow.addColorStop(1.0, 'rgba(0,0,0,0)');
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.ellipse(region.cx, region.cy, region.rx * (1.05 + 0.06 * pulse), region.ry * (1.05 + 0.06 * pulse), 0, 0, Math.PI * 2);
  ctx.fill();

  // Outline
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = `rgba(${r},${g},${b},${0.18 + 0.40 * hot})`;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.ellipse(region.cx, region.cy, region.rx, region.ry, 0, 0, Math.PI * 2);
  ctx.stroke();

  // Label (dim)
  ctx.fillStyle = `rgba(248,250,252,${0.45})`;
  ctx.font = '10px Inter, system-ui, -apple-system, Segoe UI, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const short = region.label.split(' ')[0].toUpperCase();
  ctx.fillText(short, region.cx, region.cy);
  ctx.restore();
}

function drawSpikes(ctx, layout, activeRegions, globalGain, t, shouldAnimate) {
  // small sparkles inside active regions
  if (!shouldAnimate) return;

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (const r of layout) {
    const act = activeRegions[r.id] || 0;
    const p = clamp((act / 60) * (globalGain / 2), 0, 1);
    const n = Math.floor(2 + 10 * p);
    const { r: rr, g, b } = hexToRgb(r.color);
    for (let i = 0; i < n; i++) {
      if (Math.random() > p) continue;
      const ang = Math.random() * Math.PI * 2;
      const rad = Math.random();
      const x = r.cx + Math.cos(ang) * r.rx * 0.75 * rad;
      const y = r.cy + Math.sin(ang) * r.ry * 0.75 * rad;
      const size = 0.8 + Math.random() * 1.6;
      const a = 0.25 + 0.55 * p;

      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${rr},${g},${b},${a})`;
      ctx.fill();
    }
  }
  ctx.restore();
}

export function NeuralCanvas({ activeRegions, globalGain, brainStatus }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const layoutRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      layoutRef.current = makeRegionLayout(canvas.width, canvas.height);
    };
    resize();
    window.addEventListener('resize', resize);

    let t = 0;
    const totalActivity = Object.values(activeRegions).reduce((a, b) => a + b, 0);
    const shouldAnimate = (brainStatus === 'ACTIVE' || brainStatus === 'RUNNING') && totalActivity > 1.0;

    const draw = () => {
      t++;
      const w = canvas.width;
      const h = canvas.height;
      const layout = layoutRef.current || makeRegionLayout(w, h);

      drawBrainSilhouette(ctx, w, h);

      // Draw regions (blobs)
      for (const r of layout) {
        drawRegionBlob(ctx, r, activeRegions[r.id] || 0, globalGain, t);
      }

      // draw micro-spikes
      drawSpikes(ctx, layout, activeRegions, globalGain, t, shouldAnimate);

      rafRef.current = requestAnimationFrame(draw);
    };

    // always animate lightly; it looks alive and allows shiny highlights.
    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [activeRegions, globalGain, brainStatus]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block', background: '#05060a' }}
    />
  );
}