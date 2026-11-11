// Toon people: flat 2D cartoon characters (thick ink outlines, round white heads, bean bodies, stick limbs)
// that live inside the 3D world as camera-facing cut-outs with real shadows.
// Tuned directly to match the @RicksClips3000 viral shorts screenshots.
import * as THREE from 'three';

export const INK = '#15141D';
const LW = 10;
const R2D = Math.PI / 180;

export function shadeOf(hex, k = 0.78) {
  const n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, gg = (n >> 8) & 255, b = n & 255;
  const f = (v) => Math.max(0, Math.min(255, Math.round(v * k)));
  return '#' + ((1 << 24) + (f(r) << 16) + (f(gg) << 8) + f(b)).toString(16).slice(1);
}

// ── Draw one 2D toon into any canvas context (512 x 1024 box, feet at y 920) ──
export function drawToon(g, look = {}, st = {}) {
  const L = {
    body: '#FFCC00', head: '#FFFFFF', hair: 'parted', hairCol: '#583622',
    zipper: true, belt: true, extra: [], neck: 'none', ...look
  };
  const S = {
    mood: 'neutral', look: [0, 0], blink: 0, talk: 0,
    armL: [14, 10], armR: [14, 10], legs: 'stand', phase: 0, lean: 0, bob: 0, squash: 0, ...st
  };

  g.save();
  g.lineCap = 'round'; g.lineJoin = 'round';
  if (S.flip) { g.translate(512, 0); g.scale(-1, 1); }

  const sit = S.legs === 'sit', dive = S.legs === 'dive', steer = S.legs === 'steer';
  const by = (sit ? 140 : (steer ? 130 : 0)) + (S.bob || 0) + (dive ? -50 : 0);
  const sq = 1 + (S.squash || 0);

  // Pivot at hips for leaning/diving so head and torso tilt naturally without swinging off canvas
  const FEET_Y = 920;
  const pivotY = (dive || S.lean) ? 570 : FEET_Y;
  const leanDeg = S.lean || (dive ? -8 : 0);
  g.translate(256, pivotY);
  g.rotate(leanDeg * R2D);
  g.translate(-256, -pivotY);

  // Proportions: Head r=116 at y=230, Torso top=340..bot=580, Legs 580..920
  const bx = 256, top = 340 + by, bot = 590 + by * 0.98, bw = 86;
  const hipY = bot - 22;

  // ── 1. Legs (Behind body) ──
  g.strokeStyle = INK; g.lineWidth = 14;
  const leg = (sx, side) => {
    let kx, ky, fx, fy;
    if (sit || steer) {
      const kx2 = sx + side * 36, ky2 = hipY + 70; fx = sx + side * 38; fy = FEET_Y;
      g.beginPath(); g.moveTo(sx, hipY); g.lineTo(kx2, ky2); g.lineTo(fx, fy); g.stroke();
      g.fillStyle = INK; g.beginPath(); g.ellipse(fx + side * 10, fy - 3, 20, 10, 0, 0, Math.PI * 2); g.fill();
      return;
    }
    if (dive) {
      // Pedestrian stumbling backward away from vehicle
      const kx2 = sx + side * 50 - 30, ky2 = hipY + 140;
      fx = sx + side * 80 - 40; fy = FEET_Y - (side < 0 ? 60 : 20);
      g.beginPath(); g.moveTo(sx, hipY); g.quadraticCurveTo(kx2, ky2, fx, fy); g.stroke();
      g.fillStyle = INK; g.beginPath(); g.ellipse(fx + side * 10, fy - 2, 20, 10, -0.4, 0, Math.PI * 2); g.fill();
      return;
    }
    if (S.legs === 'walk' || S.legs === 'run') {
      const amp = S.legs === 'run' ? 0.9 : 0.5, a = Math.sin(S.phase + (side > 0 ? Math.PI : 0)) * amp;
      const lift = Math.max(0, -Math.cos(S.phase + (side > 0 ? Math.PI : 0))) * 36;
      kx = sx + a * 20 + side * 6; ky = hipY + 160 - lift * 0.5;
      fx = sx + a * 30 + side * 8; fy = FEET_Y - lift;
    } else {
      kx = sx + side * 6; ky = hipY + 170; fx = sx + side * 12; fy = FEET_Y;
    }
    g.beginPath(); g.moveTo(sx, hipY); g.quadraticCurveTo(kx, ky, fx, fy); g.stroke();
    g.fillStyle = INK; g.beginPath(); g.ellipse(fx + side * 10, fy - 2, 20, 10, 0, 0, Math.PI * 2); g.fill();
  };
  leg(bx - 38, -1); leg(bx + 38, 1);

  // ── 2. Body (Smooth Bean Shape) ──
  const body = new Path2D();
  body.moveTo(bx - 52, top + 10);
  body.bezierCurveTo(bx - 74, top + 36, bx - bw - 4, bot - 100, bx - bw, bot - 42);
  body.bezierCurveTo(bx - bw + 4, bot + 6, bx + bw - 4, bot + 6, bx + bw, bot - 42);
  body.bezierCurveTo(bx + bw + 4, bot - 100, bx + 74, top + 36, bx + 52, top + 10);
  body.bezierCurveTo(bx + 26, top - 8, bx - 26, top - 8, bx - 52, top + 10);
  body.closePath();

  g.fillStyle = L.body; g.fill(body);
  g.save(); g.clip(body);

  // Soft curved volume highlight
  g.fillStyle = L.shade || shadeOf(L.body, 0.82); g.globalAlpha = 0.85;
  g.beginPath(); g.ellipse(bx + bw + 30, (top + bot) / 2 + 10, 60, 200, 0, 0, Math.PI * 2); g.fill();
  g.globalAlpha = 0.28; g.fillStyle = '#FFFFFF';
  g.beginPath(); g.ellipse(bx - 42, top + 70, 14, 44, 0.15, 0, Math.PI * 2); g.fill();
  g.globalAlpha = 1;

  // Center zipper line
  if (L.zipper) {
    g.strokeStyle = INK; g.lineWidth = 4.5;
    g.beginPath(); g.moveTo(bx, top + 6); g.lineTo(bx, bot - 22); g.stroke();
  }

  // Belt with silver buckle
  if (L.belt) {
    g.fillStyle = '#1D1E24'; g.fillRect(bx - bw, bot - 30, bw * 2, 18);
    g.strokeStyle = INK; g.lineWidth = 3.5; g.strokeRect(bx - bw, bot - 30, bw * 2, 18);
    // Silver buckle
    g.fillStyle = '#E2E4EB'; g.fillRect(bx - 14, bot - 34, 28, 26);
    g.strokeRect(bx - 14, bot - 34, 28, 26);
    g.fillStyle = '#1D1E24'; g.fillRect(bx - 7, bot - 27, 14, 12);
  }

  // Seatbelt across torso
  if (L.extra.includes('seatbelt') || st.seatbelt) {
    g.strokeStyle = '#15161C'; g.lineWidth = 28;
    g.beginPath(); g.moveTo(bx - 65, top + 12); g.lineTo(bx + 62, bot - 26); g.stroke();
    g.strokeStyle = '#3E414E'; g.lineWidth = 6;
    g.beginPath(); g.moveTo(bx - 63, top + 12); g.lineTo(bx + 60, bot - 26); g.stroke();
  }

  g.restore();
  g.strokeStyle = INK; g.lineWidth = LW; g.stroke(body);

  // ── 3. Arms ──
  const arm = (side, [a, e], hold) => {
    let sx = bx + side * 62, sy = top + 40;
    let hx, hy;
    if (steer) {
      hx = bx + side * 42; hy = top + 74;
      g.strokeStyle = INK; g.lineWidth = 14;
      g.beginPath(); g.moveTo(sx, sy); g.quadraticCurveTo(bx + side * 72, top + 64, hx, hy); g.stroke();
      g.fillStyle = INK; g.beginPath(); g.ellipse(hx, hy, 15, 16, 0, 0, Math.PI * 2); g.fill();
      return;
    }
    // Dynamic screaming / panic arm flail (matches screenshot 1)
    if (S.legs === 'dive' || S.mood === 'scream') {
      if (side < 0) {
        // Hand bent up touching cheek/head in panic
        a = 145; e = 65;
      } else {
        // Flung out in panic
        a = 125; e = 25;
      }
    }
    const u = 105, lo = 100;
    const a1 = a * R2D, a2 = (a + e) * R2D;
    const ex = sx + side * Math.sin(a1) * u, ey = sy + Math.cos(a1) * u;
    hx = ex + side * Math.sin(a2) * lo; hy = ey + Math.cos(a2) * lo;

    g.strokeStyle = INK; g.lineWidth = 14;
    g.beginPath(); g.moveTo(sx, sy); g.quadraticCurveTo(ex, ey, hx, hy); g.stroke();
    if (hold) { g.save(); hold(g, hx, hy, side * (a + e) * R2D, side); g.restore(); }
    g.fillStyle = INK; g.beginPath(); g.ellipse(hx, hy, 15, 16, 0, 0, Math.PI * 2); g.fill();
  };
  arm(-1, S.armL, S.holdL);
  arm(1, S.armR, S.holdR);

  // ── 4. Head ──
  const hx = 256, hy = 210 + by * 0.99, r = 118;
  g.save();
  g.translate(hx, hy); g.scale(1 + (S.squash || 0) * -0.25, sq); g.translate(-hx, -hy);

  // White circular face
  g.fillStyle = L.head;
  g.beginPath(); g.arc(hx, hy, r, 0, Math.PI * 2); g.fill();
  g.strokeStyle = INK; g.lineWidth = LW; g.stroke();

  // Face features & accessories
  drawFace(g, L, S, hx, hy, r);

  // Hair & hats (with ample headroom)
  drawHair(g, L, hx, hy, r);

  g.restore();
  g.restore();
}

