/**
 * Sepete ekleme — tam sayfa yenileme / yönlendirme yapmadan AJAX ile.
 * Böylece tarayıcı geçmişine fazladan kayıt eklenmez; "sepete eklendi" mesajı
 * yüzünden geri tuşu bir önceki sayfaya geçemeden takılmaz.
 *
 * Form `data-cart-add` özniteliği taşımalıdır. JS yoksa veya istek başarısız
 * olursa form normal şekilde gönderilir (gerileme/fallback).
 */
(function () {
  function getToken(form) {
    var input = form.querySelector("input[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    return window.CSRF_TOKEN || "";
  }

  /** Üst menüdeki sepet rozetini (adet) günceller; yoksa oluşturur. */
  function updateCartBadge(count) {
    var cartLink = document.querySelector(".nav-link--cart");
    if (!cartLink) return;
    var badge = cartLink.querySelector(".badge");
    if (count > 0) {
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "badge";
        cartLink.appendChild(badge);
      }
      badge.textContent = count;
    } else if (badge) {
      badge.remove();
    }
  }

  var ICONS = {
    success:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    info:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    warning:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
    error:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
  };
  var TITLES = {
    success: "Başarılı",
    info: "Bilgi",
    warning: "Dikkat",
    error: "Hata",
  };

  var toastTimer = null;
  function showToast(message, level, title) {
    level = level || "success";
    if (!ICONS[level]) level = "success";
    var container = document.getElementById("cart-toast");
    if (!container) {
      container = document.createElement("div");
      container.id = "cart-toast";
      container.setAttribute("role", "status");
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    container.className = "cart-toast cart-toast--" + level;
    container.innerHTML =
      '<span class="cart-toast-icon" aria-hidden="true">' +
      (ICONS[level] || ICONS.success) +
      "</span>" +
      '<span class="cart-toast-body">' +
      '<span class="cart-toast-title"></span>' +
      '<span class="cart-toast-text"></span>' +
      "</span>" +
      '<span class="cart-toast-progress" aria-hidden="true"></span>';
    container.querySelector(".cart-toast-title").textContent =
      title || TITLES[level] || TITLES.success;
    container.querySelector(".cart-toast-text").textContent = message;

    // Yeniden tetiklemede animasyonu sıfırla
    void container.offsetWidth;
    container.classList.add("is-visible");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      container.classList.remove("is-visible");
    }, 3600);
  }

  // Diğer scriptlerin (ör. onay modalı) de kullanabilmesi için dışa aç.
  window.showToast = showToast;

  /**
   * Sunucudan gelen Django mesajlarını (base.html'deki gizli JSON) üstte değil,
   * sağ altta 3 saniyelik toast bildirimi olarak gösterir.
   */
  function showDjangoMessages() {
    var el = document.getElementById("dj-messages");
    if (!el) return;
    var list;
    try {
      list = JSON.parse(el.textContent || "[]");
    } catch (e) {
      return;
    }
    var levelMap = {
      success: "success",
      info: "info",
      warning: "warning",
      error: "error",
      debug: "info",
    };
    (list || []).forEach(function (m, i) {
      var level = levelMap[m.level] || "info";
      setTimeout(function () {
        showToast(m.text, level);
      }, i * 500);
    });
    el.remove();
  }

  if (document.readyState !== "loading") showDjangoMessages();
  else document.addEventListener("DOMContentLoaded", showDjangoMessages);

  /** Ortak AJAX form gönderimi (sepete ekle / stok bildirimi). */
  function ajaxSubmit(form, onData, title) {
    var submitBtn = form.querySelector("button[type=submit]");
    if (submitBtn) submitBtn.disabled = true;

    var action = form.getAttribute("action") || location.pathname;
    var body = new FormData(form);

    fetch(action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getToken(form),
      },
      body: body,
    })
      .then(function (r) {
        if (!r.ok) throw new Error("İstek başarısız");
        return r.json();
      })
      .then(function (data) {
        if (data.message) showToast(data.message, data.level, title);
        if (onData) onData(data);
      })
      .catch(function () {
        form.submit();
      })
      .finally(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
  }

  document.addEventListener("submit", function (e) {
    var addForm = e.target.closest("form[data-cart-add]");
    if (addForm) {
      e.preventDefault();
      ajaxSubmit(addForm, function (data) {
        if (typeof data.count === "number") updateCartBadge(data.count);
      }, "Sepete eklendi");
      return;
    }

    var notifyForm = e.target.closest("form[data-stock-notify]");
    if (notifyForm) {
      e.preventDefault();
      ajaxSubmit(notifyForm, function (data) {
        if (data.ok) {
          // Başarılı abonelikte formu kilitle (tekrar göndermeyi önle).
          var input = notifyForm.querySelector(".stock-notify-input");
          var btn = notifyForm.querySelector("button[type=submit]");
          if (input) input.readOnly = true;
          if (btn) {
            btn.disabled = true;
            btn.classList.add("is-done");
            btn.textContent = "Talebiniz alındı ✓";
          }
        }
      }, "Stok bildirimi");
      return;
    }
  });
})();
