"""Product-owned seed content for innosoft_app.

Features seed what every product of the line shares; what this website says
about itself lives here. Each seeder below replaces the (empty or generic)
seeder of the feature it names, so the feature stays reusable and this
product keeps its own story: who organises the days, which editions have
happened, who sponsors them, what the legal pages say.

Content migrated from innosoftdays.com (Spanish version, this site's primary
language) plus the frozen export under migration/innosoft_export/.
"""

import os
from datetime import date

from splent_framework.seeders.BaseSeeder import BaseSeeder

from splent_io.splent_feature_about.models import AboutSection
from splent_io.splent_feature_editions.models import Edition
from splent_io.splent_feature_editions.services import EditionsService
from splent_io.splent_feature_legal.models import LegalPage
from splent_io.splent_feature_partners.models import Partner
from splent_io.splent_feature_settings.services import SettingsService
from splent_io.splent_feature_team.models import Role, TeamMember

try:
    from splent_io.splent_feature_media.services import MediaService
except ImportError:
    MediaService = None


def _seed_image(filename, title=""):
    """Import a bundled image through the media library and return the item."""
    if MediaService is None:
        return None
    path = os.path.join(os.path.dirname(__file__), "seed_media", filename)
    return MediaService().import_from_file(
        path, title=title, source_key="seed://innosoft_app/" + filename
    )


def _slug(value):
    return EditionsService.slugify(value)


# ── About ──────────────────────────────────────────────────────────────────
QUE_SON = """\
<p>Los InnoSoft Days son unas jornadas anuales organizadas en la Universidad
de Sevilla por los estudiantes del Grado en Ingeniería Informática del
Software. Este evento, que llega a su 14.ª edición, forma parte de la
asignatura Evolución y Gestión de la Configuración, en la que cada estudiante
desempeña un papel fundamental en el éxito de la jornada.</p>

<p>La organización de los InnoSoft Days implica múltiples tareas, desde la
coordinación del evento hasta la gestión de redes sociales, la búsqueda de
patrocinadores y ponentes, y mucho más. InnoSoft Days es, en esencia, un
evento creado por y para estudiantes, que fomenta el desarrollo personal y
profesional a través de experiencias prácticas y de un compromiso firme con
el futuro de la informática y su impacto en el mundo.</p>
"""

UBICACION = """\
<h3>Escuela Técnica Superior de Ingeniería Informática</h3>
<p>Av. Reina Mercedes s/n, 41012 Sevilla</p>
<p><a href="https://maps.google.com/maps?q=Escuela%20T%C3%A9cnica%20Superior%20de%20Ingenier%C3%ADa%20Inform%C3%A1tica%2CAv.%20de%20la%20Reina%20Mercedes%2C%20s%2Fn%2C%2041012%20Sevilla&amp;t=m&amp;z=17">Ver en Google Maps</a></p>
"""

VALORES = """\
<ul>
<li>Colaboración</li>
<li>Innovación</li>
<li>Igualdad</li>
<li>Aprendizaje</li>
<li>Sostenibilidad</li>
<li>Creatividad</li>
</ul>
"""

CONTACTO = """\
<p>Escríbenos desde el <a href="/contact">formulario de contacto</a>, a
<a href="mailto:innosoftdays@gmail.com">innosoftdays@gmail.com</a> o, si lo
prefieres, a través de cualquiera de nuestras redes sociales. Si quieres
proponer una charla, un taller o patrocinar la próxima edición, ese es el
camino.</p>
"""


class AboutSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_about",)

    def run(self):
        sections = [
            ("que-son", "¿Qué son las jornadas InnoSoft Days?", QUE_SON),
            ("donde-estamos", "¿Dónde nos ubicamos?", UBICACION),
            ("valores", "Valores principales", VALORES),
            ("contacto", "¿Cómo contactar?", CONTACTO),
        ]
        self.seed(
            [
                AboutSection(
                    slug=slug,
                    title=title,
                    content=content.strip(),
                    order=i,
                    published=True,
                )
                for i, (slug, title, content) in enumerate(sections, start=1)
            ]
        )


# ── Editions ───────────────────────────────────────────────────────────────
# The XIII edition is the one the old site documented (and whose programme
# the events feature seeds); the XIV is the next one, flagged current so the
# homepage counts down to it. Earlier editions are recovered separately from
# the web archive and added through the admin or a later seed.
XIII_DESCRIPTION = """\
<p>La XIII edición de los InnoSoft Days se celebró del 3 al 6 de noviembre de
2025 en la Escuela Técnica Superior de Ingeniería Informática de la
Universidad de Sevilla, con dos jornadas presenciales (martes 4 y jueves 6) y
una semana de eSports en línea.</p>
<p>Charlas de NTT Data, Indra y CaixaBank Tech, la conferencia de Andreas
Zeller (CISPA), talleres, torneos, escape room, game jam, gymkhana y el reto
sostenible completaron un programa de 23 actividades.</p>
"""

