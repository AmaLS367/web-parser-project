# core/admin.py
from django.contrib import admin
from .models import BookingSite, Slot, ParserStatus

@admin.register(BookingSite)
class BookingSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'url')

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('booking_site', 'date', 'start_time', 'end_time', 'raw_shift', 'is_available', 'price', 'court', 'updated_at')
    list_filter = ('booking_site', 'is_available', 'date')
    search_fields = ('court', 'raw_shift')
    date_hierarchy = 'date'

@admin.register(ParserStatus)
class ParserStatusAdmin(admin.ModelAdmin):
    list_display = ('booking_site', 'status', 'checked_at', 'duration')
    list_filter = ('status', 'booking_site')
    search_fields = ('message',)
    date_hierarchy = 'checked_at'

# Оптимизация Django admin для Celery Beat PeriodicTask
try:
    from django_celery_beat.models import PeriodicTask
    from django_celery_beat.admin import PeriodicTaskAdmin as BeatPeriodicTaskAdmin

    # Перерегистрируем PeriodicTask с ограничением выборки
    admin.site.unregister(PeriodicTask)

    @admin.register(PeriodicTask)
    class CustomPeriodicTaskAdmin(BeatPeriodicTaskAdmin):
        list_display = ('name', 'task', 'enabled', 'last_run_at')
        search_fields = ('name', 'task')
        list_select_related = True
        list_per_page = 20
except Exception:
    pass

