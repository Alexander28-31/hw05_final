from django.utils import timezone as tz


def year(request):
    """Возращает текущий годом."""
    return {
        'year': tz.now().year,
    }