function drawFace(g, L, S, hx, hy, r) {
  const m = S.mood, ex = 40, ey = hy + 6;
  const [lx, ly] = S.look;

  // Eyebrows
  const brow = {
    neutral: [4, 0], smug: [-6, 12], happy: [6, 0], laugh: [8, 0],
    shock: [24, 0], scream: [26, -14], worried: [8, -16], angry: [-10, 22],
    sly: [-6, 14], deadpan: [2, 0], tired: [-2, 0]
  }[m] || [4, 0];

  g.strokeStyle = INK; g.lineWidth = 11;
  [-1, 1].forEach((s) => {
    let lift = brow[0], tilt = brow[1] * s;
    if ((m === 'smug' || m === 'sly') && s > 0) { lift = 16; tilt = -4; }
    const y = ey - 40 - lift;
    g.beginPath();
    g.moveTo(hx + s * (ex - 22), y + tilt * 0.5);
    g.quadraticCurveTo(hx + s * ex, y - 5, hx + s * (ex + 22), y - tilt * 0.5);
    g.stroke();
  });

  // Eyes
  if (L.extra.includes('aviator')) {
    drawAviators(g, hx, ey);
  } else {
    drawEyes(g, hx, ey, ex, S, m, lx, ly, L);
  }

  // Glasses / Airpod
  if (L.extra.includes('glasses') && !L.extra.includes('aviator')) {
    g.strokeStyle = INK; g.lineWidth = 4.5;
    [-1, 1].forEach((s) => { g.beginPath(); g.arc(hx + s * ex, ey, 24, 0, 7); g.stroke(); });
    g.beginPath(); g.moveTo(hx - 14, ey - 3); g.lineTo(hx + 14, ey - 3); g.stroke();
  }
  if (L.extra.includes('airpod')) {
    g.fillStyle = '#FFFFFF'; g.strokeStyle = INK; g.lineWidth = 3;
    const ax = hx - 118, ay = hy + 6;
    g.beginPath(); g.ellipse(ax, ay, 8, 11, 0.2, 0, Math.PI * 2); g.fill(); g.stroke();
    g.fillRect(ax - 2, ay + 5, 4, 12); g.strokeRect(ax - 2, ay + 5, 4, 12);
  }

  // Mouth
  drawMouth(g, hx, ey + 52, m, S.talk);

  // Flying sweat teardrop (Screenshot 1)
  if (S.sweat || m === 'worried' || m === 'scream' || m === 'shock') {
    const k = S.sweat ?? 1;
    g.globalAlpha = Math.min(1, k);
    g.fillStyle = '#7ED2FC'; g.strokeStyle = INK; g.lineWidth = 3.5;
    const sx = hx + 88, sy = hy - 56;
    g.beginPath();
    g.moveTo(sx, sy - 20);
    g.quadraticCurveTo(sx + 15, sy, sx, sy + 10);
    g.quadraticCurveTo(sx - 15, sy, sx, sy - 20);
    g.fill(); g.stroke();
    g.globalAlpha = 1;
  }
}

