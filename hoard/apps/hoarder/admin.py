import json

from django.contrib import admin
from django.utils.safestring import SafeString
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

from .models import Category, Header, Hoard


@admin.register(Hoard)
class HoardAdmin(admin.ModelAdmin):
    list_display = (
        "recorded",
        "category",
    )

    readonly_fields = ("pretty_json",)

    @admin.display(description="Data")
    def pretty_json(self, instance):
        """Function to display pretty version of our data"""

        # Convert the data to sorted, indented JSON
        response = json.dumps(
            instance.data, sort_keys=True, indent=2
        )  # <-- your field here

        # Truncate the data. Alter as needed
        response = response[:3_500_000]

        # Get the Pygments formatter
        formatter = HtmlFormatter(style="colorful")

        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)

        # Get the stylesheet
        style = "<style>" + formatter.get_style_defs() + "</style>"

        # Safe the output
        return SafeString(style + response)

    @admin.display(description="Data")
    def data_excerpt(self, obj):
        if len(str(obj.data)) > 127:
            ret = str(obj.data)[:127] + "..."
        else:
            ret = str(obj.data)
        return SafeString("<code>" + ret + "</code>")


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
