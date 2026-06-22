"""Sipariş durumu değiştiğinde stok geri yükleme ve müşteri bilgilendirme maili.

Durum; admin liste ekranı, admin düzenleme formu veya kullanıcı iptali gibi
herhangi bir yerden değiştirilse de yakalanır.
"""

from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from . import emails as order_emails
from .models import Order


@receiver(post_init, sender=Order)
def _remember_status(sender, instance, **kwargs):
    instance._original_status = instance.status


@receiver(post_save, sender=Order)
def _notify_status_change(sender, instance, created, **kwargs):
    if created:
        instance._original_status = instance.status
        return
    old_status = getattr(instance, "_original_status", None)
    if old_status is None or old_status == instance.status:
        return

    # İptal durumuna geçildiğinde (admin veya kullanıcı) stok geri yüklenir.
    if old_status not in instance.cancelled_statuses and instance.is_cancelled:
        instance.restore_stock()

    order_emails.send_status_update(instance)
    instance._original_status = instance.status