function drawEyes(g, hx, ey, ex, S, m, lx, ly, L) {
  g.fillStyle = INK; g.strokeStyle = INK;
  if (m === 'scream' || m === 'panic') {
    // Wide panicked curved eyes (^ ^) from screenshot 1
    g.lineWidth = 9;
    [-1, 1].forEach((s) => {
      g.beginPath();
      g.arc(hx + s * ex, ey + 4, 15, Math.PI * 1.15, Math.PI * 1.85);
      g.stroke();
    });
    return;
  }
  if (m === 'shock') {
    [-1, 1].forEach((s) => {
      g.fillStyle = '#FFFFFF'; g.lineWidth = 5;
      g.beginPath(); g.ellipse(hx + s * ex, ey, 22, 26, 0, 0, 7); g.fill(); g.stroke();
      g.fillStyle = INK; g.beginPath(); g.arc(hx + s * ex + lx * 7, ey + ly * 7, 7, 0, 7); g.fill();
    });
    return;
  }
  // Standard eyes
  [-1, 1].forEach((s) => {
    const x = hx + s * ex, y = ey;
    const px = x + lx * 8, py = y + ly * 7;
    g.beginPath(); g.ellipse(px, py, 11, 14, 0, 0, Math.PI * 2); g.fill();

    // Heavy eyelid for smug / deadpan / sly
    if (m === 'smug' || m === 'sly' || m === 'deadpan') {
      g.fillStyle = L.head; g.fillRect(x - 20, y - 24, 40, 22);
      g.lineWidth = 6; g.beginPath(); g.moveTo(x - 17, y - 2); g.lineTo(x + 17, y - 2); g.stroke();
    }
  });
}

