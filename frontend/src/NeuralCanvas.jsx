import React, { useEffect, useRef } from 'react';
import { REGIONS } from './constants';

export function NeuralCanvas({ activeRegions, globalGain, brainStatus }) {
  const canvasRef = useRef(null);
  const stateRef  = useRef(null);
  const rafRef    = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const W = () => canvas.width;
    const H = () => canvas.height;
    const N = 120;

    const nodes = Array.from({ length: N }, () => ({
      x: Math.random() * W(), y: Math.random() * H(),
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 2 + 1,
      regionIdx: Math.floor(Math.random() * REGIONS.length),
      spikeTimer: 0, phase: Math.random() * Math.PI * 2,
    }));

    nodes.forEach(n => {
      n.conn = Array.from({ length: 3 + Math.floor(Math.random() * 4) },
        () => Math.floor(Math.random() * N)
      );
    });

    stateRef.current = { nodes, t: 0 };

    const totalActivity = Object.values(activeRegions).reduce((a,b)=>a+b,0);
    const shouldAnimate = (brainStatus === 'ACTIVE' || brainStatus === 'RUNNING') && totalActivity > 1.0;

    const draw = () => {
      const { nodes, t } = stateRef.current;
      stateRef.current.t++;
      const w = W(), h = H();

      ctx.fillStyle = "rgba(9,9,11,0.18)";
      ctx.fillRect(0, 0, w, h);

      nodes.forEach(nd => {
        nd.phase += 0.02;
        nd.x += nd.vx; nd.y += nd.vy;
        if (nd.x < 0 || nd.x > w) nd.vx *= -1;
        if (nd.y < 0 || nd.y > h) nd.vy *= -1;
        if (nd.spikeTimer > 0) nd.spikeTimer--;

        const region = REGIONS[nd.regionIdx];
        const isActive = activeRegions[region.id] > 5;
        // Only generate stochastic spikes when we have a real backend activity
        if (shouldAnimate) {
          const spikeProb = (activeRegions[region.id] || region.baseAct) / 3000 * globalGain;
          if (Math.random() < spikeProb) nd.spikeTimer = 20;
        }

        const col = region.color;
        const hexRgb = c => [
          parseInt(c.slice(1,3),16),
          parseInt(c.slice(3,5),16),
          parseInt(c.slice(5,7),16),
        ].join(",");
        const rgb = hexRgb(col);

        nd.conn.forEach(ci => {
          const o = nodes[ci];
          const alpha = nd.spikeTimer > 0 ? 0.25 : 0.04;
          ctx.beginPath();
          ctx.moveTo(nd.x, nd.y);
          ctx.lineTo(o.x, o.y);
          ctx.strokeStyle = `rgba(${rgb},${alpha})`;
          ctx.lineWidth = nd.spikeTimer > 0 ? 0.6 : 0.3;
          ctx.stroke();

          if (nd.spikeTimer > 0) {
            const prog = (stateRef.current.t % 24) / 24;
            const px = nd.x + (o.x - nd.x) * prog;
            const py = nd.y + (o.y - nd.y) * prog;
            ctx.beginPath();
            ctx.arc(px, py, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${rgb},0.9)`;
            ctx.fill();
          }
        });

        if (nd.spikeTimer > 0) {
          const grad = ctx.createRadialGradient(nd.x, nd.y, 0, nd.x, nd.y, 8);
          grad.addColorStop(0, `rgba(${rgb},0.6)`);
          grad.addColorStop(1, "rgba(0,0,0,0)");
          ctx.beginPath();
          ctx.arc(nd.x, nd.y, 8, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();
        }
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2);
        ctx.fillStyle = nd.spikeTimer > 0 ? col : `rgba(${rgb},0.35)`;
        ctx.fill();
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    // If we should animate, start RAF loop; otherwise draw one static frame
    if (shouldAnimate) {
      rafRef.current = requestAnimationFrame(draw);
    } else {
      // static render: clear and draw nodes without stochastic spikes
      const { nodes } = stateRef.current;
      ctx.fillStyle = "rgba(9,9,11,0.18)";
      ctx.fillRect(0,0,W(),H());
      nodes.forEach(nd => {
        const region = REGIONS[nd.regionIdx];
        const rgb = (c => [parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)].join(','))(region.color);
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI*2);
        ctx.fillStyle = `rgba(${rgb},0.15)`;
        ctx.fill();
      });
    }
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [activeRegions, globalGain, brainStatus]);

  return (
    <canvas ref={canvasRef}
      style={{ width:"100%", height:"100%", display:"block" }} />
  );
}