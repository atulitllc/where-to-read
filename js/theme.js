(function () {
  var key = "wtr-theme";
  var root = document.documentElement;
  function apply(theme) {
    root.setAttribute("data-theme", theme);
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    var dark = theme === "dark";
    btn.setAttribute("aria-pressed", dark ? "true" : "false");
    var label = btn.querySelector(".theme-toggle-label");
    if (label) label.textContent = dark ? "Day paper" : "Night lamp";
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".theme-toggle");
    if (!btn) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    try { localStorage.setItem(key, next); } catch (err) {}
    apply(next);
  });
  document.addEventListener("DOMContentLoaded", function () {
    apply(root.getAttribute("data-theme") || "light");
    var input = document.querySelector("[data-find]");
    if (!input) return;
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      document.querySelectorAll("[data-card]").forEach(function (card) {
        var hay = (card.getAttribute("data-card") || "").toLowerCase();
        card.hidden = q.length > 0 && hay.indexOf(q) === -1;
      });
    });
  });
})();