XIV_DESCRIPTION = """\
<p>La XIV edición de los InnoSoft Days se celebrará del 3 al 5 de noviembre
de 2026 en la ETSII de la Universidad de Sevilla. El programa se irá
publicando aquí a medida que se confirmen ponentes y actividades.</p>
"""

EDITIONS = [
    {
        "name": "InnoSoft Days XIII",
        "number": 13,
        "starts_on": date(2025, 11, 3),
        "ends_on": date(2025, 11, 6),
        "venue": "ETSII, Universidad de Sevilla",
        "summary": "Tres días de charlas, talleres y competiciones en la ETSII.",
        "description": XIII_DESCRIPTION,
        "is_current": False,
    },
    {
        "name": "InnoSoft Days XIV",
        "number": 14,
        "starts_on": date(2026, 11, 3),
        "ends_on": date(2026, 11, 5),
        "venue": "ETSII, Universidad de Sevilla",
        "summary": "Tres días de charlas, talleres y competiciones en la ETSII, Universidad de Sevilla.",
        "description": XIV_DESCRIPTION,
        "is_current": True,
    },
]


class EditionsSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_editions",)

    def run(self):
        editions = self.seed(
            [
                Edition(
                    slug=_slug(e["name"]),
                    published=True,
                    order=e["number"],
                    **e,
                )
                for e in EDITIONS
            ]
        )
        # The events feature seeded the XIII programme before this runs; fold
        # every event dated inside an edition into it.
        service = EditionsService()
        for edition in editions:
            service.adopt_events(edition)


# ── Partners ───────────────────────────────────────────────────────────────
# Sponsors and collaborators of the last edition. The old site never showed
# logos, so most start as wordmarks; upload the logo in Media and pick it in
# the partners screen when it arrives. Institutional logos already in the
# workspace ship in seed_media/.
PARTNERS = [
    {"name": "CaixaBank Tech", "link": "https://www.caixabanktech.com/"},
    {"name": "NTT Data", "link": "https://www.nttdata.com/"},
    {"name": "Indra", "link": "https://www.indracompany.com/"},
    {"name": "Diverso Lab", "link": "https://diversolab.us.es/"},
    {
        "name": "Universidad de Sevilla",
        "link": "https://www.us.es/",
        "logo": "universidad-de-sevilla.jpg",
    },
    {
        "name": "ETSII",
        "link": "https://www.informatica.us.es/",
    },
    {
        "name": "Ministerio de Ciencia, Innovación y Universidades",
        "link": "https://www.ciencia.gob.es/",
        "logo": "ministerio-de-ciencia-innovacion-y-universidades.jpg",
    },
    {
        "name": "Universidad de Málaga",
        "link": "https://www.uma.es/",
        "logo": "universidad-de-malaga.jpg",
    },
]


class PartnersSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_partners",)

    def run(self):
        data = []
        for order, p in enumerate(PARTNERS, start=1):
            media = _seed_image(p["logo"], title=p["name"]) if p.get("logo") else None
            data.append(
                Partner(
                    media_id=media.id if media else None,
                    name=p["name"],
                    link=p.get("link", ""),
                    order=order,
                    active=True,
                )
            )
        self.seed(data)


# ── Team ───────────────────────────────────────────────────────────────────
# The organisers are the students of the course, a group that changes every
# year and adds itself through the admin; the role exists from day one. The
# speakers of the XIII edition come from the migrated programme, so an event
# whose speaker matches a member links to the profile.
ROLES = ["Organización", "Ponentes"]

SPEAKERS = [
    {"name": "Manuel Carranza"},
    {"name": "José Carlos Moral Cuevas", "affiliation": "NTT Data"},
    {"name": "Pablo Reina Jiménez", "affiliation": "Universidad de Sevilla"},
    {"name": "Pedro Almagro Blanco", "affiliation": "Universidad de Sevilla"},
    {"name": "Jorge Martos", "affiliation": "Indra"},
    {"name": "Pablo Dávila Herrero"},
    {
        "name": "Andreas Zeller",
        "affiliation": "CISPA Helmholtz Center / Saarland University",
        "link": "https://andreas-zeller.info/",
    },
    {"name": "Mario Jiménez Calderón", "affiliation": "CaixaBank Tech"},
    {"name": "Rebeca Sarai González Guerra"},
]


class TeamSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_team",)

    def run(self):
        roles = self.seed(
            [
                Role(name=name, slug=_slug(name), order=i)
                for i, name in enumerate(ROLES, start=1)
            ]
        )
        speakers_role = roles[1]
        members = []
        for order, s in enumerate(SPEAKERS, start=1):
            member = TeamMember(
                name=s["name"],
                slug=_slug(s["name"]),
                affiliation=s.get("affiliation", ""),
                link=s.get("link", ""),
                order=order,
                published=True,
            )
            member.roles.append(speakers_role)
            members.append(member)
        self.seed(members)


