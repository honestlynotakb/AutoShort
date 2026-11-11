// Dashcam 3D Style Sheet (1920x1080):
// Every frame and asset is drawn by the style's own Three.js engine and 2D toon kit.
import * as THREE from 'three';
import { ctx } from './core/lib.js';
import { startBoard, panel, frame, small, rules } from './core/board.js';
import { makeEngine, camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as CARS from './core/cars.js';
import { Toon, drawToon, PROPS, CAST } from './core/toon.js';
import { captionText } from './core/captions.js';

await document.fonts.load('900 40px Inter');
await document.fonts.load('800 40px Inter');
await document.fonts.load('700 40px Caladea');

const GL = document.getElementById('gl'), GL2 = document.getElementById('gl2');
GL.width = 648; GL.height = 1152;
const E = makeEngine(GL, { w: 648, h: 1152, samples: 0 });
const E2 = makeEngine(GL2, { w: 1280, h: 860, samples: 0 });
const cam = camera(35);

const B = startBoard(document.getElementById('cv'), {
  title: 'DASHCAM 3D: VIDEO STYLE SHEET',
  author: 'FACELESS SHORTS · 2026',
  bg: '#14151B',
  line: '#343844',
  head: '#FFF6E6',
  accent: '#FF4747'
});

const shot = (x, y, w, renderFn, over) => frame(x, y, w, () => {
  renderFn();
  ctx.drawImage(GL, 0, 0, 1080, 1920);
  if (over) over();
});

const wide = (box, renderFn, over) => {
  renderFn();
  B.save();
  B.beginPath();
  B.roundRect(box.x, box.y, box.w, box.h, 12);
  B.clip();
  B.drawImage(GL2, box.x, box.y, box.w, box.h);
  B.restore();
  if (over) over();
};

// ═════════════════════════ 1 · HERO FRAME ═════════════════════════
let b = panel(20, 80, 540, 520, 1, 'HERO FRAME');
const H1 = WD.highway(E, { dusk: false });
const redCar = CARS.makeRedSportsCar();
redCar.group.position.set(1.4, 0, -2.8);
redCar.group.rotation.y = -0.2;
H1.scene.add(redCar.group);

const whiteSUV = CARS.makeWhiteSUV();
whiteSUV.group.position.set(-1.8, 0, -8.0);
H1.scene.add(whiteSUV.group);

const diver = new Toon(CAST.diver);
diver.at(0.2, 0, -2.6);
diver.set({ mood: 'scream', legs: 'dive', sweat: 1.0 });
H1.scene.add(diver.group);

const carrier = new Toon(CAST.carrier);
carrier.at(-0.7, 0, -3.2);
carrier.set({ mood: 'shock', holdR: PROPS.cashbox });
H1.scene.add(carrier.group);

shot(b.x + 4, b.y, 236, () => {
  cam.position.set(-0.2, 1.45, 1.8);
  cam.lookAt(0.1, 1.0, -2.8);
  diver.face(cam); carrier.face(cam);
  E.render(H1.scene, cam, { focus: 4.0, aperture: 0.0012, bloom: 0.25 });
}, () => captionText('hits', 540, 1340, 1.0));

[
  ['2D CARTOON PEOPLE', 'ink outlines & wild acting'],
  ['MODERN 3D VEHICLES', 'sedans, SUVs & pickups'],
  ['DASHCAM POV & RAIN', 'steering, wipers & red LED'],
  ['VIRAL DRIVING SCAMS', 'staged crashes & fraud'],
  ['1-2 WORD CAPTIONS', 'bold white with deep stroke']
].forEach(([a, c], i) => {
  small(a, b.x + 256, b.y + 36 + i * 86, 'left', 15, '#FFF6E6');
  small(c.toUpperCase(), b.x + 256, b.y + 60 + i * 86, 'left', 11, '#9AA0AC');
});

// ═════════════════════════ 2 · THE CAST ═════════════════════════
b = panel(570, 80, 690, 520, 2, 'THE CAST');
{
  const g = B; g.save();
  g.beginPath(); g.roundRect(b.x, b.y, b.w, b.h - 8, 12); g.clip();
  const gr = g.createLinearGradient(0, b.y, 0, b.y + b.h);
  gr.addColorStop(0, '#1E2C3D');
  gr.addColorStop(0.72, '#2C435A');
  gr.addColorStop(0.72, '#3E2E28');
  gr.addColorStop(1, '#241B18');
  g.fillStyle = gr; g.fillRect(b.x, b.y, b.w, b.h);

  const roles = [
    ['driver', 'THE DRIVER', { mood: 'deadpan', legs: 'steer' }],
    ['scammer', 'THE SCAMMER', { mood: 'smug', armR: [30, -84], holdR: PROPS.paidHammer }],
    ['diver', 'THE DIVER', { mood: 'scream', legs: 'dive', sweat: 1.0 }],
    ['coolguy', 'COOL GUY', { mood: 'smug', armL: [20, -70], armR: [20, -70] }],
    ['trucker', 'TRUCKER', { mood: 'sly', armL: [15, 20] }],
    ['carrier', 'ACCOMPLICE', { mood: 'shock', holdR: PROPS.cashbox }]
  ];

  roles.forEach(([k, name, st], i) => {
    g.save();
    g.translate(b.x + 8 + i * 110, b.y + 24);
    g.scale(0.21, 0.21);
    drawToon(g, CAST[k], st);
    g.restore();
    small(name, b.x + 60 + i * 110, b.y + b.h - 32, 'center', 11, '#FFF6E6');
  });
  g.restore();
  small('ROUND WHITE HEAD · EXPRESSIVE EYES · JACKET/HOODIE/SEATBELT · MODERN PROPS', b.x + b.w / 2, b.y + b.h + 6, 'center', 11, '#9AA0AC');
}

// ═════════════════════════ 3 · FACES DO THE ACTING ═════════════════════════
b = panel(1270, 80, 630, 520, 3, 'FACES DO THE ACTING');
{
  const moods = ['smug', 'scream', 'deadpan', 'shock', 'sly', 'worried', 'angry', 'laugh', 'happy', 'tired', 'panic', 'neutral'];
  moods.forEach((m, i) => {
    const cx = b.x + 52 + (i % 6) * 100, cy = b.y + 20 + Math.floor(i / 6) * 215;
    B.save();
    B.beginPath(); B.roundRect(cx - 46, cy, 92, 150, 10);
    B.fillStyle = '#22252E'; B.fill(); B.clip();
    B.translate(cx - 75, cy + 4); B.scale(0.29, 0.29);
    drawToon(B, CAST.driver, { mood: m, look: m === 'sly' ? [1, 0] : (m === 'deadpan' ? [0.6, 0] : [0, 0]), sweat: (m === 'worried' || m === 'scream') ? 1 : 0 });
    B.restore();
    small(m.toUpperCase(), cx, cy + 176, 'center', 13, '#FFF6E6');
  });
}

// ═════════════════════════ 4 · WORLDS ═════════════════════════
b = panel(20, 610, 760, 456, 4, 'WORLDS');
const sw = 206, sx = (i) => b.x + 14 + i * (sw + 40);

// World (A): Highway at Sunset (Screenshot 3)
const H2 = WD.highway(E, { dusk: true });
const carRed2 = CARS.makeRedSportsCar();
carRed2.group.position.set(-0.1, 0, -1.8);
H2.scene.add(carRed2.group);

const carCyan = CARS.makeCyanSUV();
carCyan.group.position.set(-0.85, 0, -5.5);
H2.scene.add(carCyan.group);

const truckBlack = CARS.makeBlackPickup();
truckBlack.group.position.set(0.95, 0, -4.0);
H2.scene.add(truckBlack.group);

const truckerOnHighway = new Toon(CAST.trucker);
truckerOnHighway.group.scale.setScalar(0.72);
truckerOnHighway.at(0.95, 1.25, -4.0);
truckerOnHighway.set({ mood: 'deadpan' });
H2.scene.add(truckerOnHighway.group);

shot(sx(0), b.y, sw, () => {
  cam.fov = 36; cam.updateProjectionMatrix();
  cam.position.set(-0.3, 3.4, -12.4);
  cam.lookAt(0.1, 1.2, -4.2);
  truckerOnHighway.face(cam);
  E.render(H2.scene, cam, { focus: 4.8, aperture: 0.0008, bloom: 0.45 });
});

// World (B): Suburban Driveway (Screenshot 2)
const D = WD.suburbanDriveway(E);
const carRed3 = CARS.makeRedSportsCar();
carRed3.group.position.set(-0.7, 0, -3.2); carRed3.group.rotation.y = Math.PI / 2 + 0.12;
D.scene.add(carRed3.group);

const coolGuy = new Toon(CAST.coolguy);
coolGuy.group.scale.setScalar(0.92);
coolGuy.at(-0.75, 0, -2.2);
coolGuy.set({ mood: 'deadpan' });
D.scene.add(coolGuy.group);

const scammer = new Toon(CAST.scammer);
scammer.group.scale.setScalar(0.92);
scammer.at(0.65, 0, -2.3);
scammer.set({ mood: 'smug', armR: [35, -80], holdR: PROPS.paidHammer });
D.scene.add(scammer.group);

shot(sx(1), b.y, sw, () => {
  cam.fov = 38; cam.updateProjectionMatrix();
  cam.position.set(-0.1, 1.45, 1.8);
  cam.lookAt(-0.05, 1.05, -2.8);
  coolGuy.face(cam); scammer.face(cam);
  E.render(D.scene, cam, { focus: 4.0, aperture: 0.001, bloom: 0.25 });
});

// World (C): Inside Cockpit / Dashcam View (Screenshot 4)
const C = WD.carCockpit(E, { rain: true });
const driverInside = new Toon(CAST.driver);
driverInside.group.scale.setScalar(0.70);
driverInside.at(-0.16, 0.46, -0.10);
driverInside.set({ mood: 'deadpan', legs: 'steer', look: [0.7, 0] });
C.scene.add(driverInside.group);

const scammerOutside = new Toon(CAST.coolguy);
scammerOutside.group.scale.setScalar(0.85);
scammerOutside.at(0.08, 0.58, -1.8);
scammerOutside.set({ mood: 'smug', look: [-0.4, 0] });
C.scene.add(scammerOutside.group);

shot(sx(2), b.y, sw, () => {
  C.update(1.2);
  cam.fov = 58; cam.updateProjectionMatrix();
  cam.position.set(0.48, 1.30, 0.95);
  cam.lookAt(-0.08, 1.15, -0.65);
  driverInside.face(cam); scammerOutside.face(cam);
  E.render(C.scene, cam, { focus: 1.2, aperture: 0.0012, bloom: 0.45 });
});

['(A) HIGHWAY AT DUSK', '(B) SUBURBAN DRIVEWAY', '(C) COCKPIT DASHCAM'].forEach((t, i) =>
  small(t, sx(i) + sw / 2, b.y + sw * 16 / 9 + 24, 'center', 14)
);

// ═════════════════════════ 5 · CAPTIONS ═════════════════════════
b = panel(790, 610, 520, 456, 5, 'CAPTIONS');
wide({ x: b.x, y: b.y, w: b.w, h: b.h - 10 }, () => {
  const c3 = new THREE.PerspectiveCamera(34, 1280 / 860, 0.05, 800);
  c3.position.set(-0.6, 2.0, 1.2);
  c3.lookAt(0.2, 1.2, -5.5);
  E2.render(H2.scene, c3, { focus: 4.8, aperture: 0.002, bloom: 0.35 });
}, () => {
  const mid = b.x + b.w / 2;
  [['hits', 50], ['his car,', 130], ['beside you', 210], ['doesn\'t', 290]].forEach(([w, y]) => {
    B.save();
    B.translate(mid, b.y + y);
    B.scale(0.55, 0.55);
    captionText(w, 0, 0, 1.0);
    B.restore();
  });
  small('1-2 WORDS AT A TIME · WHITE · THICK BLACK INK OUTLINE · CENTERED', mid, b.y + b.h - 32, 'center', 11, '#FFFFFF');
});

// ═════════════════════════ 6 · RULES ═════════════════════════
b = panel(1320, 610, 580, 456, 6, 'RULES');
rules(b, [
  'FLAT 2D PEOPLE, 3D CARS: PEOPLE ARE CUT-OUTS; CARS ARE REAL 3D.',
  'VIRAL DRIVING STORIES: ROAD SCAMS, CRASHES & DASHCAM PROOF.',
  'COCKPIT POV: STEERING WHEEL, RAIN WIPERS & BLINKING RED LED.',
  'FACES TELL THE DRAMA: PANIC SCREAM, SMUG SMIRK, DEADPAN DRIVER.',
  '1-2 WORD CAPTIONS: WHITE INTER BLACK WITH DEEP STROKE.',
  'DYNAMIC VEHICLE CAMERAS: CRASH ZOOMS, CHASE PUSH-INS & PANS.',
  'THE TWIST: DASHCAM FOOTAGE REVEALS THE SCAM AND SAVES THE HERO.'
], b.y + 24, 11, 52);

window.SHEET_READY = true;
