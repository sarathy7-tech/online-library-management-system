from django import template

register = template.Library()


@register.filter
def star_range(rating):
    """
    Turns a 1-5 rating into something you can loop over in a template to
    draw that many star icons:

        {% load book_extras %}
        {% for _ in review.rating|star_range %}<i class="bi bi-star-fill"></i>{% endfor %}
    """
    try:
        return range(int(rating))
    except (TypeError, ValueError):
        return range(0)
