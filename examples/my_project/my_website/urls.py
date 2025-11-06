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
