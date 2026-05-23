/**
 * FastCourier — reveal при скролле и мобильное меню.
 */

(function () {
  "use strict";

  function initThemeToggle() {
    var toggleBtn = document.getElementById("theme-toggle");
    if (!toggleBtn) return;

    var storageKey = "fastcourier-theme";

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
    var switcher = document.getElementById("country-switcher");
    var trigger = document.getElementById("country-trigger");
    var valueNode = document.getElementById("country-value");
    var options = switcher ? switcher.querySelectorAll(".country-switcher__option") : [];
    var cards = document.querySelectorAll(".vacancy-card[data-country]");
    if (!switcher || !trigger || !valueNode || !options.length || !cards.length) return;

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

    function closeDropdown() {
      switcher.classList.remove("active");
      trigger.setAttribute("aria-expanded", "false");
    }

    function openDropdown() {
      switcher.classList.add("active");
      trigger.setAttribute("aria-expanded", "true");
    }

    function setActiveCountry(countryCode, title) {
      var selected = (countryCode || "RU").toUpperCase();
      valueNode.textContent = title;
      options.forEach(function (option) {
        var isActive = (option.getAttribute("data-country") || "").toUpperCase() === selected;
        option.classList.toggle("is-active", isActive);
        option.setAttribute("aria-selected", isActive ? "true" : "false");
      });
      applyFilter(selected);
    }

    var initialOption = switcher.querySelector(".country-switcher__option.is-active") || options[0];
    setActiveCountry(
      initialOption.getAttribute("data-country"),
      initialOption.textContent.trim()
    );

    trigger.addEventListener("click", function () {
      if (switcher.classList.contains("active")) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    options.forEach(function (option) {
      option.addEventListener("click", function () {
        setActiveCountry(option.getAttribute("data-country"), option.textContent.trim());
        closeDropdown();
      });
    });

    document.addEventListener("click", function (event) {
      if (!switcher.contains(event.target)) {
        closeDropdown();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeDropdown();
      }
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
