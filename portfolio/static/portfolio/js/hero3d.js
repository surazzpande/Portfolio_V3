/**
 * Interactive 3D hero background.
 *
 * A rotating icosahedral core inside a particle field. Nearby particles draw
 * connecting lines into a shifting constellation, particles near the cursor are
 * pushed away, and scrolling pulls the camera back through the field.
 *
 * Three.js is served from this site (js/vendor/), not a CDN, so the page works
 * offline and depends on nobody else's uptime.
 *
 * Bails out quietly, leaving the CSS gradient in place, when the visitor prefers
 * reduced motion, the screen is under 760px, or WebGL is unavailable. Rendering
 * pauses when the hero scrolls out of view or the tab is hidden, so it never
 * burns battery in the background.
 */

import * as THREE from "./vendor/three.module.min.js";

const BRAND = new THREE.Color(0x8289ff);
const INK = new THREE.Color(0xf0f0f3);

const PARTICLE_COUNT = 900;      // field density
const FIELD_RADIUS = 24;         // how far the field spreads
const LINK_DISTANCE = 4.4;       // how close two particles must be to link
const MAX_LINKS = 900;           // hard cap, so the line buffer never grows
const REPEL_RADIUS = 6.5;        // cursor influence radius, in world units
const REPEL_STRENGTH = 9;

