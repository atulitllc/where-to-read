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
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
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
    var box = document.getElementById("find-results");
    var shelves = document.getElementById("shelves");
    if (!box) {
      input.addEventListener("input", function () {
        var q = input.value.trim().toLowerCase();
        document.querySelectorAll("[data-card]").forEach(function (card) {
          var hay = (card.getAttribute("data-card") || "").toLowerCase();
          card.hidden = q.length > 0 && hay.indexOf(q) === -1;
        });
        document.querySelectorAll("[data-letter]").forEach(function (block) {
          var any = false;
          block.querySelectorAll("[data-card]").forEach(function (card) {
            if (!card.hidden) any = true;
          });
          block.hidden = q.length > 0 && !any;
        });
      });
      return;
    }
    var cache = null;
    function paint(rows) {
      var q = input.value.trim().toLowerCase();
      if (q.length < 2) {
        box.hidden = true;
        box.innerHTML = "";
        if (shelves) shelves.hidden = false;
        return;
      }
      var hits = [];
      for (var i = 0; i < rows.length && hits.length < 16; i++) {
        var row = rows[i];
        if ((row.t + " " + row.a).toLowerCase().indexOf(q) !== -1) hits.push(row);
      }
      if (shelves) shelves.hidden = true;
      box.hidden = false;
      if (!hits.length) {
        box.innerHTML = "<li>No titles match. Open a subject for the full list.</li>";
        return;
      }
      box.innerHTML = hits.map(function (row) {
        return '<li><a href="books/' + encodeURIComponent(row.s) + '/">' + esc(row.t) + '</a> <span>· ' + esc(row.a) + "</span></li>";
      }).join("");
    }
    input.addEventListener("input", function () {
      if (cache) paint(cache);
      else fetch("search.json").then(function (r) { return r.json(); }).then(function (rows) { cache = rows; paint(rows); });
    });
  });
})();
