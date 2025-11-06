# Run Cheap Static Site Generator (SSG)

This is a barebones django "app" (i.e. plugin) that you can use to generate static sites from your django views and templates.

I wrote this as an alternative to Jekyll for folks who are more used to using Django's template system. 

## How to use

First, install the django app (the only dependency is `django`). 

```bash
python3 -m pip install runcheap-ssg
```

Next, add `runcheap_ssg` to your `INSTALLED_APPS` list in your `settings.py`.
This enables management commands for building the static site and some helpful template filters.

```python3
INSTALLED_APPS = [
    ...
    "runcheap_ssg",
]
```

Next, update the views in your `urls.py` to use `include_in_ssg`.

```python3
from django.urls import path, re_path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import TemplateView
from runcheap_ssg.decorators import include_in_ssg
from my_website.views import landing_view, BlogEntryView, favicon_view, robots_view

# works with translated pages
i18n_urlpatterns = i18n_patterns(
    # works with simple views and default paths
    path("", include_in_ssg(landing_view), name="landing"),
    # works with class-based views and regex paths
    re_path(r"^about/$", include_in_ssg(TemplateView.as_view(template_name="about.html")), name="about"),
    # works with url parameters
    # (set parameters for each page to generate with `ssg_reverse_iter` kwarg)
    path(
        "blog/",
        include_in_ssg(
            TemplateView.as_view(template_name="about.html", extra_context={"entries": BlogEntryView.entries})
        ),
        name="blog_list",
    ),
    path(
        "blog/<slug:slug>/",
        include_in_ssg(
            BlogEntryView.as_view(),
            # generates one page per entry (i.e. `reverse("blog_entry", kwargs={"slug": "..."})`)
            ssg_reverse_iter=[{"kwargs": {"slug": entry["slug"]}} for entry in BlogEntryView.entries],
        ),
        name="blog_entry",
    ),
)

# works other types of pages
urlpatterns = i18n_urlpatterns + [
    # works with non-internationalized pages
    path("non-i18n/", include_in_ssg(TemplateView.as_view(template_name="non-i18n.html")), name="non-i18n"),
    # works with non-html files
    path("favicon.ico", include_in_ssg(favicon_view), name="favicon_ico"),
    # works with views that use @include_in_ssg decorator (so don't have to use it in the urls.py)
    path("robots.txt", robots_view, name="robots_txt"),
    # this view isn't wrapped by include_in_ssg(), so won't be included in the static build
    path("not-included/", TemplateView.as_view(template_name="not_included.html"), name="not_included"),
]
```

You can also use `@include_in_ssg` as a decorator in your views.

```python3
# ...in your myapp/views.py
from runcheap_ssg.decorators import include_in_ssg
...
@include_in_ssg
def robots_view(request):
    return FileResponse(open(finders.find("robots.txt"), "rb"))
```

Finally, you can generate your site as a set of static files using the built-in command
(views that don't inherit from `StaticTemplateView` or `StaticFileView` are ignored).

```bash
python3 manage.py runcheap_ssg_build --output "_build"
```

Your static site is now rendered in `./_build/`! Hooray!

Additionally, if you want to test your static site, there's a built-in server.

```bash
python3 manage.py runcheap_ssg_serve
```

## Examples

Check out the [examples](https://github.com/runcheap/runcheap-ssg/tree/main/examples/)
folder of this repository to see example django projects that use Run Cheap SSG.
