import uuid

import sentry_sdk
from django.db import models
from django.utils.module_loading import import_string


class Category(models.Model):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    preprocessors = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Dotted paths of functions applied to the payload before storage. "
            "Each function takes a dict and returns a dict."
        ),
    )

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name

    def preprocess(self, data: dict) -> dict:
        # A failing preprocessor is skipped (logged to Sentry) and the
        # pipeline continues with the input dict unchanged.
        for path in self.preprocessors:
            try:
                result = import_string(path)(data)
                if not isinstance(result, dict):
                    raise TypeError(
                        f"{path} returned {type(result).__name__}, expected dict"
                    )
            except Exception:  # noqa: BLE001 - preprocessor failures must not break intake
                sentry_sdk.capture_exception()
                continue
            data = result
        return data


class Header(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="headers"
    )
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=255, editable=False)

    def __str__(self) -> str:
        return f"{self.category.name}: {self.key}"


class Hoard(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, db_index=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="hoards"
    )
    recorded = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, editable=False)

    def __str__(self) -> str:
        return f"{self.category.name}: {str(self.data)[:100]}..."
