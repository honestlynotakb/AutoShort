// 3D Worlds for Dashcam 3D:
// 1. highway(E, { dusk }) - Multi-lane highway with traffic & guardrails
// 2. suburbanDriveway(E) - American suburban house, driveway & green lawn
// 3. cockpitStage(E, { rain }) - First-person driver view with dashcam, windshield & steering wheel
import * as THREE from 'three';
import { lightRig } from './engine.js';

function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// ── 1. Multi-Lane Highway ──
export function highway(E, { dusk = false } = {}) {
  const scene = new THREE.Scene();
  scene.environment = E.envMap; scene.environmentIntensity = 0.35;

  // Sky gradient
  scene.background = canvasTex(256, 512, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h);
    if (dusk) {
      gr.addColorStop(0, '#152E58');
      gr.addColorStop(0.55, '#854256');
      gr.addColorStop(0.85, '#FF8A42');
      gr.addColorStop(1, '#FFB852');
    } else {
      gr.addColorStop(0, '#1B74C9');
      gr.addColorStop(0.65, '#72B8EC');
      gr.addColorStop(1, '#B9E2FC');
    }
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  });

  // Road Asphalt
  const roadTex = canvasTex(1024, 1024, (g, w, h) => {
    g.fillStyle = '#26282E'; g.fillRect(0, 0, w, h);
    // Subtle asphalt noise
    for (let i = 0; i < 400; i++) {
      g.fillStyle = Math.random() > 0.5 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.06)';
      g.fillRect(Math.random() * w, Math.random() * h, 3, 3);
    }
    // Solid yellow left shoulder line
    g.fillStyle = '#FFC83B'; g.fillRect(80, 0, 18, h);
    // Dashed white lane markings
    g.fillStyle = '#FFFFFF';
    for (let y = 0; y < h; y += 128) {
      g.fillRect(360, y + 20, 16, 76);
      g.fillRect(660, y + 20, 16, 76);
    }
    // Solid white right shoulder line
    g.fillStyle = '#FFFFFF'; g.fillRect(940, 0, 18, h);
  });
  roadTex.wrapS = roadTex.wrapT = THREE.RepeatWrapping;
  roadTex.repeat.set(1, 12);

  const roadMat = new THREE.MeshStandardMaterial({ map: roadTex, roughness: 0.85 });
  const road = new THREE.Mesh(new THREE.PlaneGeometry(16, 120), roadMat);
  road.rotation.x = -Math.PI / 2;
  road.receiveShadow = true;
  scene.add(road);

  // Roadside Grass Banks
  const grassMat = new THREE.MeshStandardMaterial({ color: dusk ? '#426829' : '#3E8C28', roughness: 0.9 });
  for (const s of [-1, 1]) {
    const grass = new THREE.Mesh(new THREE.PlaneGeometry(18, 120), grassMat);
    grass.rotation.x = -Math.PI / 2;
    grass.position.set(s * 17, -0.02, 0);
    grass.receiveShadow = true;
    scene.add(grass);
  }

  // Corrugated Metal Guardrails
  const railMat = new THREE.MeshStandardMaterial({ color: '#A6AEB8', metalness: 0.7, roughness: 0.35 });
  for (const s of [-1, 1]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.44, 120), railMat);
    rail.position.set(s * 7.8, 0.52, 0);
    rail.castShadow = true; rail.receiveShadow = true;
    scene.add(rail);

    // Support posts every 4 meters
    for (let z = -56; z <= 56; z += 4) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.65, 0.14), railMat);
      post.position.set(s * 7.8, 0.28, z);
      scene.add(post);
    }
  }

  // Roadside trees and utility poles
  const poleMat = new THREE.MeshStandardMaterial({ color: '#5A4634', roughness: 0.9 });
  const treeMat = new THREE.MeshStandardMaterial({ color: dusk ? '#294820' : '#2D6B22', roughness: 0.85 });
  for (let z = -50; z <= 50; z += 18) {
    // Utility pole
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 9, 8), poleMat);
    pole.position.set(9.8, 4.5, z);
    pole.castShadow = true;
    scene.add(pole);

    // Crossbar
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.12, 2.2), poleMat);
    bar.position.set(9.8, 8.4, z);
    scene.add(bar);

    // Roadside tree
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.3, 3, 8), poleMat);
    trunk.position.set(-11, 1.5, z + 6);
    trunk.castShadow = true;
    scene.add(trunk);

    const foliage = new THREE.Mesh(new THREE.SphereGeometry(1.8, 12, 10), treeMat);
    foliage.scale.set(1.2, 1.6, 1.2);
    foliage.position.set(-11, 4.2, z + 6);
    foliage.castShadow = true;
    scene.add(foliage);
  }

  // Lighting
  const lights = dusk
    ? lightRig(scene, {
        key: '#FF8838', keyI: 4.8, keyPos: [-12, 4.5, -20],
        rimCol: '#6FA4E8', rimI: 1.4, sky: '#C97452', ground: '#2E1E16',
        hemiI: 0.8, shadowBox: 12, target: [0, 0.8, 0]
      })
    : lightRig(scene, {
        key: '#FFF3DC', keyI: 4.2, keyPos: [8, 14, 10],
        rimCol: '#CFE6FF', rimI: 1.2, sky: '#D6EDFF', ground: '#465E36',
        hemiI: 0.9, shadowBox: 12, target: [0, 0.8, 0]
      });

  return { scene, lights, update() {} };
}