function drawAviators(g, hx, ey) {
  g.strokeStyle = '#CCA01A'; g.lineWidth = 4.5;
  g.fillStyle = '#1D2026';
  [-1, 1].forEach((s) => {
    const cx = hx + s * 38;
    g.beginPath();
    g.moveTo(cx - 24, ey - 15);
    g.lineTo(cx + 24, ey - 15);
    g.bezierCurveTo(cx + 28, ey + 15, cx + 15, ey + 28, cx, ey + 29);
    g.bezierCurveTo(cx - 15, ey + 28, cx - 28, ey + 15, cx - 24, ey - 15);
    g.closePath();
    g.fill(); g.stroke();
    g.strokeStyle = 'rgba(255,255,255,0.4)'; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(cx - 12, ey - 8); g.lineTo(cx - 20, ey + 15); g.stroke();
  });
  g.strokeStyle = '#CCA01A'; g.lineWidth = 3.5;
  g.beginPath(); g.moveTo(hx - 15, ey - 15); g.lineTo(hx + 15, ey - 15); g.stroke();
  g.beginPath(); g.moveTo(hx - 14, ey - 6); g.lineTo(hx + 14, ey - 6); g.stroke();
}

function drawMouth(g, hx, my, m, talk = 0) {
  g.strokeStyle = INK; g.fillStyle = INK; g.lineWidth = 7;
  if (m === 'scream' || m === 'shock') {
    // Large screaming open mouth with white flat teeth and arched pink tongue (Screenshot 1)
    const w = 30, h = 38 + talk * 8;
    g.beginPath(); g.ellipse(hx, my + 8, w, h, 0, 0, Math.PI * 2);
    g.fillStyle = '#26121D'; g.fill(); g.stroke();
    g.save();
    g.beginPath(); g.ellipse(hx, my + 8, w, h, 0, 0, Math.PI * 2); g.clip();
    // Teeth on top
    g.fillStyle = '#FFFFFF'; g.fillRect(hx - 24, my - 24, 48, 14);
    // Tongue at bottom
    g.fillStyle = '#E85870'; g.beginPath(); g.ellipse(hx, my + 30, 22, 18, 0, 0, Math.PI * 2); g.fill();
    g.restore();
    return;
  }
  if (m === 'smug' || m === 'sly') {
    // Sharp devious side smirk with teeth line (Screenshot 2)
    g.beginPath(); g.moveTo(hx - 20, my + 4);
    g.quadraticCurveTo(hx + 6, my + 18, hx + 26, my - 6); g.stroke();
    g.beginPath(); g.moveTo(hx + 20, my - 10); g.lineTo(hx + 26, my - 4); g.stroke();
    return;
  }
  if (m === 'deadpan') {
    g.beginPath(); g.moveTo(hx - 16, my + 4); g.lineTo(hx + 16, my + 4); g.stroke();
    return;
  }
  if (m === 'worried') {
    g.beginPath(); g.moveTo(hx - 22, my + 6);
    g.bezierCurveTo(hx - 8, my - 4, hx + 6, my + 14, hx + 22, my + 4); g.stroke();
    return;
  }
  if (talk > 0.05) {
    g.beginPath(); g.ellipse(hx, my + 4, 15, 8 + talk * 14, 0, 0, 7);
    g.fillStyle = '#26121D'; g.fill(); g.stroke();
    return;
  }
  g.beginPath(); g.moveTo(hx - 18, my + 2); g.quadraticCurveTo(hx, my + 12, hx + 18, my + 2); g.stroke();
}

