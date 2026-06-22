/**
 * Özel onay penceresi — tarayıcının yerleşik confirm() kutusu yerine ekranın
 * ortasında profesyonel bir modal gösterir.
 *
 * Kullanım: bir formun `data-confirm="mesaj"` özniteliği olsun.
 *   - data-confirm-title   : başlık (varsayılan "Onay")
 *   - data-confirm-ok      : onay butonu metni (varsayılan "Onayla")
 *   - data-confirm-cancel  : vazgeç butonu metni (varsayılan "Vazgeç")
 *   - data-confirm-danger  : varsa onay butonu kırmızı (tehlikeli işlem)
 *   - data-ajax            : varsa form AJAX ile gönderilir (sayfa yenilenmez),
 *                            JSON yanıtındaki message sağ altta toast olarak gösterilir.
 */
(function () {
  var modal = document.getElementById("confirm-modal");
  if (!modal) return;

  var box = modal.querySelector(".confirm-modal-box");
  var titleEl = document.getElementById("confirm-modal-title");
  var textEl = document.getElementById("confirm-modal-text");
  var okBtn = document.getElementById("confirm-modal-ok");
  var iconEl = document.getElementById("confirm-modal-icon");
  var pendingForm = null;
  var lastFocused = null;

  function getToken(form) {
    var input = form && form.querySelector("input[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    return window.CSRF_TOKEN || "";
  }

  function toast(message, level) {
    if (typeof window.showToast === "function") {
      window.showToast(message, level);
    }
  }

  function openModal(form) {
    pendingForm = form;
    lastFocused = document.activeElement;

    titleEl.textContent = form.dataset.confirmTitle || "Onay";
    textEl.textContent = form.dataset.confirm || "Bu işlemi onaylıyor musunuz?";
    okBtn.textContent = form.dataset.confirmOk || "Onayla";

    var cancelBtn = modal.querySelector(".confirm-modal-cancel");
    if (cancelBtn) cancelBtn.textContent = form.dataset.confirmCancel || "Vazgeç";

    var danger = form.hasAttribute("data-confirm-danger");
    box.classList.toggle("is-danger", danger);

    modal.hidden = false;
    // reflow ile geçiş animasyonunu tetikle
    void modal.offsetWidth;
    modal.classList.add("is-open");
    document.body.classList.add("confirm-modal-open");
    okBtn.focus();
  }

  function closeModal() {
    modal.classList.remove("is-open");
    document.body.classList.remove("confirm-modal-open");
    pendingForm = null;
    var hideAfter = function () {
      modal.hidden = true;
      modal.removeEventListener("transitionend", hideAfter);
    };
    modal.addEventListener("transitionend", hideAfter);
    setTimeout(hideAfter, 260);
    if (lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  /** AJAX iptal sonrası sipariş detay sayfasını yerinde günceller. */
  function applyOrderCancelResult(form, data) {
    if (!form.classList.contains("order-cancel-form")) return;
    var badge = document.getElementById("order-status-badge");
    if (badge && data.status_code) {
      badge.className = "order-status order-status--" + data.status_code;
      if (data.status_display) badge.textContent = data.status_display;
    }
    var area = document.getElementById("order-cancel-area");
    if (area) {
      area.innerHTML =
        '<p class="order-cancel-note">Bu sipariş tarafınızdan iptal edildi.</p>';
    }
  }

  function submitForm(form) {
    if (!form.hasAttribute("data-ajax")) {
      // Onay alındı: normal gönderim (modal devre dışı bırakılarak).
      form.dataset.confirmed = "1";
      if (typeof form.requestSubmit === "function") form.requestSubmit();
      else form.submit();
      return;
    }

    okBtn.disabled = true;
    var action = form.getAttribute("action") || location.pathname;
    fetch(action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getToken(form),
      },
      body: new FormData(form),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("İstek başarısız");
        return r.json();
      })
      .then(function (data) {
        closeModal();
        if (data.message) toast(data.message, data.level);
        if (data.ok) applyOrderCancelResult(form, data);
      })
      .catch(function () {
        closeModal();
        // AJAX başarısızsa normal gönderime düş.
        form.dataset.confirmed = "1";
        form.submit();
      })
      .finally(function () {
        okBtn.disabled = false;
      });
  }

  document.addEventListener("submit", function (e) {
    var form = e.target.closest("form[data-confirm]");
    if (!form) return;
    if (form.dataset.confirmed === "1") {
      // Modal onayından sonra gerçek gönderim; tekrar yakalama.
      delete form.dataset.confirmed;
      return;
    }
    e.preventDefault();
    openModal(form);
  });

  okBtn.addEventListener("click", function () {
    if (pendingForm) submitForm(pendingForm);
  });

  modal.addEventListener("click", function (e) {
    if (e.target.closest("[data-confirm-close]")) {
      e.preventDefault();
      closeModal();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("is-open")) {
      closeModal();
    }
  });
})();
