from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from dailyapp import models

User = get_user_model()


class Command(BaseCommand):
    help = ("Creates a Django User (with a properly HASHED password) for every "
            "existing userlist / Staff row and links them.")

    @transaction.atomic
    def handle(self, *args, **opts):
        made = skipped = 0

        for g in models.userlist.objects.filter(user__isnull=True):
            email = g.email.lower()
            if User.objects.filter(username=email).exists():
                self.stdout.write(self.style.WARNING(f"skip guest {email}: username taken"))
                skipped += 1
                continue
            u = User.objects.create_user(
                username=email, email=email, password=g.password, first_name=g.name)
            g.user = u
            g.password = "!"          # wipe the plaintext copy
            g.save(update_fields=["user", "password"])
            made += 1

        for st in models.Staff.objects.filter(user__isnull=True):
            if User.objects.filter(username=st.username).exists():
                self.stdout.write(self.style.WARNING(f"skip staff {st.username}: username taken"))
                skipped += 1
                continue
            u = User.objects.create_user(
                username=st.username, password=st.password,
                first_name=st.name, is_staff=True)
            st.user = u
            st.password = "!"
            st.save(update_fields=["user", "password"])
            made += 1

        self.stdout.write(self.style.SUCCESS(f"Done. created={made} skipped={skipped}"))