function drawHair(g, L, hx, hy, r) {
  const col = L.hairCol || '#583622';
  g.fillStyle = col; g.strokeStyle = INK; g.lineWidth = LW;

  if (L.hair === 'slick') {
    // Slicked back hair cleanly conforming to skull (Screenshot 2 right)
    g.beginPath();
    g.moveTo(hx - r * 0.92, hy - 10);
    g.bezierCurveTo(hx - r * 0.94, hy - r * 0.75, hx - 20, hy - r * 1.05, hx + r * 0.25, hy - r * 1.02);
    g.bezierCurveTo(hx + r * 0.9, hy - r * 0.82, hx + r * 0.98, hy - 5, hx + r * 0.85, hy + 18);
    g.bezierCurveTo(hx + r * 0.65, hy - 32, hx + 36, hy - r * 0.55, hx - 8, hy - r * 0.6);
    g.bezierCurveTo(hx - 55, hy - r * 0.6, hx - r * 0.82, hy - 10, hx - r * 0.92, hy - 10);
    g.closePath();
    g.fill(); g.stroke();
  } else if (L.hair === 'wavy') {
    // Voluminous wavy hair (Driver in screenshot 4)
    g.beginPath();
    g.moveTo(hx - r * 0.92, hy + 8);
    g.bezierCurveTo(hx - r * 1.05, hy - r * 0.5, hx - r * 0.55, hy - r * 1.05, hx, hy - r * 1.02);
    g.bezierCurveTo(hx + r * 0.65, hy - r * 1.05, hx + r * 1.02, hy - r * 0.45, hx + r * 0.92, hy + 8);
    g.bezierCurveTo(hx + r * 0.7, hy - 24, hx + 50, hy - r * 0.5, hx, hy - r * 0.55);
    g.bezierCurveTo(hx - 45, hy - r * 0.6, hx - r * 0.7, hy - 18, hx - r * 0.92, hy + 8);
    g.closePath();
    g.fill(); g.stroke();
  } else if (L.hair === 'cap_backward') {
    // Red backwards cap with visor (Trucker in screenshot 3)
    g.fillStyle = L.hatCol || '#D8243A';
    g.beginPath();
    g.arc(hx, hy - 16, r * 0.96, Math.PI * 0.9, Math.PI * 2.1);
    g.closePath(); g.fill(); g.stroke();
    // Visor flap
    g.fillStyle = shadeOf(L.hatCol || '#D8243A', 0.8);
    g.beginPath(); g.ellipse(hx, hy + 32, 50, 16, 0, 0, Math.PI); g.fill(); g.stroke();
  } else {
    // Parted brown bowl / fringe hair (Screenshot 1 & 2 left)
    g.beginPath();
    g.moveTo(hx - r * 0.92, hy - 8);
    g.bezierCurveTo(hx - r * 0.94, hy - r * 0.78, hx - 26, hy - r * 1.04, hx, hy - r * 1.0);
    g.bezierCurveTo(hx + 36, hy - r * 0.98, hx + r * 0.92, hy - r * 0.78, hx + r * 0.9, hy - 8);
    g.bezierCurveTo(hx + r * 0.66, hy - 32, hx + 28, hy - r * 0.58, hx - 8, hy - r * 0.62);
    g.bezierCurveTo(hx - 46, hy - r * 0.62, hx - r * 0.7, hy - 16, hx - r * 0.92, hy - 8);
    g.closePath();
    g.fill(); g.stroke();

    // Fringe stroke lines
    g.strokeStyle = INK; g.lineWidth = 4.5;
    g.beginPath(); g.moveTo(hx - 26, hy - r * 0.88); g.lineTo(hx - 14, hy - r * 0.64); g.stroke();
    g.beginPath(); g.moveTo(hx + 10, hy - r * 0.88); g.lineTo(hx + 18, hy - r * 0.64); g.stroke();
  }
}

