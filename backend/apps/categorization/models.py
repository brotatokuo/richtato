"""Categorization models."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class CategorizationHistory(models.Model):
    """Track categorization decisions for learning and audit purposes."""

    METHOD_CHOICES = [
        ("ai", "AI Categorization"),
        ("keyword", "Keyword-based"),
        ("manual", "Manual"),
        ("suggestion", "AI Suggestion (not applied)"),
    ]

    transaction = models.ForeignKey(
        "transaction.Transaction",
        on_delete=models.CASCADE,
        related_name="categorization_history",
    )
    category = models.ForeignKey(
        "transaction.TransactionCategory",
        on_delete=models.CASCADE,
        related_name="categorization_history",
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confidence score for AI categorization (0-100)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categorization_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction"]),
            models.Index(fields=["method"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.transaction.description} → {self.category.name} ({self.method})"


class CategorizationQueue(models.Model):
    """Queue for batch AI categorization processing."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorization_queues",
    )
    transaction_ids = models.JSONField(
        help_text="List of transaction IDs to categorize"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    batch_size = models.IntegerField(default=75)
    transactions_processed = models.IntegerField(default=0)
    transactions_categorized = models.IntegerField(default=0)
    transactions_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "categorization_queue"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {len(self.transaction_ids)} transactions ({self.status})"

    def mark_processing(self):
        """Mark queue item as currently processing."""
        self.status = "processing"
        self.started_at = timezone.now()
        self.save()

    def mark_completed(self, categorized: int, failed: int, processed: int):
        """Mark queue item as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.transactions_categorized = categorized
        self.transactions_failed = failed
        self.transactions_processed = processed
        self.save()

    def mark_failed(self, error_message: str):
        """Mark queue item as failed."""
        self.status = "failed"
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()

    @property
    def duration(self):
        """Get processing duration."""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