# ── Legal ──────────────────────────────────────────────────────────────────
PRIVACY = """\
<p><strong>Información básica sobre protección de datos</strong></p>
<ul>
<li><strong>Responsable.</strong> La organización de los InnoSoft Days,
jornadas de la asignatura Evolución y Gestión de la Configuración del Grado
en Ingeniería Informática del Software, Universidad de Sevilla.</li>
<li><strong>Finalidad.</strong> Atender las consultas enviadas desde el
formulario de contacto, gestionar la participación de ponentes y
patrocinadores, y difundir las jornadas mediante fotografías y vídeos de las
actividades.</li>
<li><strong>Legitimación.</strong> El consentimiento que prestas al escribir
a través del formulario o al participar en las actividades, y el interés
legítimo en difundir un evento universitario público.</li>
<li><strong>Destinatarios.</strong> Los datos no se ceden a terceros salvo
obligación legal. Las fotografías de las actividades pueden publicarse en
esta web y en las redes sociales del evento.</li>
<li><strong>Derechos.</strong> Puedes acceder, rectificar y suprimir tus
datos, así como retirar tu imagen de la galería, escribiendo a
<a href="mailto:innosoftdays@gmail.com">innosoftdays@gmail.com</a>.</li>
<li><strong>Información adicional.</strong> La política de protección de
datos de la Universidad de Sevilla está disponible en
<a href="https://www.us.es/proteccion-datos">https://www.us.es/proteccion-datos</a>.</li>
</ul>
"""

COOKIES = """\
<p>Esta web utiliza únicamente cookies técnicas, necesarias para mantener la
sesión de quienes administran el contenido y para proteger el formulario de
contacto frente al envío automatizado. No se emplean cookies de análisis ni
de publicidad, y no se cede información de navegación a terceros.</p>
<p>Puedes bloquear o eliminar las cookies desde la configuración de tu
navegador; la parte pública de la web sigue funcionando sin ellas.</p>
"""

LEGAL_PAGES = [
    {
        "slug": "politica-de-privacidad",
        "title": "Política de privacidad",
        "content": PRIVACY,
    },
    {"slug": "politica-de-cookies", "title": "Política de cookies", "content": COOKIES},
]


class LegalSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_legal",)

    def run(self):
        self.seed(
            [
                LegalPage(
                    slug=p["slug"],
                    title=p["title"],
                    content=p["content"].strip(),
                    published=True,
                )
                for p in LEGAL_PAGES
            ]
        )


# ── Settings ───────────────────────────────────────────────────────────────
# Panel values that are editorial for this product and have no environment
# fallback in their feature. Administrators can change them afterwards in
# the settings panel; the seed only gives the site a sensible first state.
SETTINGS = {
    "partners_title": "Patrocinadores y colaboradores",
    "partners_grayscale": "0",
    "contact_recipient": "innosoftdays@gmail.com",
    "contact_success_message": "Gracias, te responderemos lo antes posible.",
}


class SettingsSeeder(BaseSeeder):
    def run(self):
        SettingsService().set_many(SETTINGS)


# ── Survey (feedback questionnaire) ─────────────────────────────────────────
# The satisfaction questionnaire InnoSoft Days has always run, rebuilt as a
# native survey from the frozen export (migration/innosoft_export/feedback.json,
# the Spanish Forminator form). 22 Likert 0-5 questions in five sections plus
# five open questions.
import json as _json  # noqa: E402

from splent_io.splent_feature_survey.models import (  # noqa: E402
    Survey,
    SurveyQuestion,
)

_FEEDBACK = os.path.join(
    os.path.dirname(__file__), "..", "..", "migration", "innosoft_export", "feedback.json"
)


class SurveySeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_survey",)

    def run(self):
        try:
            data = _json.load(open(_FEEDBACK, encoding="utf-8"))
        except OSError:
            return
        page = data.get("pages", {}).get("es", {})
        survey = Survey(
            title="Cuestionario de calidad",
            slug="cuestionario-de-calidad",
            intro="<p>" + page.get("intro", "Cuéntanos sobre tu experiencia en los InnoSoft Days.") + "</p>",
            thank_you="<p>Gracias por tu opinión. Nos ayuda a mejorar cada edición.</p>",
            published=True,
        )
        self.seed([survey])
        questions = []
        for i, q in enumerate(data.get("questions_es", []), start=1):
            if q.get("type") == "likert_0_5":
                qtype, options = "scale", {"min": 0, "max": 5, "min_label": "Nada de acuerdo", "max_label": "Muy de acuerdo"}
            else:
                qtype, options = "textarea", {}
            questions.append(
                SurveyQuestion(
                    survey_id=survey.id,
                    section=q.get("group", ""),
                    prompt=q.get("question", ""),
                    type=qtype,
                    required=bool(q.get("required")),
                    options=options,
                    order=i,
                )
            )
        self.seed(questions)