// ── Handheld & Scenery Props ──
export const CAST = {
  driver: { body: '#C92A2A', hair: 'wavy', hairCol: '#181622', extra: ['airpod', 'seatbelt'], zipper: false },
  scammer: { body: '#1E2C48', hair: 'slick', hairCol: '#181622', extra: [], zipper: true },
  diver: { body: '#FFCC00', hair: 'parted', hairCol: '#5C3826', extra: [], zipper: true },
  coolguy: { body: '#E5A912', hair: 'parted', hairCol: '#5C3826', extra: ['aviator', 'belt'], zipper: true },
  trucker: { body: '#24262E', hair: 'cap_backward', hatCol: '#D8243A', extra: ['aviator'], zipper: true },
  carrier: { body: '#4E8C34', hair: 'parted', hairCol: '#5C3826', extra: [], zipper: true }
};

export const PROPS = {
  paidHammer(g, x, y, rot = 0) {
    g.save(); g.translate(x, y); g.rotate(rot);
    g.fillStyle = '#D9A464'; g.strokeStyle = INK; g.lineWidth = 6;
    g.fillRect(-5, -100, 10, 100); g.strokeRect(-5, -100, 10, 100);
    g.fillStyle = '#D9383A';
    g.fillRect(-50, -154, 100, 54); g.strokeRect(-50, -154, 100, 54);
    g.fillStyle = '#FFFFFF'; g.fillRect(-42, -146, 84, 38);
    g.fillStyle = '#D9383A'; g.font = '900 28px Inter, sans-serif';
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('PAID', 0, -127);
    g.restore();
  },

  briefcase(g, x, y, rot = 0) {
    g.save(); g.translate(x, y); g.rotate(rot);
    g.fillStyle = '#94532B'; g.strokeStyle = INK; g.lineWidth = 5;
    g.beginPath(); g.roundRect(-38, -46, 76, 50, 7); g.fill(); g.stroke();
    g.fillStyle = '#E8C85A';
    g.fillRect(-24, -48, 10, 14); g.fillRect(14, -48, 10, 14);
    g.strokeStyle = INK; g.lineWidth = 4.5;
    g.beginPath(); g.arc(0, -52, 12, Math.PI, 0); g.stroke();
    g.restore();
  },

  cashbox(g, x, y, rot = 0) {
    g.save(); g.translate(x, y); g.rotate(rot);
    g.fillStyle = '#C92A2A'; g.strokeStyle = INK; g.lineWidth = 5;
    g.beginPath(); g.roundRect(-40, -32, 80, 40, 6); g.fill(); g.stroke();
    g.fillStyle = '#E0E0E6'; g.fillRect(-10, -24, 20, 12);
    g.restore();
  },

  steeringWheel(g, x, y) {
    g.save(); g.translate(x, y);
    g.strokeStyle = '#22252B'; g.lineWidth = 14;
    g.beginPath(); g.arc(0, 0, 70, 0, Math.PI * 2); g.stroke();
    g.lineWidth = 6;
    g.beginPath(); g.moveTo(-70, 0); g.lineTo(70, 0); g.stroke();
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 70); g.stroke();
    g.fillStyle = '#1A1C22'; g.beginPath(); g.arc(0, 0, 24, 0, Math.PI * 2); g.fill(); g.stroke();
    g.restore();
  }
};

