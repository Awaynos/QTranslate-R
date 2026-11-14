(function () {
  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js");

  var header = document.getElementById("siteHeader");
  function onScroll() {
    if (header) header.classList.toggle("stuck", window.scrollY > 6);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var menuBtn = document.getElementById("menuBtn");
  var navLinks = document.getElementById("navLinks");
  function closeMenu() {
    if (!navLinks || !menuBtn) return;
    navLinks.classList.remove("open");
    menuBtn.setAttribute("aria-expanded", "false");
  }
  if (menuBtn && navLinks) {
    menuBtn.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    navLinks.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeMenu();
    });
  }

  var toast = document.getElementById("toast");
  var toastTimer;
  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove("show"); }, 1900);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy") ? resolve() : reject();
      } catch (err) {
        reject(err);
      }
      document.body.removeChild(ta);
    });
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".copy");
    if (!btn) return;
    e.preventDefault();
    var text = btn.getAttribute("data-copy") || "";
    copyText(text).then(function () {
      var old = btn.textContent;
      btn.classList.add("ok");
      btn.textContent = "Готово";
      showToast("Скопировано");
      setTimeout(function () {
        btn.classList.remove("ok");
        btn.textContent = old;
      }, 1600);
    }).catch(function () {
      showToast("Не удалось скопировать");
    });
  });

  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.04 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  var shots = document.getElementById("shots");
  var shotsPrev = document.getElementById("shotsPrev");
  var shotsNext = document.getElementById("shotsNext");
  function shotStep() {
    var first = shots ? shots.querySelector(".shot") : null;
    return first ? first.getBoundingClientRect().width + 12 : 420;
  }
  function updateShots() {
    if (!shots) return;
    var max = shots.scrollWidth - shots.clientWidth - 2;
    if (shotsPrev) shotsPrev.disabled = shots.scrollLeft <= 2;
    if (shotsNext) shotsNext.disabled = shots.scrollLeft >= max;
  }
  if (shots) {
    if (shotsPrev) shotsPrev.addEventListener("click", function () { shots.scrollBy({ left: -shotStep(), behavior: "smooth" }); });
    if (shotsNext) shotsNext.addEventListener("click", function () { shots.scrollBy({ left: shotStep(), behavior: "smooth" }); });
    shots.addEventListener("scroll", updateShots, { passive: true });
    window.addEventListener("resize", updateShots);
    updateShots();
  }

  var lightbox = document.getElementById("lightbox");
  var lbImg = document.getElementById("lbImg");
  var lbCap = document.getElementById("lbCap");
  var lbIndex = document.getElementById("lbIndex");
  var lbClose = document.getElementById("lbClose");
  var lbPrev = document.getElementById("lbPrev");
  var lbNext = document.getElementById("lbNext");
  var shotButtons = Array.prototype.slice.call(document.querySelectorAll(".shot button"));
  var lbPos = 0;
  var lastFocus = null;

  function pad(n) { return n < 10 ? "0" + n : String(n); }

  function renderLb() {
    var btn = shotButtons[lbPos];
    if (!btn) return;
    var img = btn.querySelector("img");
    var full = btn.getAttribute("data-full") || (img ? img.src : "");
    lbImg.src = full;
    lbImg.alt = img ? img.alt : "";
    lbCap.textContent = btn.getAttribute("data-cap") || "";
    lbIndex.textContent = pad(lbPos + 1);
  }

  function openLb(index) {
    if (!lightbox || !shotButtons.length) return;
    lastFocus = document.activeElement;
    lbPos = index;
    renderLb();
    lightbox.classList.add("open");
    document.body.style.overflow = "hidden";
    lbClose.focus();
  }

  function closeLb() {
    if (!lightbox) return;
    lightbox.classList.remove("open");
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  shotButtons.forEach(function (btn, index) {
    btn.addEventListener("click", function () { openLb(index); });
  });
  if (lbClose) lbClose.addEventListener("click", closeLb);
  if (lbPrev) lbPrev.addEventListener("click", function () {
    lbPos = (lbPos - 1 + shotButtons.length) % shotButtons.length;
    renderLb();
  });
  if (lbNext) lbNext.addEventListener("click", function () {
    lbPos = (lbPos + 1) % shotButtons.length;
    renderLb();
  });
  if (lightbox) {
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLb();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMenu();
      if (lightbox && lightbox.classList.contains("open")) closeLb();
    }
    if (lightbox && lightbox.classList.contains("open")) {
      if (e.key === "ArrowLeft" && lbPrev) lbPrev.click();
      if (e.key === "ArrowRight" && lbNext) lbNext.click();
    }
  });

  var demoData = [
    {
      text: "Перевод — это мост между языками.",
      out: "Translation is a bridge between languages.",
      range: "0.5–0.9 с",
      times: ["540 мс", "610 мс", "720 мс", "580 мс", "840 мс", "490 мс", "910 мс"]
    },
    {
      text: "Доброе утро, мой друг!",
      out: "Good morning, my friend!",
      range: "0.5–0.8 с",
      times: ["510 мс", "600 мс", "690 мс", "550 мс", "800 мс", "470 мс", "880 мс"]
    },
    {
      text: "Обновление уже готово.",
      out: "The update is ready.",
      range: "0.4–0.8 с",
      times: ["480 мс", "570 мс", "650 мс", "530 мс", "760 мс", "450 мс", "820 мс"]
    }
  ];
  var demoSelected = document.getElementById("demoSelected");
  var demoResults = document.getElementById("demoResults");
  var demoTime = document.getElementById("demoTime");
  var demoCopy = document.querySelector(".result-foot .copy");
  var demoPhrases = Array.prototype.slice.call(document.querySelectorAll(".phrase"));
  var demoRows = demoResults ? Array.prototype.slice.call(demoResults.querySelectorAll(".result-row")) : [];
  var demoTimer;

  function renderDemo(index) {
    var data = demoData[index];
    if (!data) return;
    demoPhrases.forEach(function (btn, i) { btn.classList.toggle("is-active", i === index); });
    if (demoSelected) demoSelected.textContent = data.text;
    if (demoCopy) demoCopy.setAttribute("data-copy", data.out);
    if (demoTime) demoTime.textContent = "7 сервисов · " + data.range;
    if (!demoResults) return;
    demoResults.classList.add("is-swapping");
    clearTimeout(demoTimer);
    demoTimer = setTimeout(function () {
      demoRows.forEach(function (row, i) {
        var tr = row.querySelector(".result-tr");
        var ms = row.querySelector(".result-ms");
        if (tr) tr.textContent = data.out;
        if (ms) ms.textContent = data.times[i] || "";
      });
      demoResults.classList.remove("is-swapping");
    }, 150);
  }

  demoPhrases.forEach(function (btn, index) {
    btn.addEventListener("click", function () { renderDemo(index); });
  });

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
