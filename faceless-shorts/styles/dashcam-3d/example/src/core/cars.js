// 3D Procedural Cars for Dashcam 3D:
// Real Three.js vehicles with metallic paint, alloy wheels, glowing LED headlights & taillights,
// tinted glass, and suspension that match the viral Rick's Clips driving shorts.
import * as THREE from 'three';

const M = {
  redPaint: new THREE.MeshPhysicalMaterial({ color: '#E52421', roughness: 0.22, metalness: 0.35, clearcoat: 1.0, clearcoatRoughness: 0.1 }),
  cyanPaint: new THREE.MeshPhysicalMaterial({ color: '#10B8A2', roughness: 0.25, metalness: 0.25, clearcoat: 0.9, clearcoatRoughness: 0.15 }),
  blackPaint: new THREE.MeshPhysicalMaterial({ color: '#1A1C22', roughness: 0.3, metalness: 0.3, clearcoat: 0.8, clearcoatRoughness: 0.2 }),
  whitePaint: new THREE.MeshPhysicalMaterial({ color: '#F2F4F8', roughness: 0.25, metalness: 0.15, clearcoat: 0.85, clearcoatRoughness: 0.15 }),
  darkTrim: new THREE.MeshStandardMaterial({ color: '#1B1C20', roughness: 0.7, metalness: 0.1 }),
  glass: new THREE.MeshPhysicalMaterial({ color: '#0F1824', roughness: 0.1, transmission: 0.82, thickness: 0.3, transparent: true, opacity: 0.92 }),
  tire: new THREE.MeshStandardMaterial({ color: '#18191C', roughness: 0.85 }),
  rimAlloy: new THREE.MeshStandardMaterial({ color: '#D2D6DE', metalness: 0.8, roughness: 0.25 }),
  rimBlue: new THREE.MeshStandardMaterial({ color: '#1E63C9', metalness: 0.7, roughness: 0.3 }),
  ledHeadlight: new THREE.MeshBasicMaterial({ color: new THREE.Color('#EFFFFF').multiplyScalar(2.0) }),
  ledTaillight: new THREE.MeshBasicMaterial({ color: new THREE.Color('#FF1E24').multiplyScalar(2.2) }),
  ledLightBar: new THREE.MeshBasicMaterial({ color: new THREE.Color('#FFFFFF').multiplyScalar(3.0) }),
};

function makeWheel({ rimColor = M.rimBlue, radius = 0.34, width = 0.24 } = {}) {
  const g = new THREE.Group();
  // Tire
  const tireGeo = new THREE.CylinderGeometry(radius, radius, width, 24);
  tireGeo.rotateZ(Math.PI / 2);
  const tire = new THREE.Mesh(tireGeo, M.tire);
  tire.castShadow = true; tire.receiveShadow = true;
  g.add(tire);

  // Rim
  const rimGeo = new THREE.CylinderGeometry(radius * 0.72, radius * 0.72, width + 0.01, 16);
  rimGeo.rotateZ(Math.PI / 2);
  const rim = new THREE.Mesh(rimGeo, rimColor);
  g.add(rim);

  // Hub cap
  const hubGeo = new THREE.CylinderGeometry(radius * 0.3, radius * 0.3, width + 0.02, 12);
  hubGeo.rotateZ(Math.PI / 2);
  g.add(new THREE.Mesh(hubGeo, M.rimAlloy));

  return g;
}

