#core/models.py
from django.db import models

class BookingSite(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"BookingSite #{self.id}"


class Slot(models.Model):
    booking_site = models.ForeignKey(BookingSite, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time   = models.TimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    court = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_shift = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.date} {self.start_time}-{self.end_time} ({self.court})"
        else:
            return f"{self.date} {self.raw_shift or 'no time'} ({self.court})"



class ParserStatus(models.Model):
    booking_site = models.ForeignKey(BookingSite, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)  
    message = models.TextField(blank=True, null=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True) 

    class Meta:
        verbose_name = "Parser Status"
        verbose_name_plural = "Parser Statuses"    

    def __str__(self):
        site_name = getattr(self.booking_site, "name", "Unknown site")
        return f"{site_name} — {self.status}"
