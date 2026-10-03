/* ==========================================================================
   NutriTrack – frontend scripts
   ========================================================================== */
(function () {
  "use strict";

  /* ---------- Toasts auto-dismiss ---------- */
  function initToasts() {
    var stack = document.getElementById("toastStack");
    if (!stack) return;
    setTimeout(function () {
      stack.style.transition = "opacity .4s ease";
      stack.style.opacity = "0";
      setTimeout(function () { stack.remove(); }, 400);
    }, 4000);
  }

  /* ---------- Sidebar (mobile) ---------- */
  function initSidebar() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");
    var openBtn = document.getElementById("topbarMenu");
    var closeBtn = document.getElementById("sidebarClose");
    if (!sidebar) return;

    function open() {
      sidebar.classList.add("open");
      if (overlay) overlay.classList.add("show");
    }
    function close() {
      sidebar.classList.remove("open");
      if (overlay) overlay.classList.remove("show");
    }
    if (openBtn) openBtn.addEventListener("click", open);
    if (closeBtn) closeBtn.addEventListener("click", close);
    if (overlay) overlay.addEventListener("click", close);
  }

  /* ---------- Landing nav (mobile) ---------- */
  function initLandingNav() {
    var toggle = document.getElementById("navToggle");
    var links = document.querySelector(".nav-links");
    if (!toggle || !links) return;
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });
  }

  /* ---------- Password toggles ---------- */
  function initPasswordToggles() {
    document.querySelectorAll(".pwd-toggle").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = document.getElementById(btn.getAttribute("data-target"));
        if (!input) return;
        if (input.type === "password") {
          input.type = "text";
          btn.querySelector("i").className = "lucide eye-off";
        } else {
          input.type = "password";
          btn.querySelector("i").className = "lucide eye";
        }
      });
    });
  }

  /* ---------- Food form toggle ---------- */
  function initFoodFormToggle() {
    var btn = document.getElementById("toggleFoodForm");
    var form = document.getElementById("foodForm");
    if (!btn || !form) return;
    btn.addEventListener("click", function () {
      form.classList.toggle("collapsed");
    });
  }

  /* ---------- Built-in food database quick fill ---------- */
  function initFoodDatabase() {
    var nameInput = document.getElementById("foodName");
    var datalist = document.getElementById("builtinFoods");
    if (!nameInput || !datalist) return;

    var fields = {
      calories: document.getElementById("fCalories"),
      protein: document.getElementById("fProtein"),
      carbs: document.getElementById("fCarbs"),
      fat: document.getElementById("fFat"),
      fiber: document.getElementById("fFiber"),
    };

    var db = null;

    fetch("/api/food-database")
      .then(function (r) { return r.json(); })
      .then(function (items) {
        db = items;
        items.forEach(function (item) {
          var opt = document.createElement("option");
          opt.value = item.food_name;
          datalist.appendChild(opt);
        });
      })
      .catch(function () { /* silent */ });

    nameInput.addEventListener("change", function () {
      if (!db) return;
      var match = db.filter(function (f) {
        return f.food_name.toLowerCase() === nameInput.value.trim().toLowerCase();
      })[0];
      if (match) {
        fields.calories.value = match.calories;
        fields.protein.value = match.protein;
        fields.carbs.value = match.carbs;
        fields.fat.value = match.fat;
        fields.fiber.value = match.fiber;
      }
    });
  }

  /* ---------- Calorie progress ring ---------- */
  function initCaloriesRing() {
    var ring = document.getElementById("caloriesRing");
    if (!ring || !window.NUTRI) return;
    var circumference = 2 * Math.PI * 86;
    ring.style.strokeDasharray = circumference;
    var target = window.NUTRI.target || 1;
    var consumed = window.NUTRI.calories || 0;
    var pct = Math.min(consumed / target, 1);
    var offset = circumference * (1 - pct);
    requestAnimationFrame(function () {
      ring.style.strokeDashoffset = offset;
    });
  }

  /* ---------- Confetti for balanced days ---------- */
  function initConfetti() {
    if (!window.NUTRI || window.NUTRI.status !== "balanced") return;
    var canvas = document.getElementById("confettiCanvas");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    canvas.classList.add("show");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    var colors = ["#6C63FF", "#A78BFA", "#A7F3D0", "#FED7AA", "#FBCFE8", "#10B981"];
    var particles = [];
    for (var i = 0; i < 120; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * -canvas.height,
        r: Math.random() * 6 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        vy: Math.random() * 3 + 2,
        vx: Math.random() * 2 - 1,
        rot: Math.random() * 360,
        vrot: Math.random() * 4 - 2,
      });
    }

    var frames = 0;
    var maxFrames = 240;

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(function (p) {
        p.y += p.vy;
        p.x += p.vx;
        p.rot += p.vrot;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rot * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 0.6);
        ctx.restore();
      });
      frames++;
      if (frames < maxFrames) {
        requestAnimationFrame(draw);
      } else {
        canvas.classList.remove("show");
      }
    }
    draw();
  }

  /* ---------- Charts ---------- */
  function chartFontColor() { return "#64748B"; }
  function gridColor() { return "rgba(226,232,240,0.6)"; }

  function initAnalyticsCharts() {
    if (!window.NUTRI_WEEK || !window.Chart) return;
    var week = window.NUTRI_WEEK;
    var labels = week.map(function (d) { return d.label; });
    var calData = week.map(function (d) { return d.calories; });
    var proData = week.map(function (d) { return d.protein; });
    var carbData = week.map(function (d) { return d.carbs; });
    var fatData = week.map(function (d) { return d.fat; });
    var target = window.NUTRI_TARGET;

    var baseOpts = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: chartFontColor() } },
        y: { grid: { color: gridColor() }, ticks: { color: chartFontColor() }, beginAtZero: true },
      },
    };

    function lineChart(id, data, color, label) {
      var el = document.getElementById(id);
      if (!el) return null;
      return new Chart(el, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: label,
              data: data,
              borderColor: color,
              backgroundColor: color + "22",
              fill: true,
              tension: 0.4,
              pointBackgroundColor: color,
              pointRadius: 5,
              pointHoverRadius: 7,
              borderWidth: 3,
            },
          ],
        },
        options: baseOpts,
      });
    }

    lineChart("caloriesChart", calData, "#6C63FF", "Calories");
    lineChart("proteinChart", proData, "#6C63FF", "Protein (g)");
    lineChart("carbsChart", carbData, "#F59E0B", "Carbs (g)");
    lineChart("fatChart", fatData, "#EC4899", "Fat (g)");

    // Weekly summary chart
    var weeklyEl = document.getElementById("weeklyCaloriesChart");
    if (weeklyEl) {
      new Chart(weeklyEl, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Calories",
              data: calData,
              backgroundColor: calData.map(function (c) {
                if (c === 0) return "#E2E8F0";
                if (c > target * 1.15) return "#FBCFE8";
                if (c < target * 0.8) return "#FED7AA";
                return "#A7F3D0";
              }),
              borderRadius: 10,
              borderSkipped: false,
            },
            {
              label: "Target",
              data: Array(7).fill(target),
              type: "line",
              borderColor: "#6C63FF",
              borderDash: [6, 4],
              pointRadius: 0,
              fill: false,
            },
          ],
        },
        options: baseOpts,
      });
    }

    // Macro donut
    var donutEl = document.getElementById("macroDonut");
    if (donutEl) {
      var sumPro = proData.reduce(function (a, b) { return a + b; }, 0);
      var sumCarb = carbData.reduce(function (a, b) { return a + b; }, 0);
      var sumFat = fatData.reduce(function (a, b) { return a + b; }, 0);
      new Chart(donutEl, {
        type: "doughnut",
        data: {
          labels: ["Protein", "Carbohydrates", "Fat"],
          datasets: [
            {
              data: [sumPro * 4, sumCarb * 4, sumFat * 9],
              backgroundColor: ["#6C63FF", "#F59E0B", "#EC4899"],
              borderWidth: 0,
              hoverOffset: 8,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "65%",
          plugins: {
            legend: { position: "bottom", labels: { color: chartFontColor(), padding: 16, usePointStyle: true } },
          },
        },
      });
    }
  }

  /* ---------- Init on DOM ready ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    initToasts();
    initSidebar();
    initLandingNav();
    initPasswordToggles();
    initFoodFormToggle();
    initFoodDatabase();
    initCaloriesRing();
    initConfetti();
    initAnalyticsCharts();
  });
})();
