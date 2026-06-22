/**
 * Tek sayfa: ana / hakkımızda / ürünler / hizmetlerimiz / iletişim yatay geçiş + hash.
 * Üst menü sırası ile .spa-panel DOM sırası aynı olmalı (yatay kaydırma yönü tutarlı olsun).
 * Track yüksekliği yalnızca aktif panele göre ayarlanır (alt boşluk olmaz).
 */
(function () {
  const viewport = document.getElementById("spa-viewport");
  const track = document.getElementById("spa-track");
  if (!viewport || !track) return;

  const order = ["ana", "hakkimizda", "urunler", "hizmetlerimiz", "iletisim"];
  const panelCount = order.length;
  const panels = Array.from(track.querySelectorAll(".spa-panel"));
  let activeIndex = 0;
  let ro = null;
  /* #spa-urunler içeriğinin sunucudan hangi sorguyla yüklendiğini izler (gereksiz fetch'i önler). */
  let loadedCatalogSearch = location.search;

  if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
  }

  /** Sayfa en üstünden başlasın (hash / dış sayfa geçişlerinde tarayıcı kaydırmasını ez). */
  function forceScrollTop() {
    window.scrollTo(0, 0);
    requestAnimationFrame(function () {
      window.scrollTo(0, 0);
      requestAnimationFrame(function () {
        window.scrollTo(0, 0);
      });
    });
    setTimeout(function () {
      window.scrollTo(0, 0);
    }, 0);
    setTimeout(function () {
      window.scrollTo(0, 0);
    }, 80);
    setTimeout(function () {
      window.scrollTo(0, 0);
    }, 200);
  }

  function panelIndex(name) {
    const i = order.indexOf(name);
    return i >= 0 ? i : 0;
  }

  function nameFromHash() {
    const h = (location.hash || "#spa-ana").replace(/^#/, "");
    if (h === "spa-ana") return "ana";
    if (h === "spa-hakkimizda") return "hakkimizda";
    if (h === "spa-urunler") return "urunler";
    if (h === "spa-hizmetlerimiz") return "hizmetlerimiz";
    if (h === "spa-iletisim") return "iletisim";
    return "ana";
  }

  let pendingScrollTarget = null;

  function measurePanelHeight(panel) {
    const inner = panel.querySelector(":scope > .container") || panel;
    const pcs = getComputedStyle(panel);
    const padY =
      (parseFloat(pcs.paddingTop) || 0) + (parseFloat(pcs.paddingBottom) || 0);
    /* scrollHeight: iletişim/harita gibi uzun içerik track'te kesilmesin, yukarı kaydırma kilitlenmesin */
    const innerH = Math.max(inner.scrollHeight, inner.offsetHeight);
    return Math.ceil(Math.max(innerH + padY, panel.scrollHeight, 1));
  }

  function syncTrackHeight() {
    const panel = panels[activeIndex];
    if (!panel) return;
    track.style.height = measurePanelHeight(panel) + "px";
  }

  function headerScrollOffset() {
    const header = document.querySelector(".site-header");
    return (header ? header.offsetHeight : 0) + 14;
  }

  function goToIndex(i, opts) {
    opts = opts || {};
    i = Math.max(0, Math.min(panelCount - 1, i));
    activeIndex = i;
    if (!opts.skipForceScrollTop) {
      forceScrollTop();
    }
    const pct = (i * 100) / panelCount;
    track.style.transform = "translateX(-" + pct + "%)";

    panels.forEach(function (panel, idx) {
      if (idx === i) {
        panel.removeAttribute("inert");
        panel.removeAttribute("aria-hidden");
      } else {
        panel.setAttribute("inert", "");
        panel.setAttribute("aria-hidden", "true");
      }
    });

    document.querySelectorAll(".spa-nav-header").forEach(function (a) {
      const match = a.dataset.spaPanel === order[i];
      a.classList.toggle("is-active", match);
      if (match) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });

    syncTrackHeight();
    requestAnimationFrame(function () {
      syncTrackHeight();
      requestAnimationFrame(syncTrackHeight);
    });
  }

  function applyFromUrl() {
    const params = new URLSearchParams(location.search);
    if (params.has("q") || params.has("kategori")) {
      goToIndex(panelIndex("urunler"));
      if (location.hash !== "#spa-urunler") {
        history.replaceState(null, "", location.pathname + location.search + "#spa-urunler");
      }
    } else {
      const scrollMap = params.has("harita");
      goToIndex(panelIndex(nameFromHash()), { skipForceScrollTop: scrollMap });
    }
    if (params.has("harita")) {
      params.delete("harita");
      const qs = params.toString();
      history.replaceState(
        null,
        "",
        location.pathname + (qs ? "?" + qs : "") + (location.hash || "#spa-iletisim")
      );
      scrollToTarget("contact-map");
    }
  }

  /** Aktif panel içindeki bir öğeye (ör. harita) yumuşak kaydırma. */
  function scrollToTarget(id) {
    pendingScrollTarget = id;
    function run() {
      syncTrackHeight();
      const el = document.getElementById(id);
      if (!el) return;
      const top =
        el.getBoundingClientRect().top +
        window.pageYOffset -
        headerScrollOffset() -
        170;
      window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    }
    requestAnimationFrame(function () {
      setTimeout(run, 380);
      setTimeout(function () {
        syncTrackHeight();
        run();
      }, 850);
      setTimeout(function () {
        pendingScrollTarget = null;
      }, 1200);
    });
  }

  function observeInners() {
    if (!ro) return;
    ro.disconnect();
    panels.forEach(function (p) {
      const inner = p.querySelector(":scope > .container");
      ro.observe(inner || p);
    });
  }

  /** Ürünler ızgarasına yumuşak açılış animasyonu (yeniden tetiklenebilir). */
  function animateCatalogGrid() {
    const grid = document.querySelector("#spa-urunler .grid-products--catalog");
    if (!grid) return;
    grid.classList.remove("catalog-grid-enter");
    void grid.offsetWidth;
    grid.classList.add("catalog-grid-enter");
  }

  /**
   * #spa-urunler içeriğini verilen sorguya (?kategori / ?q) göre AJAX ile günceller;
   * tam sayfa yenilemeden kategori/arama geçişini sağlar.
   */
  function ensureCatalogContent(search, done) {
    if (search === loadedCatalogSearch) {
      if (done) done();
      return;
    }
    const url = location.pathname + search;
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (r) {
        return r.text();
      })
      .then(function (html) {
        const doc = new DOMParser().parseFromString(html, "text/html");
        const fresh = doc.getElementById("spa-urunler");
        const current = document.getElementById("spa-urunler");
        if (fresh && current) {
          current.innerHTML = fresh.innerHTML;
          loadedCatalogSearch = search;
          observeInners();
          animateCatalogGrid();
        }
        if (done) done();
      })
      .catch(function () {
        window.location.href = url + "#spa-urunler";
      });
  }

  /** Ürünler paneline geç + içeriği sorguyla eşitle (kategori/arama). */
  function goToCatalog(search, push) {
    if (push) {
      history.pushState(null, "", location.pathname + search + "#spa-urunler");
    }
    goToIndex(panelIndex("urunler"));
    ensureCatalogContent(search, syncTrackHeight);
  }

  /**
   * Ana sayfadaki "Malzeme ara" kutusundan yazılınca: Ürünler paneline geç,
   * sorguya göre içeriği yükle ve odağı oradaki arama kutusuna devret (canlı arama).
   */
  function goToCatalogFromHome(search) {
    history.pushState(null, "", location.pathname + search + "#spa-urunler");
    goToIndex(panelIndex("urunler"));
    ensureCatalogContent(search, function () {
      syncTrackHeight();
      const inp = document.querySelector(
        "#spa-urunler input[type='search'][name='q']"
      );
      if (inp) {
        inp.focus();
        const v = inp.value;
        try {
          inp.setSelectionRange(v.length, v.length);
        } catch (err) {
          /* bazı tarayıcılar search input'ta setSelectionRange desteklemez */
        }
      }
    });
  }

  /** Kategori rozetlerinin href'lerindeki q (arama) parametresini günceller. */
  function updateChipQueries(q) {
    document
      .querySelectorAll("#spa-urunler .chips--toolbar a.chip")
      .forEach(function (chip) {
        let u;
        try {
          u = new URL(chip.href, location.origin);
        } catch (err) {
          return;
        }
        if (q) u.searchParams.set("q", q);
        else u.searchParams.delete("q");
        chip.setAttribute("href", u.pathname + u.search + "#spa-urunler");
      });
  }

  /**
   * Canlı arama: yalnızca ürün ızgarasını (.catalog-products-wrap) AJAX ile değiştirir.
   * Arama kutusu DOM'da kaldığı için odak ve imleç korunur.
   */
  let liveSearchTimer = null;
  function runLiveSearch(form) {
    const params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      if (String(value).trim() !== "") params.append(key, value);
    });
    const qs = params.toString();
    const search = qs ? "?" + qs : "";
    if (search === loadedCatalogSearch) return;
    history.replaceState(null, "", location.pathname + search + "#spa-urunler");
    const url = location.pathname + search;
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (r) {
        return r.text();
      })
      .then(function (html) {
        const doc = new DOMParser().parseFromString(html, "text/html");
        const fresh = doc.querySelector("#spa-urunler .catalog-products-wrap");
        const current = document.querySelector(
          "#spa-urunler .catalog-products-wrap"
        );
        if (fresh && current) {
          current.innerHTML = fresh.innerHTML;
          loadedCatalogSearch = search;
          updateChipQueries(params.get("q") || "");
          observeInners();
          animateCatalogGrid();
          syncTrackHeight();
        }
      })
      .catch(function () {});
  }

  /** İletişim formu POST sonrası: tarayıcının hash kaydırmasını ezerek sayfayı en üste alır. */
  function finishIletisimFormReturnScroll() {
    const params = new URLSearchParams(location.search);
    if (!params.has("iletisim_scroll")) return;
    params.delete("iletisim_scroll");
    const qs = params.toString();
    history.replaceState(
      null,
      "",
      location.pathname + (qs ? "?" + qs : "") + location.hash
    );
    function bump() {
      window.scrollTo(0, 0);
    }
    bump();
    requestAnimationFrame(function () {
      bump();
      requestAnimationFrame(bump);
    });
    window.addEventListener(
      "load",
      function () {
        bump();
        setTimeout(bump, 0);
      },
      { once: true }
    );
    setTimeout(bump, 60);
    setTimeout(bump, 180);
  }

  viewport.classList.add("spa-ready");
  forceScrollTop();
  /* Taban çizgisini translateX(0)'da sabitle: ardından applyFromUrl hedef panele
     her zaman transition ile kayar (dış sayfadan gelişte animasyon tutarlı olur). */
  void track.offsetWidth;

  if (typeof ResizeObserver !== "undefined") {
    ro = new ResizeObserver(function () {
      syncTrackHeight();
    });
    observeInners();
  }

  window.addEventListener("resize", function () {
    syncTrackHeight();
  });

  document.addEventListener("click", function (e) {
    const a = e.target.closest("a[href*='#spa-']");
    if (!a || !a.getAttribute("href")) return;
    if (!document.getElementById("spa-viewport")) return;
    let u;
    try {
      u = new URL(a.href, location.origin);
    } catch (err) {
      return;
    }
    if (u.pathname !== location.pathname) return;
    const m = u.hash.match(/^#spa-(ana|hakkimizda|urunler|hizmetlerimiz|iletisim)$/);
    if (!m) return;
    e.preventDefault();
    if (m[1] === "urunler") {
      // Kategori / arama bağlantıları: sayfayı yenilemeden içerik değişir.
      goToCatalog(u.search, true);
      return;
    }
    // Diğer paneller: sorgu temizlenir, yalnızca yatay geçiş.
    history.pushState(null, "", u.pathname + u.search + u.hash);
    const scrollId = a.dataset.spaScroll || "";
    goToIndex(panelIndex(m[1]), { skipForceScrollTop: !!scrollId });
    if (scrollId) {
      scrollToTarget(scrollId);
    }
  });

  // Sıralama seçimi değişince filtre formunu otomatik gönder (SPA içinde).
  document.addEventListener("change", function (e) {
    const el = e.target.closest("#spa-urunler [data-autosubmit]");
    if (!el) return;
    if (!document.getElementById("spa-viewport")) return;
    const form = el.closest("form.search-form");
    if (!form) return;
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
  });

  document.addEventListener("input", function (e) {
    const input = e.target.closest(
      "#spa-urunler input[type='search'][name='q']"
    );
    if (!input) return;
    if (!document.getElementById("spa-viewport")) return;
    const form = input.closest("form.search-form");
    if (!form) return;
    clearTimeout(liveSearchTimer);
    liveSearchTimer = setTimeout(function () {
      runLiveSearch(form);
    }, 250);
  });

  let homeSearchTimer = null;
  document.addEventListener("input", function (e) {
    const input = e.target.closest(
      ".home-search-form input[type='search'][name='q']"
    );
    if (!input) return;
    if (!document.getElementById("spa-viewport")) return;
    clearTimeout(homeSearchTimer);
    homeSearchTimer = setTimeout(function () {
      const qv = input.value.trim();
      // Kutu boşsa (silindiyse) Ürünler paneline gönderme; sadece metin varken gönder.
      if (!qv) return;
      const params = new URLSearchParams();
      params.append("q", qv);
      goToCatalogFromHome("?" + params.toString());
    }, 250);
  });

  document.addEventListener("submit", function (e) {
    const form = e.target.closest("form.search-form");
    if (!form) return;
    if (!document.getElementById("spa-viewport")) return;
    e.preventDefault();
    clearTimeout(liveSearchTimer);
    clearTimeout(homeSearchTimer);
    const action = form.getAttribute("action") || location.pathname;
    let actionUrl;
    try {
      actionUrl = new URL(action, location.origin);
    } catch (err) {
      form.submit();
      return;
    }
    if (actionUrl.pathname !== location.pathname) {
      form.submit();
      return;
    }
    const params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      if (String(value).trim() !== "") params.append(key, value);
    });
    const qs = params.toString();
    goToCatalog(qs ? "?" + qs : "", true);
  });

  window.addEventListener("hashchange", function () {
    const params = new URLSearchParams(location.search);
    if (params.has("q") || params.has("kategori")) {
      goToIndex(panelIndex("urunler"));
      return;
    }
    goToIndex(panelIndex(nameFromHash()));
  });

  window.addEventListener("popstate", function () {
    const params = new URLSearchParams(location.search);
    if (nameFromHash() === "urunler" || params.has("q") || params.has("kategori")) {
      goToCatalog(location.search, false);
    } else {
      goToIndex(panelIndex(nameFromHash()));
    }
  });

  window.addEventListener("load", function () {
    syncTrackHeight();
    if (!pendingScrollTarget) {
      forceScrollTop();
    }
  });

  applyFromUrl();
  finishIletisimFormReturnScroll();
  if (!pendingScrollTarget) {
    forceScrollTop();
  }
})();
