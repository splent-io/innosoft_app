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
        "Three days of talks, workshops and competitions at the ETSII — "
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
    SITE_EVENT = {
        "edition": "XIV",
        "dates": "3–5 Nov 2026",
        "venue": "ETSII · Universidad de Sevilla",
        "iso": "2026-11-03T09:00:00",
    }
    SITE_SPONSORS = [
        "CaixaBank Tech", "NTT Data", "Indra", "Diverso Lab",
        "Universidad de Sevilla", "MCIU · AEI", "Universidad de Málaga", "ETSII",
    ]
    SITE_LOGO = "img/innosoft-logo.png"
    SITE_GALLERY = [
        "img/gallery/photo-2.jpg",
        "img/gallery/photo-10.jpg",
        "img/gallery/photo-14.jpg",
        "img/gallery/photo-18.jpg",
        "img/gallery/photo-23.jpg",
        "img/gallery/photo-26.jpg",
    ]
    SITE_GALLERY_TITLE = "Galería"
    SITE_SPONSORS_TITLE = "Patrocinadores y colaboradores"
    SITE_HERO_ACTIONS = [
        {"label": "Ver eventos", "href": "/events"},
        {"label": "El equipo", "href": "/team", "class": "btn-ghost"},
    ]
    SITE_HIGHLIGHTS_TITLE = "¿Por qué asistir?"
    SITE_HIGHLIGHTS = [
        {"title": "Charlas", "text": "Ponentes de referencia de la industria y la academia."},
        {"title": "Talleres", "text": "Aprende haciendo, con tecnologías punteras."},
        {"title": "Competiciones", "text": "Retos, torneos y premios para todos los niveles."},
        {"title": "Networking", "text": "Conoce a gente con tu misma pasión por el software."},
    ]
    SITE_CTA = {
        "title": "¿Te lo vas a perder?",
        "text": "Tres días de tecnología, aprendizaje y diversión en la ETSII.",
        "button": "Apúntate a InnoSoft Days",
        "href": "/events",
    }

    # i18n (native Flask-Babel support)
    BABEL_DEFAULT_LOCALE = "es"
    BABEL_SUPPORTED_LOCALES = ["es", "en"]

    # Team section/role types and their order — declared per product.
    TEAM_GROUPS = ["Organisers", "Faculty"]


class DevelopmentConfig(_SiteConfig, BaseDev):
    pass


class TestingConfig(_SiteConfig, BaseTest):
    pass


class ProductionConfig(_SiteConfig, BaseProd):
    pass
