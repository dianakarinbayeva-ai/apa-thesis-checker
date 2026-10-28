import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class RuleProfile(models.Model):
    code = models.SlugField(unique=True, default="apa-2024")
    name = models.CharField(max_length=180, default="APA 2024 · № 586")
    source_url = models.URLField(max_length=700)
    version = models.CharField(max_length=80, default="2024-09-13")
    min_pages_one = models.PositiveIntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(300)])
    min_pages_long = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1), MaxValueValidator(300)])
    font_size = models.FloatField(default=14, validators=[MinValueValidator(6), MaxValueValidator(32)])
    margin_left = models.FloatField(default=30, validators=[MinValueValidator(0), MaxValueValidator(80)])
    margin_right = models.FloatField(default=10, validators=[MinValueValidator(0), MaxValueValidator(80)])
    margin_top = models.FloatField(default=20, validators=[MinValueValidator(0), MaxValueValidator(80)])
    margin_bottom = models.FloatField(default=20, validators=[MinValueValidator(0), MaxValueValidator(80)])
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def snapshot(self):
        keys = ("code", "name", "source_url", "version", "min_pages_one", "min_pages_long", "font_size",
                "margin_left", "margin_right", "margin_top", "margin_bottom")
        return {key: getattr(self, key) for key in keys}


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to="documents/%Y/%m/")
    language = models.CharField(max_length=2, choices=settings.LANGUAGES)
    duration = models.CharField(max_length=3, choices=[("1", "1"), ("1.5", "1.5"), ("2", "2")])
    profile = models.JSONField(default=dict)
    status = models.CharField(max_length=12, default="queued", choices=[(s, s) for s in ("queued", "processing", "done", "failed")])
    error_code = models.CharField(max_length=40, blank=True)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]
