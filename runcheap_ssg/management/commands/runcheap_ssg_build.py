import os
import shutil
import logging
import importlib
from textwrap import dedent
from urllib.parse import urlparse
from django.urls import URLPattern, URLResolver, reverse
from django.urls.resolvers import LocalePrefixPattern
from django.utils.translation import activate, get_language
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles.finders import get_finder
from django.template.loader import render_to_string
from django.test import Client

logger = logging.getLogger("django.runcheap_ssg.build_static")

DEFAULT_BUILD_DIR = getattr(
    settings,
    "RUNCHEAP_SSG_BUILD_DIR",
    "_build",
)
DEFAULT_REDIRECT_STYLE = getattr(
    settings,
    "RUNCHEAP_SSG_REDIRECT_STYLE",
    "html { background-color: black; color: white; } a { color: white; }",
)
DEFAULT_REDIRECT_MESSAGE = getattr(
    settings,
    "RUNCHEAP_SSG_REDIRECT_MESSAGE",
    "Redirecting...",
)
DEFAULT_REDIRECT_NOSCRIPT = getattr(
    settings,
    "RUNCHEAP_SSG_REDIRECT_NOSCRIPT",
    "If you are not redirected automatically, follow this link:",
)


def get_static_content(urlpatterns, namespace=tuple(), redirect_context=None, also_handle_nolang=False):
    """
    This function scans a list of urlpatterns and yields rendered pages (or redirects)
    for those url patterns. It only will render pages for url pattern entries that have
    a view that has a .ssg_reverse_iter attribute (which is added by the @included_in_ssg
    decorator). Pages are rendered using Django's built-in testing Client(), so the
    rendered pages and redirect behavior detected is the same as if you were making
    requests while running tests.

    For internationalized url patterns (e.g. /en/about/), a render for each language in
    settings.LANGUAGES is yielded, plus a redirect for the non-internationalized url to
    the settings.LANGUAGE_CODE default language (e.g. /about/ --> /en/about/).

    For urls that have an appended slash and settings.APPEND_SLASH is enabled, a render
    of the page at the appended slash versions is yielded (e.g. /faq/) and a redirect
    for the non-slash version is also yielded (e.g. /faq --> /faq/).

    Redirects are rendered as html pages with a meta http-equiv="refresh" tag and a
    javascript location.href redirect to the desired url.
    """
    for entry in urlpatterns:

        # nested set of views
        if isinstance(entry, URLResolver):
            new_namespace = tuple(n for n in list(namespace) + [entry.namespace] if n)

            # i18n_patterns() views, produce urls for each language
            if isinstance(entry.pattern, LocalePrefixPattern):
                cur_lang = get_language()
                for lang, _ in settings.LANGUAGES:
                    cur_also_handle_nolang = also_handle_nolang
                    if entry.pattern.prefix_default_language and lang == settings.LANGUAGE_CODE:
                        also_handle_nolang = True
                    activate(lang)
                    for content_path, content_iter in get_static_content(
                        entry.url_patterns,
                        namespace=new_namespace,
                        redirect_context=redirect_context,
                        also_handle_nolang=also_handle_nolang,
                    ):
                        yield content_path, content_iter
                    also_handle_nolang = cur_also_handle_nolang
                # reset to language
                activate(cur_lang)
            # include() views
            else:
                for content_path, content_iter in get_static_content(
                    entry.url_patterns,
                    namespace=new_namespace,
                    redirect_context=redirect_context,
                    also_handle_nolang=also_handle_nolang,
                ):
                    yield content_path, content_iter

        # individual view
        elif isinstance(entry, URLPattern):

            # only output pages that have a set of reverse() kwargs as an attribute
            # (which indicates that this page can be generated statically)
            reverse_kwargs_iter = getattr(entry.callback, "ssg_reverse_iter", None)
            if reverse_kwargs_iter is not None:

                # support callable runcheap_ssg_reverse_kwargs attributes
                if callable(reverse_kwargs_iter):
                    reverse_kwargs_iter = reverse_kwargs_iter()

                # generate individual pages for the view (default is just one page per view)
                view_urls = []
                view_name = ":".join(n for n in list(namespace) + [entry.name])

                for reverse_kwargs in reverse_kwargs_iter:
                    page_urls = [reverse(view_name, **reverse_kwargs)]

                    # for language pages where the prefix is always added (i.e. prefix_default_language=True),
                    # also include urls with the prefix removed to capture the redirect
                    if also_handle_nolang:
                        nolang_url = page_urls[0].removeprefix(f"/{settings.LANGUAGE_CODE}") or "/"
                        page_urls.append(nolang_url)

                    # for auto appended slashed pages,
                    # also include urls with the ending slash removed to capture the redirect
                    if settings.APPEND_SLASH and page_urls[0].endswith("/"):
                        for page_url in list(page_urls):
                            noslash_url = page_url[:-1]
                            if noslash_url:
                                page_urls.append(noslash_url)

                    view_urls.extend(page_urls)

                # render the view's set of urls as static content
                for view_url in view_urls:

                    # fake a request to the page
                    resp = Client().get(view_url, follow=False)

                    # render any TemplateResponse views
                    if hasattr(resp, "render"):
                        resp.render()

                    # handle redirects
                    if resp.status_code in {301, 302} and resp.get("Location"):
                        content_iter = [
                            render_to_string(
                                "runcheap_ssg/redirect.html",
                                redirect_context | {"redirect_url": resp["Location"]},
                            ).encode()
                        ]
                    # handle streaming content
                    elif hasattr(resp, "streaming_content"):
                        content_iter = resp.streaming_content
                    # handle fixed content
                    else:
                        content_iter = [resp.content]

                    # handle urls ending with slashes
                    if view_url.endswith("/"):
                        content_path = view_url[:-1] + "/index.html"
                    # handle html pages without a suffix
                    elif (resp.get("Content-Type") or "").startswith("text/html") and not view_url.endswith(
                        (".html", ".htm")
                    ):
                        content_path = view_url + ".html"
                    # default is to just save the content to the view url's path
                    else:
                        content_path = view_url

                    # map the view's content to it's static file
                    yield content_path, content_iter


