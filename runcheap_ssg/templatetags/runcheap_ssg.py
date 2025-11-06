from django import template
from django.utils import translation
from django.urls import reverse, resolve
from django.conf import settings

register = template.Library()


@register.filter
def runcheap_ssg_language_url(cur_url, lang_code):
    """
    This template filter takes a url and converts it into the equivalent url in another language.
    NOTE: URL parameters are NOT included in the returned url string (e.g. "/en/home?a=1" => "/de/home")

    Example:
        <a href="{{ request.path|runcheap_ssg_language_url:'de' }}">Read this article in German</a>
    """
    view = resolve(cur_url)
    cur_lang = translation.get_language()
    translation.activate(lang_code)
    alt_url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
    translation.activate(cur_lang)
    return alt_url


@register.filter
def runcheap_ssg_alt_languages(cur_url):
    """
    This template filter takes a url and returns a list of language codes for which the url is available,
    other than the current language (e.g. for what other languages is a page translated).

    Example:
        {% for alt_lang in request.path|runcheap_ssg_alt_languages %}
            <li>Translated to {{ alt_lang }}</li>
        {% empty %}
            <li>No other translations available</li>
        {% endfor %}
    """
    alt_languages = []
    view = resolve(cur_url)
    cur_lang = translation.get_language()
    cur_url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
    for lang_code, _ in settings.LANGUAGES:
        translation.activate(lang_code)
        alt_url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
        if alt_url != cur_url:
            alt_languages.append(lang_code)
    translation.activate(cur_lang)
    return alt_languages
