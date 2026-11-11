from django.contrib import admin

from .models import Conversation, DailyUsage, Message, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "in_stock", "updated_at")
    list_filter = ("category", "in_stock")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    inlines = [MessageInline]


@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display = ("date", "count")
