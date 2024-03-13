from django import template

from historical_currencies.choices import currency_choices

register = template.Library()


@register.simple_tag
def currency_choices_list(exclude_special=True):
    """Return a list of tuples (code, name), for rendering form fields."""
    return currency_choices(exclude_special=exclude_special)


@register.inclusion_tag("historical_currencies/currency_choices_options.html")
def currency_choices_options(exclude_special=True, selected=None):
    """Return a rendered set of <option> tags."""
    return {
        "currency_choices": currency_choices(exclude_special=exclude_special),
        "selected": selected,
    }