// ── Red Sports Sedan (Screenshots 1, 2, 3) ──
export function makeRedSportsCar() {
  const car = new THREE.Group();

  // Lower chassis
  const bodyGeo = new THREE.BoxGeometry(1.85, 0.58, 4.3);
  const body = new THREE.Mesh(bodyGeo, M.redPaint);
  body.position.set(0, 0.52, 0);
  body.castShadow = true; body.receiveShadow = true;
  car.add(body);

  // Cabin / Greenhouse
  const cabinGeo = new THREE.BoxGeometry(1.55, 0.56, 2.3);
  const cabin = new THREE.Mesh(cabinGeo, M.redPaint);
  cabin.position.set(0, 0.98, -0.2);
  cabin.castShadow = true; cabin.receiveShadow = true;
  car.add(cabin);

  // Sloped windshield & rear glass
  const glassGeo = new THREE.BoxGeometry(1.52, 0.48, 2.22);
  const glass = new THREE.Mesh(glassGeo, M.glass);
  glass.position.set(0, 1.0, -0.2);
  car.add(glass);

  // Aerodynamic rear spoiler
  const spoiler = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.06, 0.28), M.redPaint);
  spoiler.position.set(0, 0.88, 1.95);
  spoiler.castShadow = true;
  car.add(spoiler);
  for (const s of [-0.65, 0.65]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.16, 0.1), M.darkTrim);
    post.position.set(s, 0.8, 1.95);
    car.add(post);
  }

  // Headlights
  for (const s of [-0.7, 0.7]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.12, 0.08), M.ledHeadlight);
    hl.position.set(s, 0.55, -2.14);
    car.add(hl);
  }

  // Taillights
  for (const s of [-0.68, 0.68]) {
    const tl = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.12, 0.08), M.ledTaillight);
    tl.position.set(s, 0.64, 2.14);
    car.add(tl);
  }

  // Dark grille
  const grille = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.18, 0.06), M.darkTrim);
  grille.position.set(0, 0.42, -2.14);
  car.add(grille);

  // Wheels
  const wheels = [];
  const addWheel = (x, y, z) => {
    const w = makeWheel({ rimColor: M.rimBlue, radius: 0.33, width: 0.22 });
    w.position.set(x, y, z);
    car.add(w);
    wheels.push(w);
  };
  addWheel(-0.95, 0.33, -1.35); // Front left
  addWheel(0.95, 0.33, -1.35);  // Front right
  addWheel(-0.95, 0.33, 1.35);  // Rear left
  addWheel(0.95, 0.33, 1.35);   // Rear right

  return {
    group: car,
    wheels,
    drive(dist) {
      wheels.forEach((w) => (w.rotation.x += dist * 3.0));
    }
  };
}

// ── Cyan Modern Crossover SUV (Screenshot 3) ──
export function makeCyanSUV() {
  const car = new THREE.Group();

  // Chunky SUV Body
  const bodyGeo = new THREE.BoxGeometry(1.95, 0.72, 4.4);
  const body = new THREE.Mesh(bodyGeo, M.cyanPaint);
  body.position.set(0, 0.68, 0);
  body.castShadow = true; body.receiveShadow = true;
  car.add(body);

  // Tall boxy cabin
  const cabinGeo = new THREE.BoxGeometry(1.68, 0.68, 2.6);
  const cabin = new THREE.Mesh(cabinGeo, M.cyanPaint);
  cabin.position.set(0, 1.25, -0.15);
  cabin.castShadow = true; cabin.receiveShadow = true;
  car.add(cabin);

  // Tinted glass
  const glass = new THREE.Mesh(new THREE.BoxGeometry(1.64, 0.6, 2.52), M.glass);
  glass.position.set(0, 1.25, -0.15);
  car.add(glass);

  // Roof rails
  for (const s of [-0.78, 0.78]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 2.3), M.darkTrim);
    rail.position.set(s, 1.62, -0.15);
    car.add(rail);
  }

  // Geometric glowing LED headlights (like Volvo / Modern SUV)
  for (const s of [-0.75, 0.75]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.16, 0.08), M.ledHeadlight);
    hl.position.set(s, 0.76, -2.19);
    car.add(hl);
  }

  // Rear taillights
  for (const s of [-0.76, 0.76]) {
    const tl = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.44, 0.08), M.ledTaillight);
    tl.position.set(s, 1.0, 2.19);
    car.add(tl);
  }

  // Wheels
  const wheels = [];
  const addWheel = (x, y, z) => {
    const w = makeWheel({ rimColor: M.rimAlloy, radius: 0.38, width: 0.26 });
    w.position.set(x, y, z);
    car.add(w);
    wheels.push(w);
  };
  addWheel(-1.02, 0.38, -1.4);
  addWheel(1.02, 0.38, -1.4);
  addWheel(-1.02, 0.38, 1.4);
  addWheel(1.02, 0.38, 1.4);

  return {
    group: car,
    wheels,
    drive(dist) {
      wheels.forEach((w) => (w.rotation.x += dist * 2.7));
    }
  };
}

