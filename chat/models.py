import uuid

from django.db import models, transaction
from django.utils import timezone


class Product(models.Model):
    """Catalog the chatbot knows about. Fill it with `manage.py sync_products` or via /admin."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(max_length=120, blank=True, default="General")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    in_stock = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    ROLE_CHOICES = [("user", "User"), ("model", "Assistant")]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class DailyUsage(models.Model):
    """Counts Gemini calls per day so we never exceed the free quota."""

    date = models.DateField(unique=True)
    count = models.PositiveIntegerField(default=0)

    @classmethod
    def take(cls, limit):
        """Reserve one call. Returns False if today's limit is reached."""
        today = timezone.localdate()
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(date=today)
            if obj.count >= limit:
                return False
            obj.count += 1
            obj.save(update_fields=["count"])
            return True

    def __str__(self):
        return f"{self.date}: {self.count}"
