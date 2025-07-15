from django.utils import timezone

from richtato.apps.richtato_user.models import User


def cleanup_expired_demo_users():
    now = timezone.now()
    expired_users = User.objects.filter(is_demo=True, demo_expires_at__lt=now)
    count = expired_users.count()
    expired_users.delete()
    print(f"Deleted {count} expired demo users.")


if __name__ == "__main__":
    cleanup_expired_demo_users()
