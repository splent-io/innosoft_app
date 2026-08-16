"""
Configuration for innosoft_app.

Each class extends the framework's base configuration. Only override
what your product needs — everything else is inherited automatically.

Hierarchy (later layers win):
  1. Framework defaults (Config base class)
  2. This file (product config)
  3. Feature inject_config() calls
"""

from splent_framework.configuration.default_config import (
    DevelopmentConfig as BaseDev,
    TestingConfig as BaseTest,
    ProductionConfig as BaseProd,
)


class _SiteConfig:
    """Site-level configuration — consumed by the theme (header, footer, SEO).

    This is what makes the product *its own website* rather than a generic
    SPLENT app: the brand name, tagline, navigation and social links live here,
    at the product level, not hardcoded in any feature.
    """

    SITE_NAME = "InnoSoft Days"
    SITE_TAGLINE = (
        "Tres días de charlas, talleres y competiciones en la ETSII, "
        "Universidad de Sevilla."
    )
    # No SITE_NAV: the main navigation is composed from the INSTALLED features
    # (each declares its entry via register_nav_item) and tuned in the admin
    # Menus editor. The theme keeps SITE_NAV support only as a zero-feature
    # fallback, which this product never hits.
    SITE_SOCIAL = [
        {"network": "Instagram", "href": "https://www.instagram.com/innosoftdays/"},
        {"network": "X", "href": "https://x.com/innosoftdays"},
        {"network": "YouTube", "href": "https://www.youtube.com/@innosoftdays"},
        {"network": "Twitch", "href": "https://www.twitch.tv/innosoftdays"},
        {"network": "LinkedIn", "href": "https://www.linkedin.com/company/innosoft-days/"},
    ]
    SITE_LOGO = "img/innosoft-logo.png"
    # The headline moment (edition, dates, venue, countdown, registration)
    # is content, not config: the editions feature owns the homepage hero
    # from the edition flagged as current in the admin. Likewise sponsors
    # (partners feature) and the photo strip (media feature). What stays
    # here is brand copy that does not change from one edition to the next.
    SITE_HERO_ACTIONS = [
        {"label": "Quiénes somos", "href": "/about", "class": "btn-ghost"},
    ]
    SITE_HIGHLIGHTS_TITLE = "¿Por qué asistir?"
    SITE_HIGHLIGHTS = [
        {"title": "Charlas", "text": "Ponentes de referencia de la industria y la academia."},
        {"title": "Talleres", "text": "Aprende haciendo, con tecnologías punteras."},
        {"title": "Competiciones", "text": "Retos, torneos y premios para todos los niveles."},
        {"title": "Networking", "text": "Conoce a gente con tu misma pasión por el software."},
    ]
    SITE_CTA = {
        "title": "¿Quieres participar?",
        "text": "Propón una charla o un taller, patrocina la próxima edición o simplemente cuéntanos qué te gustaría ver.",
        "button": "Escríbenos",
        "href": "/contact",
    }

    # i18n: the language is product configuration read from the environment
    # (BABEL_DEFAULT_LOCALE / BABEL_SUPPORTED_LOCALES in [tool.splent.config]
    # of pyproject.toml), so it is not repeated here.



class DevelopmentConfig(_SiteConfig, BaseDev):
    pass


class TestingConfig(_SiteConfig, BaseTest):
    pass


class ProductionConfig(_SiteConfig, BaseProd):
    pass