// ── 3D Toon Cut-out Mesh for Three.js ──
export class Toon {
  constructor(look = {}, { height = 1.85, res = 1024 } = {}) {
    this.look = { ...look };
    this.st = {};
    this.height = height;

    this.cv = document.createElement('canvas');
    this.cv.width = res / 2; this.cv.height = res;
    this.ctx = this.cv.getContext('2d');

    this.texture = new THREE.CanvasTexture(this.cv);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.generateMipmaps = false;
    this.texture.minFilter = THREE.LinearFilter;

    const w = height * (512 / 1024);
    const geo = new THREE.PlaneGeometry(w, height);
    geo.translate(0, height / 2, 0);

    const mat = new THREE.MeshStandardMaterial({
      map: this.texture,
      transparent: true,
      alphaTest: 0.05,
      roughness: 0.85,
      metalness: 0.05,
      side: THREE.DoubleSide
    });

    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = false;

    this.group = new THREE.Group();
    this.group.add(this.mesh);

    this.redraw();
  }

  set(st = {}) {
    this.st = { ...this.st, ...st };
    this.redraw();
    return this;
  }

  restyle(look = {}) {
    this.look = { ...this.look, ...look };
    this.redraw();
    return this;
  }

  at(x, y, z) {
    this.group.position.set(x, y, z);
    return this;
  }

  face(cam) {
    this.group.quaternion.copy(cam.quaternion);
    this.group.rotation.x = 0;
    this.group.rotation.z = 0;
    return this;
  }

  redraw() {
    this.ctx.clearRect(0, 0, this.cv.width, this.cv.height);
    drawToon(this.ctx, this.look, this.st);
    this.texture.needsUpdate = true;
  }
}