function init() {
  const mount = document.getElementById("hero3d");
  if (!mount) return;

  // --- Opt-outs -------------------------------------------------------------

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (window.innerWidth < 760) return;

  const probe = document.createElement("canvas");
  const supportsWebGL = (() => {
    try {
      return !!(
        window.WebGLRenderingContext &&
        (probe.getContext("webgl2") || probe.getContext("webgl"))
      );
    } catch (err) {
      return false;
    }
  })();
  if (!supportsWebGL) return;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  } catch (err) {
    return; // context creation can still fail on locked-down drivers
  }

  // --- Scene ----------------------------------------------------------------

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0a0a0b, 0.021);

  const camera = new THREE.PerspectiveCamera(
    55,
    mount.clientWidth / mount.clientHeight,
    0.1,
    140
  );
  camera.position.set(0, 0, 30);

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(mount.clientWidth, mount.clientHeight);
  renderer.setClearColor(0x000000, 0);
  mount.appendChild(renderer.domElement);

  // --- Particle field -------------------------------------------------------
  // `home` holds each particle's resting place; `position` is where it actually
  // is. Repulsion moves position away from home, and a spring pulls it back.

  const home = new Float32Array(PARTICLE_COUNT * 3);
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const velocities = new Float32Array(PARTICLE_COUNT * 3);
  const sizes = new Float32Array(PARTICLE_COUNT);

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    // Cube-root keeps the distribution even instead of clustering at the centre.
    const r = FIELD_RADIUS * Math.cbrt(Math.random());
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);

    home[i * 3] = positions[i * 3] = x;
    home[i * 3 + 1] = positions[i * 3 + 1] = y;
    home[i * 3 + 2] = positions[i * 3 + 2] = z;
    sizes[i] = 0.06 + Math.random() * 0.12;
  }

  const particleGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  const particles = new THREE.Points(
    particleGeometry,
    new THREE.PointsMaterial({
      color: INK,
      size: 0.13,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.7,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  scene.add(particles);

  // --- Constellation lines --------------------------------------------------
  // One pre-allocated buffer, redrawn each frame with a per-vertex alpha that
  // fades a link out as the two particles drift apart.

  const linkPositions = new Float32Array(MAX_LINKS * 6);
  const linkColors = new Float32Array(MAX_LINKS * 6);

  const linkGeometry = new THREE.BufferGeometry();
  linkGeometry.setAttribute("position", new THREE.BufferAttribute(linkPositions, 3));
  linkGeometry.setAttribute("color", new THREE.BufferAttribute(linkColors, 3));

  const links = new THREE.LineSegments(
    linkGeometry,
    new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  scene.add(links);

  // Spatial hash so linking is near-linear rather than 900² comparisons.
  const CELL = LINK_DISTANCE;
  const buckets = new Map();
  const cellKey = (x, y, z) =>
    `${Math.floor(x / CELL)},${Math.floor(y / CELL)},${Math.floor(z / CELL)}`;

  function rebuildLinks() {
    buckets.clear();

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const key = cellKey(positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]);
      let bucket = buckets.get(key);
      if (!bucket) buckets.set(key, (bucket = []));
      bucket.push(i);
    }

    let n = 0;

    outer: for (const [key, bucket] of buckets) {
      const [cx, cy, cz] = key.split(",").map(Number);

      for (let dx = 0; dx <= 1; dx++) {
        for (let dy = dx === 0 ? 0 : -1; dy <= 1; dy++) {
          for (let dz = dx === 0 && dy === 0 ? 0 : -1; dz <= 1; dz++) {
            const neighbours = buckets.get(`${cx + dx},${cy + dy},${cz + dz}`);
            if (!neighbours) continue;
            const sameCell = dx === 0 && dy === 0 && dz === 0;

            for (let a = 0; a < bucket.length; a++) {
              for (let b = sameCell ? a + 1 : 0; b < neighbours.length; b++) {
                const i = bucket[a];
                const j = neighbours[b];
                if (i === j) continue;

                const ax = positions[i * 3], ay = positions[i * 3 + 1], az = positions[i * 3 + 2];
                const bx = positions[j * 3], by = positions[j * 3 + 1], bz = positions[j * 3 + 2];
                const dist = Math.hypot(ax - bx, ay - by, az - bz);
                if (dist > LINK_DISTANCE) continue;

                const fade = 1 - dist / LINK_DISTANCE;
                const o = n * 6;

                linkPositions[o] = ax; linkPositions[o + 1] = ay; linkPositions[o + 2] = az;
                linkPositions[o + 3] = bx; linkPositions[o + 4] = by; linkPositions[o + 5] = bz;

                const r = BRAND.r * fade, g = BRAND.g * fade, bl = BRAND.b * fade;
                linkColors[o] = r; linkColors[o + 1] = g; linkColors[o + 2] = bl;
                linkColors[o + 3] = r; linkColors[o + 4] = g; linkColors[o + 5] = bl;

                if (++n >= MAX_LINKS) break outer;
              }
            }
          }
        }
      }
    }

    linkGeometry.setDrawRange(0, n * 2);
    linkGeometry.attributes.position.needsUpdate = true;
    linkGeometry.attributes.color.needsUpdate = true;
  }

  // --- Wireframe core -------------------------------------------------------

  const core = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(7.4, 1)),
    new THREE.LineBasicMaterial({ color: BRAND, transparent: true, opacity: 0.6 })
  );
  scene.add(core);

  const innerCore = new THREE.Mesh(
    new THREE.IcosahedronGeometry(4.4, 0),
    new THREE.MeshBasicMaterial({ color: BRAND, wireframe: true, transparent: true, opacity: 0.24 })
  );
  scene.add(innerCore);

  // --- Interaction ----------------------------------------------------------

  const pointer = new THREE.Vector2();   // normalised device coords
  const eased = { x: 0, y: 0 };
  const cursorWorld = new THREE.Vector3();
  const raycaster = new THREE.Raycaster();
  const cursorPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);

  let hasPointer = false;
  let scrollProgress = 0;

  function onPointerMove(event) {
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -((event.clientY / window.innerHeight) * 2 - 1);
    hasPointer = true;
  }
  window.addEventListener("pointermove", onPointerMove, { passive: true });

  function onScroll() {
    const height = mount.offsetHeight || 1;
    scrollProgress = Math.min(window.scrollY / height, 1);
  }
  window.addEventListener("scroll", onScroll, { passive: true });

  // --- Resize ---------------------------------------------------------------

  function onResize() {
    const { clientWidth: w, clientHeight: h } = mount;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  const resizeObserver = new ResizeObserver(onResize);
  resizeObserver.observe(mount);

  // --- Render loop ----------------------------------------------------------

  let frameId = null;
  let running = false;
  let tick = 0;
  const clock = new THREE.Clock();

  function frame() {
    frameId = requestAnimationFrame(frame);

    const elapsed = clock.getElapsedTime();
    const delta = Math.min(clock.getDelta(), 0.05); // clamp after a tab switch

    eased.x += (pointer.x - eased.x) * 0.05;
    eased.y += (pointer.y - eased.y) * 0.05;

    // Where the cursor sits in the scene, on the z=0 plane.
    if (hasPointer) {
      raycaster.setFromCamera(pointer, camera);
      raycaster.ray.intersectPlane(cursorPlane, cursorWorld);
    }

    // Particle physics: push away from the cursor, spring back home.
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const ix = i * 3, iy = ix + 1, iz = ix + 2;

      if (hasPointer) {
        const dx = positions[ix] - cursorWorld.x;
        const dy = positions[iy] - cursorWorld.y;
        const dz = positions[iz] - cursorWorld.z;
        const dist = Math.hypot(dx, dy, dz);

        if (dist < REPEL_RADIUS && dist > 0.001) {
          const push = ((REPEL_RADIUS - dist) / REPEL_RADIUS) * REPEL_STRENGTH * delta;
          velocities[ix] += (dx / dist) * push;
          velocities[iy] += (dy / dist) * push;
          velocities[iz] += (dz / dist) * push;
        }
      }

      // Spring toward the resting position, with damping.
      velocities[ix] += (home[ix] - positions[ix]) * 2.6 * delta;
      velocities[iy] += (home[iy] - positions[iy]) * 2.6 * delta;
      velocities[iz] += (home[iz] - positions[iz]) * 2.6 * delta;

      const damp = 1 - 3.2 * delta;
      velocities[ix] *= damp;
      velocities[iy] *= damp;
      velocities[iz] *= damp;

      positions[ix] += velocities[ix] * delta * 12;
      positions[iy] += velocities[iy] * delta * 12;
      positions[iz] += velocities[iz] * delta * 12;
    }
    particleGeometry.attributes.position.needsUpdate = true;

    // Linking is the expensive part — every third frame is plenty.
    if (tick++ % 3 === 0) rebuildLinks();

    core.rotation.y += delta * 0.13;
    core.rotation.x = Math.sin(elapsed * 0.22) * 0.16 + eased.y * -0.2;
    core.rotation.z = eased.x * 0.12;

    innerCore.rotation.y -= delta * 0.22;
    innerCore.rotation.x += delta * 0.1;

    const pulse = 1 + Math.sin(elapsed * 0.9) * 0.03;
    innerCore.scale.set(pulse, pulse, pulse);

    particles.rotation.y += delta * 0.015;
    links.rotation.y = particles.rotation.y;

    // Camera: leans toward the cursor, and pulls back as you scroll away.
    const targetX = eased.x * 3.4;
    const targetY = eased.y * 2.4;
    const targetZ = 30 + scrollProgress * 22;

    camera.position.x += (targetX - camera.position.x) * 0.045;
    camera.position.y += (targetY - camera.position.y) * 0.045;
    camera.position.z += (targetZ - camera.position.z) * 0.06;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  function start() {
    if (running) return;
    running = true;
    clock.start();
    frame();
  }

  function stop() {
    if (!running) return;
    running = false;
    cancelAnimationFrame(frameId);
    frameId = null;
  }

  const visibility = new IntersectionObserver(
    (entries) => entries.forEach((e) => (e.isIntersecting ? start() : stop())),
    { threshold: 0 }
  );
  visibility.observe(mount);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else if (mount.getBoundingClientRect().bottom > 0) start();
  });

  rebuildLinks();
  requestAnimationFrame(() => mount.classList.add("is-ready"));

  // --- Teardown -------------------------------------------------------------

  window.addEventListener("pagehide", () => {
    stop();
    visibility.disconnect();
    resizeObserver.disconnect();
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("scroll", onScroll);
    [particleGeometry, linkGeometry, core.geometry, innerCore.geometry].forEach((g) => g.dispose());
    [particles.material, links.material, core.material, innerCore.material].forEach((m) => m.dispose());
    renderer.dispose();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
