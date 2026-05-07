/**
 * HRCouriers — deeplink в Telegram (?start=), reveal при скролле, меню.
 */

(function () {
  "use strict";

  function getBotUsername() {
    var raw = window.HRCOURIERS_BOT_USERNAME || "HRCouriersbot";
    return String(raw).replace(/^@/, "").trim();
  }

  function telegramDeepLink(startPayload) {
    var user = getBotUsername();
    var payload = String(startPayload || "site").trim();
    return "https://t.me/" + encodeURIComponent(user) + "?start=" + encodeURIComponent(payload);
  }

  function bindTelegramDeepLinks() {
    document.querySelectorAll("[data-tg-start]").forEach(function (el) {
      var start = el.getAttribute("data-tg-start");
      if (!start) return;
      el.href = telegramDeepLink(start);
    });
  }

  function initScrollReveal() {
    var nodes = document.querySelectorAll(".reveal");
    if (!nodes.length) return;

    if (!window.IntersectionObserver) {
      nodes.forEach(function (el) {
        el.classList.add("reveal--visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("reveal--visible");
          observer.unobserve(entry.target);
        });
      },
      { root: null, rootMargin: "0px 0px -12% 0px", threshold: 0.08 }
    );

    nodes.forEach(function (el) {
      observer.observe(el);
    });
  }

  bindTelegramDeepLinks();
  initScrollReveal();

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();
