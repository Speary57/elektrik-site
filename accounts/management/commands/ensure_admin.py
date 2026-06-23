import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ortam değişkenlerinden yönetici (superuser) oluşturur veya şifresini günceller."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        email = os.environ.get("ADMIN_EMAIL", "kilaguzelektrik@gmail.com").strip()
        password = os.environ.get("ADMIN_PASSWORD", "").strip()

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_PASSWORD tanımlı değil; yönetici oluşturulmadı."
                )
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        if not created:
            user.email = email
            user.is_staff = True
            user.is_superuser = True

        user.set_password(password)
        user.save()

        action = "oluşturuldu" if created else "güncellendi"
        self.stdout.write(
            self.style.SUCCESS(
                f"Yönetici kullanıcı {action}: {username} ({email})"
            )
        )
