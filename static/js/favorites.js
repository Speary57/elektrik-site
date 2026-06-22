/** Favori (kalp) butonu — giriş yapmış kullanıcı için AJAX ile ekle/çıkar. */
(function () {
  function getToken() {
    return window.CSRF_TOKEN || "";
  }

  function syncFavoritesEmptyState() {
    var grid = document.getElementById("favorites-grid");
    var empty = document.getElementById("favorites-empty");
    if (!grid || !empty) return;
    var hasCards = grid.querySelectorAll(".card").length > 0;
    grid.hidden = !hasCards;
    empty.hidden = hasCards;
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-fav-toggle]");
    if (!btn) return;
    e.preventDefault();
    if (btn.disabled) return;

    var url = btn.dataset.url;
    if (!url) return;
    btn.disabled = true;

    fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getToken(),
      },
    })
      .then(function (r) {
        if (!r.ok) throw new Error("İstek başarısız");
        return r.json();
      })
      .then(function (data) {
        var active = !!data.active;
        // Aynı ürünün tüm kalp butonlarını (kartlar + detay) güncelle
        document
          .querySelectorAll('[data-fav-toggle][data-url="' + url + '"]')
          .forEach(function (el) {
            el.classList.toggle("is-active", active);
            el.setAttribute("aria-pressed", active ? "true" : "false");
          });
        // Sağ altta 3 saniyelik bildirim
        if (typeof window.showToast === "function") {
          if (active) {
            window.showToast(
              "Ürün başarıyla favorilerim bölümüne eklendi.",
              "success",
              "Favorilere eklendi"
            );
          } else {
            window.showToast(
              "Ürün favorilerinizden çıkarıldı.",
              "info",
              "Favorilerden çıkarıldı"
            );
          }
        }
        // Favorilerim sayfasındaysak ve çıkarıldıysa kartı kaldır; liste boşaldıysa boş durumu göster
        if (!active && document.getElementById("favorites-grid")) {
          var card = btn.closest(".card");
          if (card) card.remove();
          syncFavoritesEmptyState();
        }
      })
      .catch(function () {})
      .finally(function () {
        btn.disabled = false;
      });
  });
})();
