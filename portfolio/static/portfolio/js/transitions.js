/**
 * Page transitions.
 *
 * Intercepts clicks on internal links, plays a short wipe, then navigates.
 * On arrival the overlay wipes back out.
 *
 * Deliberately conservative: it only handles plain left-clicks on same-origin
 * links, and any modifier key, target, download attribute or hash link falls
 * through to normal browser behaviour. If anything goes wrong the navigation
 * still happens — a hard timeout guarantees it.
 *
 * Skipped entirely under prefers-reduced-motion.
 */

(function () {
  "use strict";

  var OUT_MS = 420;      // wipe-in before navigating
  var SAFETY_MS = 900;   // navigate regardless, if something stalls

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var overlay = document.getElementById("pageWipe");
  if (!overlay) return;

  var navigating = false;

  /* ---------- Arriving ---------- */

  function reveal() {
    overlay.classList.remove("is-covering");
    overlay.classList.add("is-revealing");
    setTimeout(function () {
      overlay.classList.remove("is-revealing");
    }, 620);
  }

  // Runs on first paint, and again when returning via the back button
  // (bfcache restores the page with the overlay still covering it).
  requestAnimationFrame(reveal);

  window.addEventListener("pageshow", function (event) {
    navigating = false;
    if (event.persisted) reveal();
  });

  /* ---------- Leaving ---------- */

  function shouldIntercept(link, event) {
    if (event.defaultPrevented) return false;
    if (event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;

    if (!link || !link.href) return false;
    if (link.target && link.target !== "_self") return false;
    if (link.hasAttribute("download")) return false;
    if (link.dataset.noTransition !== undefined) return false;

    var url;
    try {
      url = new URL(link.href, window.location.href);
    } catch (err) {
      return false;
    }

    if (url.origin !== window.location.origin) return false;
    if (!/^https?:$/.test(url.protocol)) return false;

    // Same page, different anchor — that's a scroll, not a navigation.
    if (url.pathname === window.location.pathname && url.hash) return false;
    if (url.href === window.location.href) return false;

    // Leave the admin alone; it has its own flows.
    if (url.pathname.indexOf("/admin/") === 0) return false;

    // Files are not pages — a wipe before a PDF download would be nonsense.
    if (url.pathname.indexOf("/media/") === 0) return false;
    if (url.pathname.indexOf("/static/") === 0) return false;
    if (/\.(pdf|zip|png|jpe?g|svg|docx?|csv|txt)$/i.test(url.pathname)) return false;

    return url.href;
  }

  document.addEventListener("click", function (event) {
    var link = event.target.closest ? event.target.closest("a") : null;
    if (!link) return;

    var destination = shouldIntercept(link, event);
    if (!destination) return;

    event.preventDefault();
    if (navigating) return;
    navigating = true;

    overlay.classList.add("is-covering");

    var went = false;
    function go() {
      if (went) return;
      went = true;
      window.location.href = destination;
    }

    setTimeout(go, OUT_MS);
    setTimeout(go, SAFETY_MS); // belt and braces — never strand the visitor
  });
})();
