/* Portfolio front-end behaviour: reveal, nav state, project filter, contact form. */

(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Scroll reveal ---------- */

  var revealables = document.querySelectorAll(".reveal");

  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealables.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

    revealables.forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i % 6, 5) * 55 + "ms";
      revealObserver.observe(el);
    });
  }

  /* ---------- Active nav link ---------- */

  var sections = document.querySelectorAll("main section[id]");
  var navLinks = document.querySelectorAll(".nav-links a");

  if ("IntersectionObserver" in window && sections.length) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        navLinks.forEach(function (link) {
          link.classList.toggle("is-current", link.getAttribute("href") === "#" + id);
        });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });

    sections.forEach(function (s) { navObserver.observe(s); });
  }

  /* ---------- Mobile menu ---------- */

  var toggle = document.getElementById("navToggle");
  var menu = document.querySelector(".nav-links");

  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- Project filter ---------- */

  var filters = document.querySelectorAll(".filter");
  var projects = document.querySelectorAll(".project");
  var noResults = document.getElementById("noResults");

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var want = btn.dataset.filter;

      filters.forEach(function (f) { f.classList.toggle("is-active", f === btn); });

      var shown = 0;
      projects.forEach(function (card) {
        var tags = (card.dataset.tags || "").split(" ");
        var match = want === "all" || tags.indexOf(want) !== -1;
        card.classList.toggle("is-hidden", !match);
        if (match) shown++;
      });

      if (noResults) noResults.hidden = shown !== 0;
    });
  });

  /* ---------- Animated stat counters ---------- */

  var statValues = document.querySelectorAll(".stat-value");

  if (!reduceMotion && "IntersectionObserver" in window) {
    var statObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        statObserver.unobserve(el);

        var raw = el.dataset.count || el.textContent;
        var num = parseInt(raw, 10);
        if (isNaN(num)) return; // e.g. "Distinction" — leave it alone

        var suffix = raw.replace(/^[0-9]+/, "");
        var start = performance.now();
        var duration = 900;

        function step(now) {
          var progress = Math.min((now - start) / duration, 1);
          var eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(num * eased) + suffix;
          if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.5 });

    statValues.forEach(function (el) { statObserver.observe(el); });
  }

  /* ---------- Contact form ---------- */

  var form = document.getElementById("contactForm");

  if (form) {
    var statusEl = document.getElementById("formStatus");
    var submitBtn = document.getElementById("submitBtn");

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      form.querySelectorAll(".err").forEach(function (el) { el.textContent = ""; });
      statusEl.textContent = "";
      statusEl.className = "form-status";
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending…";

      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" }
      })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
          if (result.ok && result.data.ok) {
            form.reset();
            statusEl.textContent = result.data.message;
            statusEl.classList.add("is-ok");
          } else {
            var errors = result.data.errors || {};
            Object.keys(errors).forEach(function (field) {
              var target = form.querySelector('[data-err="' + field + '"]');
              if (target) target.textContent = errors[field][0];
            });
            statusEl.textContent = "Please fix the errors above.";
            statusEl.classList.add("is-err");
          }
        })
        .catch(function () {
          statusEl.textContent = "Something went wrong. Please email me directly.";
          statusEl.classList.add("is-err");
        })
        .finally(function () {
          submitBtn.disabled = false;
          submitBtn.textContent = "Send Message";
        });
    });
  }
})();

/* ---------- 3D tilt on cards ----------------------------------------------
   Cards lean toward the cursor in perspective. Pointer-based, so it is inert
   on touch devices, and skipped entirely under prefers-reduced-motion.        */

(function () {
  "use strict";

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  var MAX_TILT = 6;      // degrees
  var cards = document.querySelectorAll(".project, .post-card, .explore-card, .skill-card, .edu-card");

  cards.forEach(function (card) {
    var frame = null;

    function onMove(event) {
      if (frame) return;                      // one update per animation frame
      frame = requestAnimationFrame(function () {
        frame = null;
        var rect = card.getBoundingClientRect();
        var px = (event.clientX - rect.left) / rect.width - 0.5;
        var py = (event.clientY - rect.top) / rect.height - 0.5;

        card.style.transform =
          "perspective(900px) rotateY(" + (px * MAX_TILT).toFixed(2) + "deg) " +
          "rotateX(" + (-py * MAX_TILT).toFixed(2) + "deg) translateY(-3px)";
      });
    }

    function reset() {
      if (frame) { cancelAnimationFrame(frame); frame = null; }
      card.style.transform = "";
    }

    card.addEventListener("pointermove", onMove);
    card.addEventListener("pointerleave", reset);
    card.addEventListener("blur", reset, true);
  });
})();


/* ---------- Learning progress bars ----------------------------------------
   Bars fill from zero when they scroll into view.                            */

(function () {
  "use strict";

  var bars = document.querySelectorAll(".cert-bar");
  if (!bars.length) return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      !("IntersectionObserver" in window)) {
    return; // the inline width is already correct — just don't animate it
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var bar = entry.target;
      observer.unobserve(bar);
      var target = bar.style.width;
      bar.style.width = "0%";
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { bar.style.width = target; });
      });
    });
  }, { threshold: 0.4 });

  bars.forEach(function (bar) { observer.observe(bar); });
})();
