import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

for i in range(10):
    email = f"user{i}@test.com"
    username = f"user{i}"
    password = "test1234"

    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        print(f"Created {email}")
    else:
        print(f"{email} already exists")