// ── 2. Suburban Driveway & House (Screenshot 2) ──
export function suburbanDriveway(E) {
  const scene = new THREE.Scene();
  scene.environment = E.envMap; scene.environmentIntensity = 0.4;

  scene.background = canvasTex(256, 512, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, '#1E82D6');
    gr.addColorStop(0.7, '#88C4F4');
    gr.addColorStop(1, '#CDE8FC');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  });

  // Grass Lawn
  const grassTex = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#449E28'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 300; i++) {
      g.fillStyle = Math.random() > 0.5 ? '#55B834' : '#398420';
      g.fillRect(Math.random() * w, Math.random() * h, 4, 8);
    }
  });
  grassTex.wrapS = grassTex.wrapT = THREE.RepeatWrapping;
  grassTex.repeat.set(8, 8);
  const lawn = new THREE.Mesh(new THREE.PlaneGeometry(36, 36), new THREE.MeshStandardMaterial({ map: grassTex, roughness: 0.85 }));
  lawn.rotation.x = -Math.PI / 2;
  lawn.receiveShadow = true;
  scene.add(lawn);

  // Concrete Driveway
  const driveTex = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#D6D8DE'; g.fillRect(0, 0, w, h);
    g.strokeStyle = '#9AA0AC'; g.lineWidth = 4;
    g.strokeRect(0, 0, w, h);
  });
  driveTex.wrapS = driveTex.wrapT = THREE.RepeatWrapping;
  driveTex.repeat.set(2, 4);
  const driveway = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 18), new THREE.MeshStandardMaterial({ map: driveTex, roughness: 0.7 }));
  driveway.rotation.x = -Math.PI / 2;
  driveway.position.set(-0.6, 0.01, 1.0);
  driveway.receiveShadow = true;
  scene.add(driveway);

  // Suburban House Facade (White siding)
  const sidingTex = canvasTex(256, 512, (g, w, h) => {
    g.fillStyle = '#F4F5F7'; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(0,0,0,0.08)';
    for (let y = 0; y < h; y += 16) g.fillRect(0, y, w, 2);
  });
  const houseMat = new THREE.MeshStandardMaterial({ map: sidingTex, roughness: 0.65 });
  const house = new THREE.Mesh(new THREE.BoxGeometry(14, 5.5, 8), houseMat);
  house.position.set(0, 2.75, -8.5);
  house.castShadow = true; house.receiveShadow = true;
  scene.add(house);

  // Pitched Roof
  const roof = new THREE.Mesh(new THREE.ConeGeometry(9.8, 3.2, 4), new THREE.MeshStandardMaterial({ color: '#4E535C', roughness: 0.6 }));
  roof.rotation.y = Math.PI / 4;
  roof.position.set(0, 6.8, -8.5);
  roof.scale.set(1.1, 1.0, 0.8);
  roof.castShadow = true;
  scene.add(roof);

  // Garage Door
  const garageDoor = new THREE.Mesh(new THREE.PlaneGeometry(5.2, 3.2), new THREE.MeshStandardMaterial({ color: '#FFFFFF', roughness: 0.5 }));
  garageDoor.position.set(-0.6, 1.6, -4.48);
  scene.add(garageDoor);

  // Lighting
  const lights = lightRig(scene, {
    key: '#FFF6E6', keyI: 4.4, keyPos: [8, 12, 10],
    rimCol: '#B5DCFF', rimI: 1.1, sky: '#C9E6FF', ground: '#4A6B38',
    hemiI: 0.95, shadowBox: 10, target: [0, 0.8, 0]
  });

  return { scene, lights, update() {} };
}

