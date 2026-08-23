/**
 * Robot companion.
 *
 * A small Three.js robot in the bottom-right corner. It watches the cursor,
 * blinks, bobs while idle, and reacts when you click it. A toggle button turns
 * it off, and that choice is remembered in localStorage.
 *
 * Built from primitives — no model file to download, so it costs nothing beyond
 * the Three.js already loaded for the hero.
 *
 * Skipped entirely under prefers-reduced-motion, on small screens, and where
 * WebGL is unavailable.
 */

import * as THREE from "./vendor/three.module.min.js";

const STORAGE_KEY = "portfolio:robot";
const BRAND = 0x8289ff;
const PANEL = 0x1a1a1f;
const EYE = 0x9fe8ff;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const GREETINGS = [
  "Hi — I'm Suraj's build assistant.",
  "Everything here is Django, all the way down.",
  "The projects below are real repos. Have a look.",
  "Say hello through the contact form — it actually works.",
  "Built with Three.js. No model file, just primitives.",
];

/** localStorage can throw in private mode — never let that break the page. */
function readPreference() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (err) {
    return null;
  }
}

function writePreference(value) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch (err) {
    /* ignore — the robot just won't be remembered */
  }
}

function init() {
  const mount = document.getElementById("robot");
  const toggle = document.getElementById("robotToggle");
  if (!mount || !toggle) return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (window.innerWidth < 900) return;

  const probe = document.createElement("canvas");
  try {
    if (!(window.WebGLRenderingContext && (probe.getContext("webgl2") || probe.getContext("webgl")))) return;
  } catch (err) {
    return;
  }

  // The toggle only appears once we know the robot can actually run.
  toggle.hidden = false;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch (err) {
    return;
  }

  const SIZE = 168;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 60);
  camera.position.set(0, -0.15, 10.2);

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(SIZE, SIZE);
  renderer.setClearColor(0x000000, 0);
  mount.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 1.5));
  const keyLight = new THREE.DirectionalLight(BRAND, 2.2);
  keyLight.position.set(3, 4, 5);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0xffffff, 0.8);
  rimLight.position.set(-4, 1, -3);
  scene.add(rimLight);

  // --- Build the robot ------------------------------------------------------

  const robot = new THREE.Group();
  scene.add(robot);

  const shell = new THREE.MeshStandardMaterial({
    color: PANEL, roughness: 0.42, metalness: 0.65,
  });
  const trim = new THREE.MeshStandardMaterial({
    color: BRAND, roughness: 0.3, metalness: 0.5,
    emissive: BRAND, emissiveIntensity: 0.28,
  });
  const glow = new THREE.MeshBasicMaterial({ color: EYE });

  // Head
  const head = new THREE.Group();
  const skull = new THREE.Mesh(new THREE.BoxGeometry(2.5, 2, 1.9), shell);
  head.add(skull);

  // Visor
  const visor = new THREE.Mesh(new THREE.BoxGeometry(2.05, 0.95, 0.14), trim);
  visor.position.set(0, 0.15, 0.98);
  head.add(visor);

  // Eyes sit slightly proud of the visor so they read as lit.
  const eyes = [];
  [-0.46, 0.46].forEach((x) => {
    const eye = new THREE.Mesh(new THREE.CircleGeometry(0.2, 20), glow);
    eye.position.set(x, 0.15, 1.07);
    head.add(eye);
    eyes.push(eye);
  });

  // Antenna
  const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.75, 8), shell);
  stalk.position.set(0, 1.35, 0);
  head.add(stalk);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 16), trim);
  bulb.position.set(0, 1.78, 0);
  head.add(bulb);

  // Ears
  [-1.36, 1.36].forEach((x) => {
    const ear = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.6, 0.6), trim);
    ear.position.set(x, 0.1, 0);
    head.add(ear);
  });

  head.position.y = 0.75;
  robot.add(head);

  // Body
  const body = new THREE.Mesh(new THREE.BoxGeometry(2, 1.5, 1.4), shell);
  body.position.y = -1.05;
  robot.add(body);

  const chestLight = new THREE.Mesh(new THREE.CircleGeometry(0.26, 20), glow);
  chestLight.position.set(0, -1.0, 0.72);
  robot.add(chestLight);

  // Arms — the left one waves.
  const arms = [];
  [-1.28, 1.28].forEach((x, i) => {
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.16, 0.85, 4, 10), shell);
    arm.position.set(x, -1.0, 0);
    arm.rotation.z = i === 0 ? 0.2 : -0.2;
    robot.add(arm);
    arms.push(arm);
  });

  robot.scale.setScalar(0.84);

  // --- State ----------------------------------------------------------------

  const pointer = { x: 0, y: 0 };
  const eased = { x: 0, y: 0 };
  let waveUntil = 0;
  let nextBlink = 2 + Math.random() * 3;
  let blinkUntil = 0;
  let bubbleTimer = null;

  function onPointerMove(event) {
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = (event.clientY / window.innerHeight) * 2 - 1;
  }
  window.addEventListener("pointermove", onPointerMove, { passive: true });

  const bubble = document.getElementById("robotBubble");

  function say(text) {
    if (!bubble) return;
    bubble.textContent = text;
    bubble.classList.add("is-open");
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => bubble.classList.remove("is-open"), 4200);
  }

  let greetingIndex = 0;
  function greet() {
    waveUntil = clock.getElapsedTime() + 1.6;
    say(GREETINGS[greetingIndex % GREETINGS.length]);
    greetingIndex++;
  }

  mount.addEventListener("click", greet);
  mount.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      greet();
    }
  });

  // --- Render loop ----------------------------------------------------------

  const clock = new THREE.Clock();
  let frameId = null;
  let running = false;

  function frame() {
    frameId = requestAnimationFrame(frame);

    const t = clock.getElapsedTime();
    const delta = Math.min(clock.getDelta(), 0.05);

    eased.x += (pointer.x - eased.x) * 0.07;
    eased.y += (pointer.y - eased.y) * 0.07;

    // Look toward the cursor, within a comfortable range.
    // Clamped, so it never turns so far that it reads as looking away.
    head.rotation.y = clamp(eased.x * 0.5, -0.42, 0.42);
    head.rotation.x = clamp(eased.y * 0.3, -0.26, 0.3);
    robot.rotation.y = clamp(eased.x * 0.18, -0.2, 0.2);

    // Idle bob and sway.
    robot.position.y = Math.sin(t * 1.5) * 0.09;
    robot.rotation.z = Math.sin(t * 0.9) * 0.035;

    // Blink.
    if (t > nextBlink) {
      blinkUntil = t + 0.13;
      nextBlink = t + 2.4 + Math.random() * 3.6;
    }
    const blinking = t < blinkUntil;
    eyes.forEach((eye) => eye.scale.set(1, blinking ? 0.12 : 1, 1));

    // Antenna bulb pulses; brighter mid-wave.
    const waving = t < waveUntil;
    bulb.material.emissiveIntensity = 0.28 + Math.sin(t * 3) * 0.12 + (waving ? 0.5 : 0);

    // Wave with the left arm.
    arms[0].rotation.z = waving ? 0.2 + Math.sin(t * 14) * 0.85 : 0.2;

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

  // --- Toggle ---------------------------------------------------------------

  function setVisible(visible, remember) {
    mount.classList.toggle("is-hidden", !visible);
    toggle.setAttribute("aria-pressed", String(visible));
    toggle.setAttribute("aria-label", visible ? "Hide the robot" : "Show the robot");
    toggle.classList.toggle("is-off", !visible);
    visible ? start() : stop();
    if (remember) writePreference(visible ? "on" : "off");
  }

  toggle.addEventListener("click", () => {
    const nowVisible = mount.classList.contains("is-hidden");
    setVisible(nowVisible, true);
    if (nowVisible) greet();
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else if (!mount.classList.contains("is-hidden")) start();
  });

  setVisible(readPreference() !== "off", false);

  window.addEventListener("pagehide", () => {
    stop();
    window.removeEventListener("pointermove", onPointerMove);
    clearTimeout(bubbleTimer);
    scene.traverse((obj) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    });
    renderer.dispose();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
