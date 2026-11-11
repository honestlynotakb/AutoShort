# Dashcam 3D: viral driving & scam stories, 9:16 (Rick's Clips style)

Expressive, viral, dramatic. Flat 2D cartoon people (bold ink outlines, round white heads, expressive acting, modern hair and hoodies) acting inside a realistic, modern 3D world: high-speed multi-lane highways, American suburban driveways, and first-person car cockpit views with windshield wipers, rain, and glowing dashcam recording indicators.

Example: `example/` = **WHY DRIVERS STARTED FILMING THE ROAD** (41 s, 6 shots). Style sheet: `style-sheet.png` (regenerate via `node tools/capture.mjs stylesheet ../style-sheet.png`).

## 1. The look (rules)
- **People are 2D, vehicles & worlds are 3D.** Every person is a camera-facing `Toon` cut-out with real cast shadows. Cars (red sports sedan, cyan crossover SUV, black heavy pickup with roof light bar, white SUV) are fully procedural 3D models with metallic clearcoats, tinted windows, and glowing LED headlights.
- **Three Core Worlds:**
  - (A) **The Highway**: Multi-lane tarmac highway with white dashes, yellow shoulders, metal guardrails, roadside grass, and traffic.
  - (B) **The Suburban Driveway**: Concrete driveway, manicured 3D green lawn, American house facade with garage and siding.
  - (C) **The Car Cockpit (POV)**: First-person driver view looking through windshield glass, complete with steering wheel, dashboard gauges, wipers, rain streaks, and a windshield-mounted dashcam with a bright blinking red recording LED.
- **Faces do the acting.** Dramatic, viral expressions on every beat:
  - `scream`: Wide open screaming mouth with teeth, tongue, distress eyes, and flying sweat droplets (the pedestrian dive).
  - `smug` / `sly`: Squinting sideways smirk (the scammer demanding money, holding the "PAID" wooden hammer).
  - `deadpan`: Unbothered driver holding the steering wheel, wearing seatbelt and airpod.
  - `shock`: Huge round eyes when the scammer realizes he was recorded.
- **Captions:** 1-2 words at a time, bold white Inter Black font with a thick black ink outline (`lineWidth: 15-18`) and soft drop shadow, centered horizontally at lower-middle screen (`y: 1340`). Words preserve punctuation ("hits", "his car,", "beside you", "doesn't").
- **Camera is always moving:** Fast push-ins on crash impact, orbital pans around traffic confrontations, and subtle cockpit camera shake.

## 2. Format
- 1080x1920, 24-30 fps, 30-50 s.
- Narration: conversational, engaging storyteller (`am_michael` x1.05).
- Sound design: heavy tire screech, car horn, dull crash thud, wooden gavel/hammer hit, dashcam recording beep, and distant police sirens.

## 3. Engine map (`example/src/`)
| file | gives you |
|---|---|
| `core/engine.js` | `makeEngine(canvas)` with NeutralToneMapping, soft shadows, bloom (for LED headlights, lightbars, dashcam LED), depth of field, subtle vignette & saturation grade |
| `core/toon.js` | `drawToon(g, look, st)` & `new Toon(look, { height })`: modern hairstyles (`parted`, `slick`, `wavy`, `cap_backward`), accessories (`aviator`, `glasses`, `airpod`, `seatbelt`, `belt`), props (`PROPS.paidHammer`, `PROPS.briefcase`, `PROPS.cashbox`, `PROPS.steeringWheel`), and cast presets (`CAST.driver`, `CAST.scammer`, `CAST.diver`, `CAST.coolguy`, `CAST.trucker`, `CAST.carrier`) |
| `core/cars.js` | 3D Three.js vehicle generators: `makeRedSportsCar()`, `makeCyanSUV()`, `makeBlackPickup()` (with roof-mounted LED light bar), `makeWhiteSUV()`. Each returns `{ group, wheels, drive(dist) }` |
| `core/world.js` | 3D environments: `highway(E, { dusk })` (asphalt, markings, guardrails, poles, trees), `suburbanDriveway(E)` (house facade, garage, concrete, lawn), `carCockpit(E, { rain })` (dashboard, gauges, steering wheel, glass, wipers, dashcam with red LED) |
| `core/captions.js` | 1-2 word captions: `captionText(text, x, y)`, `buildCaptions(script)`, `drawCaption(t)` |
| `core/board.js` | 1920x1080 style sheet board renderer (`startBoard`, `panel`, `frame`, `small`, `rules`) |
| `src/shots.js` | Video choreography file |
| `src/main.js` | Orchestrator driving headless Chrome capture |

## 4. A shot
```js
add({ id: 'S04', at: 10.4, note: 'Pedestrian dive onto hood', draw(lt, d, t, blit) {
  H_day.scene.add(diver.group, redCar.group);
  redCar.group.position.set(1.4, 0, -2.8);
  diver.at(0.2, 0, -2.6);
  diver.set({ mood: 'scream', legs: 'dive', sweat: 1.0 });
  diver.face(cam);
  cam.position.set(-0.1, 1.35, 1.0);
  cam.lookAt(0.3, 1.0, -2.8);
  E.render(H_day.scene, cam, { focus: 3.8, aperture: 0.0012, bloom: 0.25 });
  blit();
} });
```

## 5. QA pitfalls we've hit
- **Shader clamping / NaN in bloom:** Any custom shader with `pow()` or inverse trig must clamp inputs (`clamp(abs(dot(vN, vV)), 0.0, 1.0)`) to prevent `pow(<negative>) = NaN` from cascading into large black box bloom artifacts.
- **Camera clipping inside car meshes:** When filming inside the cockpit, keep the camera position between $z = 0.2$ and $z = 0.5$ at $y \approx 1.25$ to stay cleanly inside the cabin volume without clipping through the rear seat.
- **Toon cutouts from extreme side angles:** Toon cutouts turn thin when viewed at steep glancing angles. Always call `toon.face(cam)` every frame.
