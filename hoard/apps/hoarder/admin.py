from django.contrib import admin

from .models import Category, Header, Hoard


@admin.register(Hoard)
class HoardAdmin(admin.ModelAdmin):
    list_display = ("category", "recorded", "data")


class HeaderInline(admin.TabularInline):
    model = Header
    extra = 0

    readonly_fields = ("key", "value_truc")

    @admin.display(description="Value")
    def value_truc(self, obj):
        if len(obj.value) > 32:
            return obj.value[:12] + "..."
        return "..."


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [HeaderInline]
    prepopulated_fields = {"slug": ("name",)}
