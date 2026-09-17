from django import forms, template

register = template.Library()


@register.filter
def is_select(field):
    return isinstance(field.field.widget, forms.Select)
