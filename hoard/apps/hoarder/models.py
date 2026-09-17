import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


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
