// Shot list for "Why Drivers Started Filming The Road"
// Dashcam 3D: 3D cars and highway/driveway/cockpit environments + 2D toon actors.
import * as THREE from 'three';
import { V3, lerp, lerpV, eo, eio, eob, clamp, seg } from './core/lib.js';
import { camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as CARS from './core/cars.js';
import { Toon, PROPS, CAST } from './core/toon.js';

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o);
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cam = camera(35);

  // Sets
  const H_day = WD.highway(E, { dusk: false });
  const H_dusk = WD.highway(E, { dusk: true });
  const D_drive = WD.suburbanDriveway(E);
  const C_rain = WD.carCockpit(E, { rain: true });

  // Vehicles
  const redCar = CARS.makeRedSportsCar();
  const cyanSUV = CARS.makeCyanSUV();
  const blackTruck = CARS.makeBlackPickup();
  const whiteSUV = CARS.makeWhiteSUV();

  // Characters
  const driver = new Toon(CAST.driver);
  const scammer = new Toon(CAST.scammer);
  const diver = new Toon(CAST.diver);
  const coolguy = new Toon(CAST.coolguy);
  const trucker = new Toon(CAST.trucker);
  const accomplice = new Toon(CAST.carrier);

  // ═════════════════════════ SHOT 01 : Hook (Cockpit POV) ═════════════════════════
  add({
    id: 'S01', at: 0, note: 'Cockpit POV: wide dashcam lens, rain on windshield, driver at wheel, scammer outside looking in',
    draw(lt, d, t, blit) {
      C_rain.update(t);
      C_rain.scene.add(driver.group, coolguy.group);

      cam.fov = 58; cam.updateProjectionMatrix();
      cam.position.set(0.48, 1.30, 0.95);
      cam.lookAt(-0.08, 1.15, -0.65);

      driver.group.scale.setScalar(0.70);
      driver.at(-0.16, 0.46, -0.10);
      driver.set({ mood: 'deadpan', legs: 'steer', look: [0.7, 0] });
      driver.face(cam);

      coolguy.group.scale.setScalar(0.85);
      coolguy.at(0.08, 0.88, -1.8);
      coolguy.set({ mood: 'smug', look: [-0.4, 0] });
      coolguy.face(cam);

      E.render(C_rain.scene, cam, { focus: 1.2, aperture: 0.0012, bloom: 0.4 });
      blit();
    }
  });
  cue(0.1, 'whoosh');

  // ═════════════════════════ SHOT 02 : Highway Traffic ═════════════════════════
  add({
    id: 'S02', at: 3.2, note: 'Highway traffic chase: cyan SUV and black pickup box in driver with headlights & lightbar',
    draw(lt, d, t, blit) {
      cam.fov = 36; cam.updateProjectionMatrix();
      H_dusk.scene.add(cyanSUV.group, blackTruck.group, redCar.group, trucker.group);

      redCar.group.position.set(-0.1, 0, -1.8);
      cyanSUV.group.position.set(-0.85, 0, -5.5);
      blackTruck.group.position.set(0.95, 0, -4.0);

      trucker.group.scale.setScalar(0.72);
      trucker.at(0.95, 1.25, -4.0);
      trucker.set({ mood: 'deadpan', look: [-0.3, 0] });
      trucker.face(cam);

      const k = eio(lt / d);
      cam.position.copy(lerpV(V3(-0.4, 3.6, -13.0), V3(-0.2, 3.2, -12.2), k));
      cam.lookAt(0.1, 1.2, -4.2);
      E.render(H_dusk.scene, cam, { focus: 4.8, aperture: 0.0008, bloom: 0.45 });
      blit();
    }
  });
  cue(3.2, 'engine_rev');

  // ═════════════════════════ SHOT 03 : The Swoop & Squat ═════════════════════════
  add({
    id: 'S03', at: 6.8, note: 'Truck cuts right beside while cyan SUV brake checks',
    draw(lt, d, t, blit) {
      H_day.scene.add(redCar.group, whiteSUV.group);
      redCar.group.position.set(1.4, 0, -2.8);
      whiteSUV.group.position.set(-1.8, 0, -7.5);

      cam.position.set(0.1, 1.5, 1.2);
      cam.lookAt(0.3, 1.0, -3.0);
      E.render(H_day.scene, cam, { focus: 4.2, aperture: 0.0012, bloom: 0.25 });
      blit();
    }
  });
  cue(6.8, 'tire_screech');

  // ═════════════════════════ SHOT 04 : The Pedestrian Dive ═════════════════════════
  add({
    id: 'S04', at: 10.4, note: 'Fake victim leaps backward screaming onto hood while accomplice watches with cashbox',
    draw(lt, d, t, blit) {
      H_day.scene.add(diver.group, accomplice.group, redCar.group, whiteSUV.group);
      redCar.group.position.set(1.5, 0, -2.8);
      whiteSUV.group.position.set(-1.2, 0, -8.0);
      whiteSUV.group.rotation.y = 0.08;

      diver.at(0.42, 0, -2.4);
      diver.set({ mood: 'scream', legs: 'dive', sweat: 1.0 });
      diver.face(cam);

      accomplice.at(-0.42, 0, -3.2);
      accomplice.set({ mood: 'sly', armL: [30, -50], armR: [30, -50], holdL: PROPS.cashbox });
      accomplice.face(cam);

      cam.position.set(-0.2, 1.45, 1.8);
      cam.lookAt(0.1, 1.0, -2.8);
      E.render(H_day.scene, cam, { focus: 4.2, aperture: 0.0012, bloom: 0.25 });
      blit();
    }
  });
  cue(10.4, 'thud');
  cue(10.6, 'yell');

  // ═════════════════════════ SHOT 05 : Driveway Confrontation ═════════════════════════
  add({
    id: 'S05', at: 14.5, note: 'Suburban driveway: fraudster hits car with PAID hammer sign',
    draw(lt, d, t, blit) {
      cam.fov = 38; cam.updateProjectionMatrix();
      D_drive.scene.add(redCar.group, coolguy.group, scammer.group);

      redCar.group.position.set(-0.7, 0, -3.2);
      redCar.group.rotation.y = Math.PI / 2 + 0.12;

      coolguy.group.scale.setScalar(0.92);
      coolguy.at(-0.75, 0, -2.2);
      coolguy.set({ mood: 'deadpan' });
      coolguy.face(cam);

      scammer.group.scale.setScalar(0.92);
      scammer.at(0.65, 0, -2.3);
      scammer.set({ mood: 'smug', armR: [35, -80], holdR: PROPS.paidHammer });
      scammer.face(cam);

      cam.position.set(-0.1, 1.45, 1.8);
      cam.lookAt(-0.05, 1.05, -2.8);
      E.render(D_drive.scene, cam, { focus: 4.0, aperture: 0.001, bloom: 0.25 });
      blit();
    }
  });
  cue(14.5, 'whoosh');
  cue(15.2, 'gavel_hit');

  // ═════════════════════════ SHOT 06 : Dashcam Turnaround ═════════════════════════
  add({
    id: 'S06', at: 18.2, note: 'Driver points up to dashcam with glowing red recording LED',
    draw(lt, d, t, blit) {
      cam.fov = 58; cam.updateProjectionMatrix();
      C_rain.update(t);
      C_rain.scene.add(driver.group, coolguy.group);

      cam.position.set(0.48, 1.30, 0.95);
      cam.lookAt(-0.08, 1.15, -0.65);

      driver.group.scale.setScalar(0.70);
      driver.at(-0.16, 0.46, -0.10);
      driver.set({ mood: 'smug', legs: 'steer', armR: [45, -70], look: [0.3, 0.5] });
      driver.face(cam);

      coolguy.group.scale.setScalar(0.85);
      coolguy.at(0.08, 0.58, -1.8);
      coolguy.set({ mood: 'shock', sweat: 1.0 });
      coolguy.face(cam);

      E.render(C_rain.scene, cam, { focus: 1.2, aperture: 0.0012, bloom: 0.45 });
      blit();
    }
  });
  cue(18.2, 'beep_record');
  cue(19.0, 'siren_distant');

  return { shots: S, cues: CUES };
}
