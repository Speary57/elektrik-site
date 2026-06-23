import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = (
        "ADMIN_EMAIL ile eşleşen kayıtlı kullanıcıyı yönetici yapar; "
        "yoksa ADMIN_USERNAME ile yeni yönetici oluşturur."
    )

    def handle(self, *args, **options):
        email = os.environ.get("ADMIN_EMAIL", "alispeary57@gmail.com").strip()
        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        password = os.environ.get("ADMIN_PASSWORD", "").strip()

        User = get_user_model()

        if email:
            user = User.objects.filter(
                Q(email__iexact=email) | Q(username__iexact=email)
            ).first()
            if user:
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=["is_staff", "is_superuser"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Yönetici yapıldı: {user.username} ({user.email})"
                    )
                )
                return

            self.stdout.write(
                self.style.WARNING(
                    f"{email} ile kayıtlı kullanıcı bulunamadı; "
                    "önce siteden kayıt olun veya e-postayı kontrol edin."
                )
            )

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_PASSWORD tanımlı değil; yedek admin hesabı oluşturulmadı."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email or f"{username}@local", "is_staff": True, "is_superuser": True},
        )

        if not created:
            if email:
                user.email = email
            user.is_staff = True
            user.is_superuser = True

        user.set_password(password)
        user.save()

        action = "oluşturuldu" if created else "güncellendi"
        self.stdout.write(
            self.style.SUCCESS(
                f"Yedek yönetici {action}: {username} ({user.email})"
            )
        )
