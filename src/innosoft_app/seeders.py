"""Product-owned seed content for innosoft_app.

Features seed what every product of the line shares; what this website says
about itself lives here. The AboutSeeder below replaces the (empty) seeder of
splent_feature_about.

Content migrated from innosoftdays.com (the "Sobre nosotros" page, Spanish
version, which is this site's primary language).
"""

from splent_framework.seeders.BaseSeeder import BaseSeeder

from splent_io.splent_feature_about.models import AboutSection

QUE_SON = """\
<p>Los InnoSoft Days son unas jornadas anuales organizadas en la Universidad
de Sevilla por los estudiantes del Grado en Ingeniería Informática del
Software. Este evento, que llega a su 13.ª edición, forma parte de la
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
<p>Escríbenos a
<a href="mailto:innosoftdays@gmail.com">innosoftdays@gmail.com</a> o, si lo
prefieres, a través de cualquiera de nuestras redes sociales.</p>
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