def build_static_from_urlpatterns(
    output_dir=DEFAULT_BUILD_DIR,
    output_clear=True,
    urlconf=settings.ROOT_URLCONF,
    redirect_style=DEFAULT_REDIRECT_STYLE,
    redirect_message=DEFAULT_REDIRECT_MESSAGE,
    redirect_noscript=DEFAULT_REDIRECT_NOSCRIPT,
    staticfiles_ignore=None,
):
    """
    This is the primary entry point for building the static site.
    With the various kwargs for this function, you can customize
    various build options for the generated static site.
    """

    # clear the existing output directory
    if output_clear:
        folder = os.path.abspath(output_dir)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

    # build the static content
    urlconf_module = importlib.import_module(urlconf)
    content_generator = get_static_content(
        urlconf_module.urlpatterns,
        redirect_context={
            "redirect_style": redirect_style,
            "redirect_message": redirect_message,
            "redirect_noscript": redirect_noscript,
        },
    )

    # save the content to the output directory
    for content_url, content_iter in content_generator:
        logger.info(f"output: {content_url}")
        out_path = os.path.join(folder, content_url[1:])
        out_dir = os.path.dirname(out_path)
        os.makedirs(out_dir, exist_ok=True)
        out_file = open(out_path, "wb")
        for content_chunk in content_iter:
            out_file.write(content_chunk)
        out_file.close()

    # collect any django staticfiles content (if configured to do so)
    if settings.STATIC_URL:
        static_prefix = urlparse(settings.STATIC_URL).path
        static_dir = static_prefix[1:] if static_prefix.startswith("/") else static_prefix
        for finder_import in settings.STATICFILES_FINDERS:
            static_finder = get_finder(finder_import)  # compat: not officially documented in django
            for base_path, storage in static_finder.list(staticfiles_ignore or []):
                # add any prefix (same as django's collectstatic)
                base_path = (storage.prefix + base_path) if getattr(storage, "prefix", None) else base_path
                source_path = storage.path(base_path)
                out_path = os.path.join(folder, static_dir, base_path)
                logger.info(f"output (staticfile): {out_path.split(folder, 1)[1]}")
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                shutil.copy(source_path, out_path)


class Command(BaseCommand):
    """
    Command-line wrapper for the build_static_from_urlpatterns() function.
    """

    help = dedent(
        """\
        Run Cheap Static Site Generator (build command) -
        This command scans the django project's url patterns
        and renders static pages for anything that's marked
        to included in the static site (i.e. wrapped by the
        @include_in_ssg decorator).
    """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            metavar="STRING",
            default=DEFAULT_BUILD_DIR,
            help=f"Where to save the built static site (default is '{DEFAULT_BUILD_DIR}')",
        )
        parser.add_argument(
            "--output-noclear",
            action="store_true",
            help="Don't delete the contents of the output directory before building the static site",
        )
        parser.add_argument(
            "--urlconf",
            metavar="STRING",
            default=settings.ROOT_URLCONF,
            help=f"Location of the root urls.py (default is '{settings.ROOT_URLCONF}')",
        )
        parser.add_argument(
            "--redirect-style",
            metavar="STRING",
            default=DEFAULT_REDIRECT_STYLE,
            help="CSS for redirect pages (default is a black background with white text)",
        )
        parser.add_argument(
            "--redirect-message",
            metavar="STRING",
            default=DEFAULT_REDIRECT_MESSAGE,
            help=f"Text to show while redirecting (default is '{DEFAULT_REDIRECT_MESSAGE}')",
        )
        parser.add_argument(
            "--redirect-noscript",
            metavar="STRING",
            default=DEFAULT_REDIRECT_NOSCRIPT,
            help=f"Text to show on redirects when javascript is disabled (default is '{DEFAULT_REDIRECT_NOSCRIPT}')",
        )
        parser.add_argument(
            "--staticfiles-ignore",
            action="append",
            metavar="STRING",
            default="",
            help=(
                "A glob-stype pattern of what staticfiles to not copy to the build folder"
                "(default is to not ignore any static files, i.e. include everything)"
            ),
        )

    def handle(self, *args, **options):
        build_static_from_urlpatterns(
            output_dir=options["output"],
            output_clear=bool(not options["output_noclear"]),
            urlconf=options["urlconf"],
            redirect_style=options["redirect_style"],
            redirect_message=options["redirect_message"],
            redirect_noscript=options["redirect_noscript"],
            staticfiles_ignore=options["staticfiles_ignore"],
        )
