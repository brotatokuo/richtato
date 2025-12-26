"""Management command to initialize keywords for existing categories."""

from apps.richtato_user.models import User
from apps.transaction.models import CategoryKeyword, TransactionCategory
from apps.transaction.services.category_initialization_service import (
    CategoryInitializationService,
)
from django.core.management.base import BaseCommand
from django.db import transaction
from loguru import logger


class Command(BaseCommand):
    help = "Initialize keywords for existing categories from defaults config"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Initialize keywords for a specific user ID",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-initialization even if keywords already exist",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        force = options.get("force", False)

        if user_id:
            users = User.objects.filter(id=user_id)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
                return
        else:
            users = User.objects.all()

        service = CategoryInitializationService()
        config = service.load_defaults_config()

        # Build a mapping of category names to their keywords
        keyword_map = {}
        for cat_config in config.get("categories", []):
            name = cat_config.get("name")
            keywords = cat_config.get("keywords", [])
            if name and keywords:
                keyword_map[name.lower()] = [str(kw).strip().lower() for kw in keywords]

        total_users = 0
        total_keywords = 0

        for user in users:
            user_keywords_created = 0

            # Get all categories for this user
            categories = TransactionCategory.objects.filter(user=user)

            for category in categories:
                # Check if this category already has keywords
                existing_count = CategoryKeyword.objects.filter(
                    user=user, category=category
                ).count()

                if existing_count > 0 and not force:
                    self.stdout.write(
                        f"  Skipping {category.name} - already has {existing_count} keywords"
                    )
                    continue

                # Get keywords from config
                keywords_to_add = keyword_map.get(category.name.lower(), [])
                if not keywords_to_add:
                    continue

                # If force, delete existing keywords first
                if force and existing_count > 0:
                    CategoryKeyword.objects.filter(
                        user=user, category=category
                    ).delete()
                    self.stdout.write(
                        f"  Deleted {existing_count} existing keywords for {category.name}"
                    )

                # Add keywords
                with transaction.atomic():
                    for keyword in keywords_to_add:
                        if not keyword:
                            continue

                        try:
                            CategoryKeyword.objects.get_or_create(
                                user=user,
                                category=category,
                                keyword=keyword,
                            )
                            user_keywords_created += 1
                        except Exception as e:
                            logger.debug(
                                f"Skipping duplicate keyword '{keyword}' for {category.name}: {str(e)}"
                            )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Added {len(keywords_to_add)} keywords to {category.name}"
                    )
                )

            if user_keywords_created > 0:
                total_users += 1
                total_keywords += user_keywords_created
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Initialized {user_keywords_created} keywords for user {user.username} (ID: {user.id})"
                    )
                )
            else:
                self.stdout.write(
                    f"No keywords needed for user {user.username} (ID: {user.id})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Initialized {total_keywords} keywords for {total_users} users"
            )
        )
