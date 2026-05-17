/**
 * HRCouriers — reveal при скролле и мобильное меню.
 */

(function () {
  "use strict";

  function initThemeToggle() {
    var toggleBtn = document.getElementById("theme-toggle");
    if (!toggleBtn) return;

    var storageKey = "hrcouriers-theme";

    function syncToggleState() {
      var isLight = document.body.classList.contains("light-theme");
      toggleBtn.setAttribute("aria-pressed", isLight ? "true" : "false");
      toggleBtn.setAttribute(
        "aria-label",
        isLight ? "Включить темную тему" : "Включить светлую тему"
      );
      toggleBtn.setAttribute(
        "title",
        isLight ? "Включить темную тему" : "Включить светлую тему"
      );
    }

    syncToggleState();

    toggleBtn.addEventListener("click", function () {
      var isLight = document.body.classList.toggle("light-theme");
      try {
        localStorage.setItem(storageKey, isLight ? "light" : "dark");
      } catch (e) {
        // No-op if localStorage is unavailable.
      }
      syncToggleState();
    });
  }

  initThemeToggle();

  function initCountryFilter() {
    var selector = document.getElementById("country-select");
    var cards = document.querySelectorAll(".vacancy-card[data-country]");
    if (!selector || !cards.length) return;

    function applyFilter(countryCode) {
      var selected = (countryCode || "RU").toUpperCase();
      cards.forEach(function (card) {
        var cardCountry = (card.getAttribute("data-country") || "").toUpperCase();
        var isMatch = cardCountry === selected;
        card.style.display = isMatch ? "flex" : "none";
        if (isMatch) {
          card.classList.add("reveal--visible");
        }
      });
    }

    applyFilter(selector.value);

    selector.addEventListener("change", function () {
      applyFilter(selector.value);
    });
  }

  initCountryFilter();

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