// ── 3. First-Person Car Cockpit (Screenshot 4) ──
export function carCockpit(E, { rain = true } = {}) {
  const scene = new THREE.Scene();
  scene.environment = E.envMap; scene.environmentIntensity = 0.3;

  // Rain sky background
  scene.background = canvasTex(256, 512, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, '#2D3A48');
    gr.addColorStop(0.65, '#566B7D');
    gr.addColorStop(1, '#8193A4');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  });

  // Outside road in rain
  const road = new THREE.Mesh(new THREE.PlaneGeometry(16, 60), new THREE.MeshStandardMaterial({ color: '#1B1D22', roughness: 0.3, metalness: 0.4 }));
  road.rotation.x = -Math.PI / 2;
  road.position.set(0, -0.6, -16);
  scene.add(road);

  // ── Cockpit Group (car interior) ──
  const cockpit = new THREE.Group();
  scene.add(cockpit);

  const dashMat = new THREE.MeshStandardMaterial({ color: '#262930', roughness: 0.85 });
  const plasticMat = new THREE.MeshStandardMaterial({ color: '#1A1C20', roughness: 0.7 });

  // Main Dashboard
  const dash = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.48, 0.9), dashMat);
  dash.position.set(0, 0.88, -0.7);
  cockpit.add(dash);

  // Instrument Cluster Hood (Speedometer binnacle)
  const binnacle = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.28, 0.45), dashMat);
  binnacle.position.set(-0.46, 1.16, -0.65);
  cockpit.add(binnacle);

  // Instrument Gauges with Glowing Orange Needles
  const gaugeTex = canvasTex(256, 128, (g, w, h) => {
    g.fillStyle = '#0D0E12'; g.fillRect(0, 0, w, h);
    // Two circular dials
    [-1, 1].forEach((s) => {
      const cx = w / 2 + s * 60, cy = h / 2;
      g.strokeStyle = '#444855'; g.lineWidth = 4;
      g.beginPath(); g.arc(cx, cy, 38, Math.PI * 0.7, Math.PI * 2.3); g.stroke();
      // Orange Needle
      g.strokeStyle = '#FF6B1A'; g.lineWidth = 3;
      g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + s * 22, cy - 20); g.stroke();
    });
  });
  const gauges = new THREE.Mesh(new THREE.PlaneGeometry(0.58, 0.2), new THREE.MeshBasicMaterial({ map: gaugeTex }));
  gauges.position.set(-0.46, 1.15, -0.42);
  cockpit.add(gauges);

  // Steering Column & Wheel
  const wheelGroup = new THREE.Group();
  wheelGroup.position.set(-0.46, 1.05, -0.32);
  wheelGroup.rotation.x = 0.35;
  cockpit.add(wheelGroup);

  const wheelRim = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.022, 12, 32), plasticMat);
  wheelGroup.add(wheelRim);

  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.04, 16), plasticMat);
  hub.rotation.x = Math.PI / 2;
  wheelGroup.add(hub);

  // Windshield Glass with Wipers
  const glassMat = new THREE.MeshPhysicalMaterial({ color: '#C8E4F8', roughness: 0.1, transmission: 0.9, thickness: 0.08, transparent: true, opacity: 0.85 });
  const windshield = new THREE.Mesh(new THREE.PlaneGeometry(2.3, 1.1), glassMat);
  windshield.rotation.x = -0.48;
  windshield.position.set(0, 1.48, -0.85);
  cockpit.add(windshield);

  // Windshield Wipers
  const wiperMat = new THREE.MeshStandardMaterial({ color: '#16171A' });
  const wiperL = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.55, 0.02), wiperMat);
  wiperL.rotation.set(-0.48, 0, -0.6);
  wiperL.position.set(-0.35, 1.34, -0.83);
  cockpit.add(wiperL);

  // Rearview Mirror
  const mirror = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.1, 0.04), plasticMat);
  mirror.position.set(0, 1.78, -0.72);
  cockpit.add(mirror);

  // ── DASHCAM mounted on windshield (Screenshot 4) ──
  const dashcam = new THREE.Group();
  dashcam.position.set(0.12, 1.68, -0.74);
  cockpit.add(dashcam);

  // Suction mount
  const mount = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.03, 12), plasticMat);
  dashcam.add(mount);

  // Camera body
  const camBody = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.1, 0.08), plasticMat);
  camBody.position.set(0, -0.06, 0.03);
  dashcam.add(camBody);

  // Camera lens facing forward
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.03, 0.04, 16), new THREE.MeshStandardMaterial({ color: '#111', metalness: 0.9 }));
  lens.rotation.x = Math.PI / 2;
  lens.position.set(0, -0.06, -0.02);
  dashcam.add(lens);

  // Bright Red Recording LED indicator!
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.009, 8, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color('#FF0022').multiplyScalar(4.0) }));
  led.position.set(0.05, -0.03, 0.07);
  dashcam.add(led);

  // Driver Seat
  const seatMat = new THREE.MeshStandardMaterial({ color: '#565A66', roughness: 0.9 });
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.85, 0.5), seatMat);
  seat.position.set(-0.46, 0.55, 0.2);
  cockpit.add(seat);

  // Rain particle streaks
  let rainGeo = null, rainMesh = null;
  if (rain) {
    const count = 400;
    rainGeo = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 1] = Math.random() * 6;
      pos[i * 3 + 2] = -Math.random() * 12;
    }
    rainGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const rainMat = new THREE.PointsMaterial({ color: '#D2E6FF', size: 0.04, transparent: true, opacity: 0.65 });
    rainMesh = new THREE.Points(rainGeo, rainMat);
    scene.add(rainMesh);
  }

  // Soft interior lighting + directional rain light
  const lights = lightRig(scene, {
    key: '#B8D4EA', keyI: 2.8, keyPos: [2, 6, -6],
    rimCol: '#86B5D8', rimI: 1.4, sky: '#668095', ground: '#1A242E',
    hemiI: 0.75, shadowBox: 5, target: [0, 1.2, -0.5]
  });

  return {
    scene, cockpit, lights,
    update(t) {
      if (rainMesh && rainGeo) {
        const p = rainGeo.attributes.position.array;
        for (let i = 1; i < p.length; i += 3) {
          p[i] -= 0.35;
          if (p[i] < 0) p[i] = 6;
        }
        rainGeo.attributes.position.needsUpdate = true;
      }
      // Wiper sweep
      wiperL.rotation.z = -0.6 + Math.sin(t * 5.0) * 0.45;
    }
  };
}