// ── Black Heavy Pickup Truck with Roof Light Bar (Screenshot 3) ──
export function makeBlackPickup() {
  const truck = new THREE.Group();

  // Heavy cab body
  const cabGeo = new THREE.BoxGeometry(2.05, 0.85, 2.4);
  const cab = new THREE.Mesh(cabGeo, M.blackPaint);
  cab.position.set(0, 0.82, -0.8);
  cab.castShadow = true; cab.receiveShadow = true;
  truck.add(cab);

  // Upper cab roof
  const roof = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.65, 1.8), M.blackPaint);
  roof.position.set(0, 1.44, -0.8);
  roof.castShadow = true;
  truck.add(roof);

  // Glass
  const glass = new THREE.Mesh(new THREE.BoxGeometry(1.76, 0.58, 1.74), M.glass);
  glass.position.set(0, 1.44, -0.8);
  truck.add(glass);

  // Open Bed in the rear
  const bedFloor = new THREE.Mesh(new THREE.BoxGeometry(1.98, 0.45, 2.4), M.blackPaint);
  bedFloor.position.set(0, 0.64, 1.4);
  bedFloor.castShadow = true; bedFloor.receiveShadow = true;
  truck.add(bedFloor);

  // Roof LED Off-Road Light Bar (Glowing bright white!)
  const barMount = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.08, 0.1), M.darkTrim);
  barMount.position.set(0, 1.84, -1.2);
  truck.add(barMount);

  const lightBar = new THREE.Mesh(new THREE.BoxGeometry(1.42, 0.07, 0.08), M.ledLightBar);
  lightBar.position.set(0, 1.84, -1.24);
  truck.add(lightBar);

  // Headlights
  for (const s of [-0.8, 0.8]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.28, 0.08), M.ledHeadlight);
    hl.position.set(s, 0.88, -2.0);
    truck.add(hl);
  }

  // Heavy-duty offroad wheels
  const wheels = [];
  const addWheel = (x, y, z) => {
    const w = makeWheel({ rimColor: M.darkTrim, radius: 0.44, width: 0.32 });
    w.position.set(x, y, z);
    truck.add(w);
    wheels.push(w);
  };
  addWheel(-1.1, 0.44, -1.35);
  addWheel(1.1, 0.44, -1.35);
  addWheel(-1.1, 0.44, 1.55);
  addWheel(1.1, 0.44, 1.55);

  return {
    group: truck,
    wheels,
    drive(dist) {
      wheels.forEach((w) => (w.rotation.x += dist * 2.3));
    }
  };
}

// ── White SUV (Screenshot 1) ──
export function makeWhiteSUV() {
  const car = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.75, 4.5), M.whitePaint);
  body.position.set(0, 0.72, 0);
  body.castShadow = true; body.receiveShadow = true;
  car.add(body);

  const cabin = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.7, 2.7), M.whitePaint);
  cabin.position.set(0, 1.32, -0.15);
  cabin.castShadow = true;
  car.add(cabin);

  const glass = new THREE.Mesh(new THREE.BoxGeometry(1.68, 0.62, 2.62), M.glass);
  glass.position.set(0, 1.32, -0.15);
  car.add(glass);

  for (const s of [-0.76, 0.76]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.08), M.ledHeadlight);
    hl.position.set(s, 0.8, -2.24);
    car.add(hl);
  }

  const wheels = [];
  for (const [x, z] of [[-1.04, -1.4], [1.04, -1.4], [-1.04, 1.4], [1.04, 1.4]]) {
    const w = makeWheel({ rimColor: M.rimAlloy, radius: 0.4, width: 0.28 });
    w.position.set(x, 0.4, z);
    car.add(w);
    wheels.push(w);
  }

  return {
    group: car,
    wheels,
    drive(dist) {
      wheels.forEach((w) => (w.rotation.x += dist * 2.5));
    }
  };
}
