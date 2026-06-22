/**
 * İletişim: aydınlatma onayı + KVKK metni diyalogu.
 */
(function () {
  const form = document.getElementById("contact-form-bize");
  const box = document.getElementById("contact-aydinlatma-onay");
  const clientErr = document.getElementById("contact-kvkk-client-error");
  const dialog = document.getElementById("contact-kvkk-dialog");
  const openBtn = document.getElementById("contact-kvkk-open");
  let lastFocus = null;

  function setKvkkError(msg) {
    if (!clientErr) return;
    if (msg) {
      clientErr.textContent = msg;
      clientErr.hidden = false;
    } else {
      clientErr.textContent = "";
      clientErr.hidden = true;
    }
  }

  function openDialog() {
    if (!dialog || typeof dialog.showModal !== "function") {
      window.alert(
        "Aydınlatma metni: 6698 sayılı KVKK kapsamında iletişim bilgileriniz yalnızca talebinize yanıt ve müşteri süreçleri için işlenir."
      );
      return;
    }
    lastFocus = document.activeElement;
    dialog.showModal();
    var closeX = dialog.querySelector(".contact-kvkk-dialog-x");
    if (closeX) closeX.focus();
  }

  function closeDialog() {
    if (!dialog || !dialog.open) return;
    dialog.close();
  }

  if (openBtn) {
    openBtn.addEventListener("click", function (e) {
      e.preventDefault();
      openDialog();
    });
  }

  if (dialog) {
    dialog.addEventListener("close", function () {
      if (lastFocus && typeof lastFocus.focus === "function") {
        lastFocus.focus();
      } else if (openBtn) {
        openBtn.focus();
      }
    });
    dialog.querySelectorAll("[data-contact-kvkk-close]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        closeDialog();
      });
    });
  }

  if (form && box) {
    form.addEventListener("submit", function (e) {
      if (!box.checked) {
        e.preventDefault();
        setKvkkError(
          "Aydınlatma metnini okuyup onay kutusunu işaretlemeden form gönderilemez."
        );
        box.focus();
        return;
      }
      setKvkkError("");
    });

    box.addEventListener("change", function () {
      if (box.checked) setKvkkError("");
    });
  }
})();
