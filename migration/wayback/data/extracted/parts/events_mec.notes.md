# events_mec

Single event pages of the Modern Events Calendar plugin (`/events/<slug>/`, class `mec-single-event`) and the `/events/` index captures. The Astra-era MEC template renders no date/time/location/organizer blocks, so every field comes from the schema.org JSON-LD block (dates, location.name, organizer) and from the Google Calendar export link (`dates=YYYYMMDDTHHMMSSZ/...`, which MEC builds from the local time under WordPress' UTC PHP timezone, so the values are the naive Europe/Madrid times; verified against the 2020 institucional capture that still renders `Hora 20:30 - 21:30`).

## Coverage

- Event captures in scope: 218 (156 distinct URLs); event-index captures: 6 (3 URLs).
- Events extracted: 155 (one per URL, latest capture). Every other capture of the same URL was extracted too and compared field by field (title, dates, room, speaker, company, summary, poster, link, description text): 0 differences found, so the older captures carry the same event.
- Skipped event URLs: 1. Speakers: 108. Editions: 8. Media: 15.
- The event pages are not limited to 2023/2024: the MEC calendar held the whole history from 2017 (edition V) to 2024 (edition XII).

## Per year

- 2017 (edition V): 13 events, 2017-11-06 to 2017-11-09, kinds {'other': 1, 'talk': 10, 'workshop': 2}
- 2018 (edition VI): 21 events, 2018-11-12 to 2018-11-16, kinds {'competition': 1, 'other': 1, 'talk': 18, 'workshop': 1}
- 2019 (edition VII): 17 events, 2019-11-04 to 2019-11-06, kinds {'ceremony': 2, 'other': 1, 'talk': 11, 'workshop': 3}
- 2020 (edition VIII): 18 events, 2020-11-24 to 2020-11-27, kinds {'ceremony': 2, 'competition': 1, 'other': 1, 'talk': 13, 'workshop': 1}
- 2021 (edition IX): 33 events, 2021-11-08 to 2021-11-17, kinds {'ceremony': 2, 'competition': 3, 'social': 2, 'talk': 26}
- 2022 (edition X): 29 events, 2022-11-08 to 2022-11-11, kinds {'ceremony': 2, 'competition': 3, 'other': 2, 'social': 3, 'talk': 19}
- 2023 (edition XI): 17 events, 2023-11-06 to 2023-11-09, kinds {'ceremony': 1, 'competition': 5, 'stand': 2, 'talk': 8, 'workshop': 1}
- 2024 (edition XII): 7 events, 2024-11-06 to 2024-11-07, kinds {'talk': 7}

## Field rules

- `starts_at`/`ends_at`: Google Calendar link; JSON-LD `startDate` as fallback (date only). Ends earlier than the start: 00:xx ends on the same day are read as 12:xx (AM/PM slip in the MEC form), otherwise `ends_at` is null (listed under Oddities).
- `room`: JSON-LD `location.name` verbatim (Aula A1.16, A3.10, Salón de Grados, Twitch Innosoft, `A0.11 Online`...). `modality` is `online` only when the location is a streaming channel (Twitch, 2020); the two 2021 rooms tagged `Online` are hybrid and stay `in_person` with the tag kept in `room`. Events without a location inherit `online` when every located event of their year is online (the 2020 umbrella entry).
- `speaker`/`company`: MEC `organizer.name` (used as speaker in 2017 to 2021; organisation names such as Abatic, atSistemas, Mujeres Tech, Dolbuck SL, Viafirma, Ayesa, OnRetrieval, GUMUS, Ping a Programadoras go to `company`; `Name (Company)`, `Name + Company` and `Name - Position` are split). 2022 titles `Charla de la Sra./del Sr. X` give the speaker and `Charla de <Empresa>` the company, with the speaker taken from the linked post title `Información sobre la ponencia del Sr. X`; 2024 titles `Charla <tema> – <nombre> (<empresa>)` give both. A small curated table (`SPEAKER_HINTS`, mostly 2023) covers speakers only mentioned in the prose. Placeholder `Organizer Name` and `InnoSoft` are ignored.
- `description_html`: `mec-single-event-description` cleaned; removed the WordPress oEmbed iframes of the site's own posts (the link stays), the `logo-innosoft` placeholder images, the 2021 ticketing boilerplate (Entradas / Aviso / Recuerda llevar las entradas...) and bare Eventbrite URLs, which move to `link`. Hourly-schedule and countdown boxes are noise and are not extracted.
- `link`: the Eventbrite ticket URL when the description has one (2021, 2024), otherwise the first link to the site itself (2022 events link their `Información sobre la ponencia...` post, Brawlhalla its news post).
- `poster_url`: featured image (`mec-events-event-image`, lazy `data-src`) or `og:image`, ignoring the site logo. Only the 2020 events had real posters.
- `kind`: from the title (taller -> workshop; torneo/CTF/gymkhana/hackatón/escape room -> competition; stand -> stand; acto/ceremonia/inauguración/presentación del día/charla de apertura or clausura -> ceremony; barrilada/quedada musical/música/grupo -> social; umbrella entries `Innosoft Days 2020`, `Innosoft Days día 3/4` and screenings -> other; everything else -> talk).
- `lang`: `en` when the title/description read as English by a stopword count, otherwise `es` (site locale es-ES). Titles are kept verbatim, including the ALL CAPS ones of 2019.
- Speakers: one entry per person name found in `speaker` (split on commas and ` y `), affiliation from `company`, position from `Name - Position` organizers, links from `organizer.url` (LinkedIn/Web, 2020 events). No photos or bios exist in the MEC pages. Names are kept as written, so `Clara Grima` (2018) and `Clara Grima Ruiz` (2022), or `Maria José Escalona`, are left for the importer's dedupe.
- Editions: one per year found, dates min/max of the events, venue ETSII (Online (Twitch) for 2020, whose events all ran on Twitch), confidence medium (low when fewer than 10 events, i.e. 2024 with 7 events on 6-7 November).

## Event-index captures

- https://www.innosoftdays.com/en/events/ capture 20241110152805: skipped, no MEC markup and no event list (menu-only page).
- https://www.innosoftdays.com/en/events/ capture 20250213192655: skipped, no MEC markup and no event list (menu-only page).
- https://www.innosoftdays.com/es/eventos/ capture 20251109045925: skipped, 2025 Elementor/Blocksy site listing the XIII edition (Andreas Zeller...), not MEC; belongs to the 2025 family.
- https://www.innosoftdays.com/es/eventos/ capture 20260217185745: skipped, 2025 Elementor/Blocksy site listing the XIII edition (Andreas Zeller...), not MEC; belongs to the 2025 family.
- https://www.innosoftdays.com/events/ capture 20240616205939: skipped, MEC calendar shortcode rendering `¡No hay eventos!` (only future events are listed and none existed); nothing to extract.
- https://www.innosoftdays.com/events/ capture 20241212034646: skipped, The Events Calendar (tribe) month view for December 2024 (three `Seminario Futuro` entries); belongs to the tribe /event/ family, not MEC.

## Skipped event captures

- https://institucional.us.es/innosoft/events/hacia-una-inteligencia-artificial-regenerativa-y-redistributiva/ capture 20201127061643 (also 20201123040053, same content): same title and start as https://www.innosoftdays.com/events/hacia-una-inteligencia-artificial-regenerativa-y-redistributiva/ (mirror of the same event)

## Version differences

- none

## Oddities

- https://www.innosoftdays.com/events/acto-de-apertura/ (20250213200309): end time 00:30 read as 12:30 (AM/PM slip)
- https://www.innosoftdays.com/events/mesa-redonda-el-impacto-de-la-ingenieria-del-software-en-la-industria-local/ (20250122215701): end time 00:40 read as 12:40 (AM/PM slip)
- Slugs and titles drifted: `dia-dos-innosoft-days-2` is titled `Innosoft Days día 3`, `innosoft-days-dia-3` is `día 4`, `conferencia-los-estudios-ingenieria-software-pasado-presente-futuro-2` is `La informática en el descubrimiento del escutoide` (Clara Grima), `-2-2` is `Mujeres en ingeniería`, `tema-a-especificar` is `Ciberseguridad, ¿qué esperan los alumnos...`, `de-devops-a-devsecpos` is `Seguridad cloud-native`, `secureit` is `Ciberseguridad: Retos y necesidades`. Titles win.
- Two 2022 talk pages point at the same company from different angles (`charla-del-sr-fernando-fernandez-mancera` and `redhat` are both `Charla de Red Hat`, on different days); both kept.
- Umbrella entries kept as kind `other`: `Innosoft Days 2020` (24-27 Nov, whole edition), `Innosoft Days día 3` and `día 4` (2022, 08:00-18:00 day markers).
- 2022 events have no room and no organizer in MEC; the linked `Información sobre la ponencia...` posts (family posts_2022) hold the speaker bios.
- The institucional.us.es capture of `hacia-una-inteligencia-artificial-regenerativa-y-redistributiva` is the same event as the innosoftdays.com URL (same title and start); the innosoftdays.com one is kept and the institucional one is listed as skipped. Its poster URL is the institucional host, mapped to www.innosoftdays.com by norm_media_url.

## Events extracted (start, title, capture used, other captures)

- 2017-11-06T08:30:00 [2017] Conferencia – Proyecto de Smart Cities del Ayuntamiento de Sevilla. <https://www.innosoftdays.com/events/conferencia-proyecto-smart-cities-del-ayuntamiento-sevilla/> capture 20241106213701
- 2017-11-06T09:30:00 [2017] Conferencia – Gestión de la seguridad dentro de las organizaciones. Normativa de seguridad de la Universidad de Sevilla. <https://www.innosoftdays.com/events/conferencia-gestion-de-la-seguridad-dentro-de-las-organizaciones-normativa-de-seguridad-de-la-universidad-de-sevilla/> capture 20250214051806 (also 20241108151926)
- 2017-11-06T12:45:00 [2017] Conferencia – Impresión 3D de órganos y la creación de algoritmos para dichas impresiones. <https://www.innosoftdays.com/events/conferencia-impresion-3d-de-organos-y-la-creacion-de-algoritmos-para-dichas-impresiones/> capture 20241110144914
- 2017-11-06T12:45:00 [2017] Taller – Sistemas operativos de los robots: librerías, software y herramientas de ayuda para construir una aplicación robot. <https://www.innosoftdays.com/events/taller-sistemas-operativos-de-los-robots-librerias-software-y-herramientas-de-ayuda-para-construir-una-aplicacion-robot/> capture 20250209143847
- 2017-11-06T13:40:00 [2017] Conferencia – Deep learning. <https://www.innosoftdays.com/events/conferencia-deep-learning/> capture 20241110161423
- 2017-11-06T15:30:00 [2017] Conferencia – El papel y la inclusión de la mujer en la tecnología. <https://www.innosoftdays.com/events/conferencia-el-papel-y-la-inclusion-de-la-mujer-en-la-tecnologia/> capture 20250214152830 (also 20241110162327)
- 2017-11-06T16:00:00 [2017] Conferencia – Cómo nace y se desarrolla una start-up tecnológica. También hablarán sobre su aplicación de modelado 3D. <https://www.innosoftdays.com/events/conferencia-como-nace-y-se-desarrolla-una-start-up-tecnologica-tambien-hablaran-sobre-su-aplicacion-de-modelado-3d/> capture 20250209153424 (also 20241110163126)
- 2017-11-06T16:50:00 [2017] Taller – Desarrollo Ágil de software, envuelve un enfoque para la toma de decisiones en los proyectos de software. <https://www.innosoftdays.com/events/taller-desarrollo-agil-de-software-envuelve-un-enfoque-para-la-toma-de-decisiones-en-los-proyectos-de-software/> capture 20250213180323
- 2017-11-09T11:30:00 [2017] Conferencia – Proyección de hologramas sobre tejido semitransparente. Concierto de Vocaloid. <https://www.innosoftdays.com/events/conferencia-proyeccion-de-hologramas-sobre-tejido-semitransparente-concierto-de-vocaloid/> capture 20250213184542
- 2017-11-09T16:15:00 [2017] Conferencia – Machine learning: rama de la inteligencia artificial cuyo objetivo es desarrollar técnicas que permitan a las computadoras aprender. <https://www.innosoftdays.com/events/conferencia-machine-learning-rama-de-la-inteligencia-artificial-cuyo-objetivo-es-desarrollar-tecnicas-que-permitan-a-las-computadoras-aprender/> capture 20250122222545
- 2017-11-09T17:30:00 [2017] Conferencia – «Guifi.Net», una red de telecomunicaciones abierta, libre y neutral. <https://www.innosoftdays.com/events/conferencia-guifi-net-una-red-de-telecomunicaciones-abierta-libre-y-neutral/> capture 20241110141333
- 2017-11-09T18:00:00 [2017] Conferencia – Drones, lo que se puede hacer ahora mismo con ellos y tendencias futuras. <https://www.innosoftdays.com/events/conferencia-drones-lo-que-se-puede-hacer-ahora-mismo-con-ellos-y-tendencias-futuras/> capture 20250209151820 (also 20241110161155)
- 2017-11-09T18:40:00 [2017] Conferencia – “OSINT. Qué sabe Internet sobre ti”. <https://www.innosoftdays.com/events/conferencia-osint-que-sabe-internet-sobre-ti/> capture 20250122221520
- 2018-11-12T19:30:00 [2018] Conferencia – Los estudios de Ingeniería de Software: pasado presente y futuro <https://www.innosoftdays.com/events/conferencia-los-estudios-ingenieria-software-pasado-presente-futuro/> capture 20250122222828
- 2018-11-12T20:30:00 [2018] Conferencia – La informática en el descubrimiento del escutoide <https://www.innosoftdays.com/events/conferencia-los-estudios-ingenieria-software-pasado-presente-futuro-2/> capture 20241106210651
- 2018-11-12T20:30:00 [2018] Conferencia – Mujeres en ingeniería <https://www.innosoftdays.com/events/conferencia-los-estudios-ingenieria-software-pasado-presente-futuro-2-2/> capture 20250213182114
- 2018-11-13T08:40:00 [2018] Proyección – Capítulo “Toda tu historia” de Black Mirror y tertulia <https://www.innosoftdays.com/events/proyeccion-capitulo-toda-tu-historia-de-black-mirror-y-tertulia/> capture 20241110141659
- 2018-11-13T08:40:00 [2018] Testing de aplicaciones en Kubernetes <https://www.innosoftdays.com/events/testing-de-aplicaciones-en-kubernetes/> capture 20250213192532
- 2018-11-13T10:40:00 [2018] Conferencia – Frontend también es diseño <https://www.innosoftdays.com/events/conferencia-frontend-tambien-es-diseno/> capture 20241110162138
- 2018-11-13T10:40:00 [2018] Conferencia – Wide Wild West 2.0 <https://www.innosoftdays.com/events/conferencia-wide-wild-west-2-0/> capture 20250214052637 (also 20241106214005)
- 2018-11-13T11:40:00 [2018] Conferencia – 100B+ rows: manejando grandes cantidades de datos en el cliente <https://www.innosoftdays.com/events/conferencia-100b-rows-manejando-grandes-cantidades-de-datos-en-el-cliente/> capture 20241106214706
- 2018-11-13T11:40:00 [2018] Conferencia – Los Nuevos Retos en la Ingeniería de Software Aplicada <https://www.innosoftdays.com/events/conferencia-los-nuevos-retos-en-la-ingenieria-de-software-aplicada/> capture 20250122212408 (also 20241110150834)
- 2018-11-13T12:40:00 [2018] Conferencia – Roadmap de oportunidades tecnológicas <https://www.innosoftdays.com/events/conferencia-roadmap-de-oportunidades-tecnologicas/> capture 20250213182348
- 2018-11-13T13:50:00 [2018] Conferencia – De b2/cafelog a WordPress <https://www.innosoftdays.com/events/conferencia-de-b2cafelog-a-wordpress/> capture 20250214051950 (also 20241110155749)
- 2018-11-13T13:50:00 [2018] Conferencia – OAS-Tools/Generator <https://www.innosoftdays.com/events/conferencia-oas-toolsgenerator/> capture 20250122221152 (also 20241110161002)
- 2018-11-13T15:50:00 [2018] Conferencia Introducción a Singular / Sass <https://www.innosoftdays.com/events/conferencia-introduccion-a-singular-sass/> capture 20250214055414
- 2018-11-13T15:50:00 [2018] Conferencia – Blockchain, qué es y cómo funciona <https://www.innosoftdays.com/events/conferencia-blockchain-que-es-y-como-funciona/> capture 20250213192734
- 2018-11-13T16:30:00 [2018] Conferencia – PostgreSQL: la base de datos libre más potente del mercado <https://www.innosoftdays.com/events/conferencia-postgresql-la-base-de-datos-libre-mas-potente-del-mercado/> capture 20250214041148 (also 20241106200930)
- 2018-11-13T17:30:00 [2018] Conferencia – ¿Por qué ellas no escogen carreras técnicas? <https://www.innosoftdays.com/events/conferencia-por-que-ellas-no-escogen-carreras-tecnicas/> capture 20241110163632
- 2018-11-13T17:30:00 [2018] Taller Clasificación de imágenes y detección de objetos con YOLO <https://www.innosoftdays.com/events/taller-clasificacion-de-imagenes-y-deteccion-de-objetos-con-yolo/> capture 20250213195556 (also 20241106213549)
- 2018-11-13T18:30:00 [2018] Competición de ideas open source y modelos de negocio de Bitnami <https://www.innosoftdays.com/events/competicion-de-ideas-open-source-y-modelos-de-negocio-de-bitnami/> capture 20241110153929
- 2018-11-16T10:30:00 [2018] Conferencia – Ingeniería informática: pasado, presente y futuro <https://www.innosoftdays.com/events/conferencia-ingenieria-informatica-pasado-presente-y-futuro/> capture 20250122204136 (also 20241106201855)
- 2018-11-16T10:30:00 [2018] Conferencia – Seguridad en entornos IoT <https://www.innosoftdays.com/events/conferencia-seguridad-en-entornos-iot/> capture 20250213184126 (also 20241110144018)
- 2018-11-16T11:20:00 [2018] Mesa redonda: el impacto de la ingeniería del software en la industria local <https://www.innosoftdays.com/events/mesa-redonda-el-impacto-de-la-ingenieria-del-software-en-la-industria-local/> capture 20250122215701
- 2019-11-04T08:30:00 [2019] BIENVENIDO A INNOSOFTDAYS <https://www.innosoftdays.com/events/bienvenido-a-innosoftdays/> capture 20250213180945 (also 20241110140900)
- 2019-11-04T10:30:00 [2019] ACTO DE APERTURA <https://www.innosoftdays.com/events/acto-de-apertura/> capture 20250213200309
- 2019-11-04T12:30:00 [2019] BUENAS PRÁCTICAS ESCRIBIENDO DOCKERFILES <https://www.innosoftdays.com/events/buenas-practicas-escribiendo-dockerfiles/> capture 20250209141843 (also 20241110145141)
- 2019-11-04T12:30:00 [2019] CHARLA DE VIDEOJUEGOS <https://www.innosoftdays.com/events/charla-de-videojuegos/> capture 20250122211800 (also 20241106204552)
- 2019-11-04T15:30:00 [2019] LECCIONES QUE HE APRENDIDO ESCRIBIENDO DOCUMENTACIÓN TÉCNICA <https://www.innosoftdays.com/events/lecciones-he-aprendido-escribiendo-documentacion-tecnica/> capture 20250214051107
- 2019-11-04T16:30:00 [2019] GREEN COMPUTING <https://www.innosoftdays.com/events/green-computing/> capture 20241110151924
- 2019-11-04T17:30:00 [2019] PRIVACIDAD Y AUTODEFENSA EN INTERNET <https://www.innosoftdays.com/events/privacidad-autodefensa-internet/> capture 20250214151523 (also 20241110161041)
- 2019-11-04T17:30:00 [2019] TALLER DE INICIACIÓN A SCRAPING <https://www.innosoftdays.com/events/taller-iniciacion-scraping/> capture 20250213181453
- 2019-11-04T18:30:00 [2019] INTRODUCCIÓN A REACTJS <https://www.innosoftdays.com/events/introduccion-a-reactjs/> capture 20241106203439
- 2019-11-04T19:30:00 [2019] EMPRENDIMIENTO SOFTWARE <https://www.innosoftdays.com/events/emprendimiento-software/> capture 20241110153735
- 2019-11-04T20:30:00 [2019] PROYECCIÓN DE DOCUMENTAL SOBRE EL APOLO XI Y MARGARET HAMILTON <https://www.innosoftdays.com/events/proyeccion-documental-apolo-xi-margaret-hamilton/> capture 20250209154309 (also 20241110163544)
- 2019-11-05T12:30:00 [2019] BUILDING MOBILE/WEB APPLICATIONS AND DEPLOYMENT ON CLOUD <https://www.innosoftdays.com/events/building-mobileweb-applications-and-deployment-on-cloud/> capture 20250214051336 (also 20241110155139)
- 2019-11-06T09:00:00 [2019] CÓMO LUCHAR CONTRA GOOGLE <https://www.innosoftdays.com/events/como-luchar-contra-google/> capture 20250209133443 (also 20241106195533)
- 2019-11-06T09:00:00 [2019] TALLER DE INTEGRACIÓN DE ANIMACIONES DE UNITY <https://www.innosoftdays.com/events/taller-integracion-animaciones-unity/> capture 20241106213820
- 2019-11-06T11:30:00 [2019] ESPECIAL NIÑOS – Charla dinámica sobre el Apolo XI <https://www.innosoftdays.com/events/especial-ninos-linea-del-tiempo-se-ha-desarrollado-la-web-2-2/> capture 20241110135425
- 2019-11-06T11:30:00 [2019] ESPECIAL NIÑOS – Línea del tiempo de cómo se ha desarrollado la web <https://www.innosoftdays.com/events/especial-ninos-linea-del-tiempo-se-ha-desarrollado-la-web/> capture 20250213191747
- 2019-11-06T11:30:00 [2019] ESPECIAL NIÑOS – Taller de Swift <https://www.innosoftdays.com/events/especial-ninos-linea-del-tiempo-se-ha-desarrollado-la-web-2/> capture 20250213202244 (also 20241110163528)
- 2020-11-24T08:30:00 [2020] Innosoft Days 2020 <https://www.innosoftdays.com/events/innosoft-2020/> capture 20241106203837
- 2020-11-24T10:40:00 [2020] Universidad Empresarial: el binomio perfecto <https://www.innosoftdays.com/events/universidad-empresarial-el-binomio-perfecto/> capture 20250213195028
- 2020-11-24T15:30:00 [2020] Iniciación a la clasificación de imágenes usando redes convolucionales <https://www.innosoftdays.com/events/iniciacion-a-la-clasificacion-de-imagenes-usando-redes-convolucionales/> capture 20241110142354
- 2020-11-24T15:30:00 [2020] Taller Hackatón <https://www.innosoftdays.com/events/taller-hackaton/> capture 20241106205419
- 2020-11-26T09:00:00 [2020] Presentación del día <https://www.innosoftdays.com/events/presentacion-del-dia/> capture 20250213193406 (also 20241110154828)
- 2020-11-26T09:30:00 [2020] ¿Quién es quién en una sociedad digital? <https://www.innosoftdays.com/events/identidades-y-el-uso-de-la-biometria-en-esas-identidades/> capture 20250213184500 (also 20241110144430)
- 2020-11-26T10:40:00 [2020] Limiting Global Warning by Improving Data-Centre Software <https://www.innosoftdays.com/events/limiting-global-warning-by-improving-data-centre-software/> capture 20250214041638
- 2020-11-26T11:50:00 [2020] Aportaciones de investigación y Transferencia en ciencia de datos <https://www.innosoftdays.com/events/aportaciones-ivestigacion-y-transferencia-en-ciencia-de-datos/> capture 20241110154238
- 2020-11-26T13:30:00 [2020] Procesos Inteligentes en la Industria 4.0 <https://www.innosoftdays.com/events/procesos-inteligentes-en-la-industria-4-0/> capture 20250122221233
- 2020-11-26T15:30:00 [2020] Introducción a la Computación Cuántica <https://www.innosoftdays.com/events/introduccion-a-la-computacion-cuantica/> capture 20250213202357
- 2020-11-26T18:00:00 [2020] Scape Room <https://www.innosoftdays.com/events/scape-room/> capture 20250122223158 (also 20241106215911)
- 2020-11-26T19:00:00 [2020] Como hacer los equipos de Data Science 10 veces más productivo <https://www.innosoftdays.com/events/como-hacer-los-equipos-de-data-science-10-veces-mas-productivo/> capture 20250209135618 (also 20241106200722)
- 2020-11-27T09:30:00 [2020] Introducción a soluciones open-source de “Machine Learning” <https://www.innosoftdays.com/events/las-soluciones-de-machine-learning/> capture 20241110160526
- 2020-11-27T11:50:00 [2020] Odoo, ERP con alma de framework <https://www.innosoftdays.com/events/odoo-erp-con-alma-de-framework/> capture 20241110160609
- 2020-11-27T16:00:00 [2020] Aprendizaje Automático con Swift <https://www.innosoftdays.com/events/gumus/> capture 20241106202146
- 2020-11-27T18:00:00 [2020] Trading algorítmico con criptomonedas <https://www.innosoftdays.com/events/trading-algoritmico-con-criptomonedas/> capture 20241110160648
- 2020-11-27T20:30:00 [2020] Hacia una Inteligencia Artificial Regenerativa y Redistributiva (keynote speech) <https://www.innosoftdays.com/events/hacia-una-inteligencia-artificial-regenerativa-y-redistributiva/> capture 20250209152253 (also 20241110161720)
- 2020-11-27T21:40:00 [2020] Acto de clausura <https://www.innosoftdays.com/events/acto-de-clausura/> capture 20250214054756 (also 20241110163519)
- 2021-11-08T08:30:00 [2021] Ceremonia de Apertura <https://www.innosoftdays.com/events/ceremonia-de-apertura/> capture 20250209151424
- 2021-11-08T08:45:00 [2021] Lo que nadie me contó durante la universidad <https://www.innosoftdays.com/events/lo-nadie-me-conto-la-universidad/> capture 20241108153032
- 2021-11-08T09:30:00 [2021] Quedada musical mañana <https://www.innosoftdays.com/events/quedada-musical-manana/> capture 20250213194830 (also 20241108152635)
- 2021-11-08T10:30:00 [2021] De mayor quiero ser pentester <https://www.innosoftdays.com/events/mayor-quiero-pentester/> capture 20250214043517 (also 20241110144636)
- 2021-11-08T11:30:00 [2021] Ciberinvestigando a los intrusos informáticos de un banco <https://www.innosoftdays.com/events/ciberinvestigando-los-intrusos-informaticos-banco/> capture 20250213180742
- 2021-11-08T17:30:00 [2021] Quedada musical tarde <https://www.innosoftdays.com/events/quedada-musical-tarde/> capture 20250209142203 (also 20241110145856)
- 2021-11-08T18:30:00 [2021] Hablemos de ciberseguridad, hablemos de framework de ciberseguridad <https://www.innosoftdays.com/events/hablemos-ciberseguridad-hablemos-framework-ciberseguridad/> capture 20241110144143
- 2021-11-10T08:30:00 [2021] Programación competitiva <https://www.innosoftdays.com/events/programacion-competitiva/> capture 20250122221803
- 2021-11-10T08:30:00 [2021] Torneo Rocket league <https://www.innosoftdays.com/events/torneo-rocket-league/> capture 20241106201934
- 2021-11-10T10:30:00 [2021] Identificación y Preservación de Evidencias Digitales <https://www.innosoftdays.com/events/identificacion-preservacion-evidencias-digitales/> capture 20241110163536
- 2021-11-10T10:30:00 [2021] Introducción al hacking 3 <https://www.innosoftdays.com/events/introduccion-al-hacking-3/> capture 20250122205155 (also 20241110144715)
- 2021-11-10T11:30:00 [2021] Futuro sin contraseñas <https://www.innosoftdays.com/events/futuro-sin-contrasenas/> capture 20250213185742 (also 20241110150538)
- 2021-11-10T11:30:00 [2021] Seguridad cloud-native <https://www.innosoftdays.com/events/de-devops-a-devsecpos/> capture 20250213201624 (also 20241106215306)
- 2021-11-10T15:30:00 [2021] Ciberseguridad: Retos y necesidades <https://www.innosoftdays.com/events/secureit/> capture 20241108153829
- 2021-11-10T16:30:00 [2021] Introducción a Computación Cuántica <https://www.innosoftdays.com/events/introduccion-computacion-cuantica/> capture 20250214054051 (also 20241110162538)
- 2021-11-10T16:30:00 [2021] Introducción a OWASP y herramientas de pentesting <https://www.innosoftdays.com/events/introduccion-al-pentest-herramientas/> capture 20241110162027
- 2021-11-15T08:30:00 [2021] Introducción al hacking 1 <https://www.innosoftdays.com/events/introduccion-al-hacking-1/> capture 20241106214520
- 2021-11-15T09:30:00 [2021] Comienzo en la ciberseguridad ¿Por dónde empiezo? <https://www.innosoftdays.com/events/comienzo-la-ciberseguridad-donde-empiezo/> capture 20250122222748 (also 20241110162755)
- 2021-11-15T09:30:00 [2021] Introducción al hacking 2 <https://www.innosoftdays.com/events/introduccion-al-hacking-2/> capture 20250214050712 (also 20241110153433)
- 2021-11-15T10:30:00 [2021] Ciberseguridad, ¿qué esperan los alumnos y donde estudiar lo que ellos esperan? <https://www.innosoftdays.com/events/tema-a-especificar/> capture 20250214042318
- 2021-11-15T11:30:00 [2021] Introducción al hacking 4 <https://www.innosoftdays.com/events/introduccion-al-hacking-4/> capture 20241110163648
- 2021-11-15T17:30:00 [2021] Recorrido de las programadoras <https://www.innosoftdays.com/events/recorrido-las-programadoras/> capture 20250213185456
- 2021-11-15T18:30:00 [2021] Ciberseguridad y hacking ético <https://www.innosoftdays.com/events/ciberseguridad-hacking-etico/> capture 20250209153147 (also 20241110162832)
- 2021-11-15T18:30:00 [2021] Seguridad en los servicios en la nube <https://www.innosoftdays.com/events/seguridad-los-servicios-la-nube/> capture 20250209140955 (also 20241110143714)
- 2021-11-17T08:30:00 [2021] Ciberseguridad en Containers y Kubernetes <https://www.innosoftdays.com/events/ciberseguridad-containers-kubernetes/> capture 20250209141755
- 2021-11-17T08:30:00 [2021] Torneo Rocket League <https://www.innosoftdays.com/events/torneo-rocket-league-2/> capture 20250209154506
- 2021-11-17T09:30:00 [2021] Identificación de ciber-inseguridades <https://www.innosoftdays.com/events/identificacion-de-ciberseguridades/> capture 20250214054458 (also 20241110163234)
- 2021-11-17T10:30:00 [2021] Ahora estoy acabando la carrera y … <https://www.innosoftdays.com/events/ahora-estoy-acabando-la-carrera/> capture 20250214053832
- 2021-11-17T10:30:00 [2021] Restos, servicios y salidas <https://www.innosoftdays.com/events/restos-servicios-salidas/> capture 20250122212050
- 2021-11-17T11:30:00 [2021] Firma digital e identidad digital <https://www.innosoftdays.com/events/firma-digital-e-identidad-digital/> capture 20241110141842
- 2021-11-17T15:30:00 [2021] Becario en Ciberseguridad: cómo no morir en el intento <https://www.innosoftdays.com/events/becaria-ciberseguridad-no-morir-intento/> capture 20241110160318
- 2021-11-17T16:15:00 [2021] Ciberseguridad: luchando contra el lado oscuro de la fuerza <https://www.innosoftdays.com/events/ciberseguridad-luchando-contra-el-lado-oscuro-de-la-fuerza/> capture 20241110135604
- 2021-11-17T17:15:00 [2021] Ceremonia de cierre <https://www.innosoftdays.com/events/ceremonia-de-cierre/> capture 20250214051915
- 2022-11-08T08:30:00 [2022] Inauguración Innosoft Days 2022 <https://www.innosoftdays.com/events/inauguracion-innosoft-days-2022/> capture 20241110144348
- 2022-11-08T09:30:00 [2022] Charla de Mesa Redonda <https://www.innosoftdays.com/events/charla-mesa-redonda/> capture 20250122222049
- 2022-11-08T09:30:00 [2022] Charla de Pandora <https://www.innosoftdays.com/events/charla-de-pandora/> capture 20250214054723
- 2022-11-08T09:30:00 [2022] Charla de Tragsatec <https://www.innosoftdays.com/events/charla-tragsatec-pandora-clarisa-mesa-redonda/> capture 20250213201935 (also 20241110163201)
- 2022-11-08T10:30:00 [2022] Charla de PRiSE <https://www.innosoftdays.com/events/charla-prise-maria-teresa/> capture 20241110151639
- 2022-11-08T10:30:00 [2022] Charla de la Sra. María Teresa Gómez López <https://www.innosoftdays.com/events/charla-la-sra-maria-teresa-gomez-lopez/> capture 20250122211438 (also 20241106204411)
- 2022-11-08T11:30:00 [2022] Charla de Accenture <https://www.innosoftdays.com/events/charla-de-accenture/> capture 20241110163510
- 2022-11-08T11:30:00 [2022] Charla de NTT DATA <https://www.innosoftdays.com/events/charla-nttdata-accenture/> capture 20250214044905
- 2022-11-08T13:00:00 [2022] Musica <https://www.innosoftdays.com/events/musica/> capture 20250214054310
- 2022-11-08T15:00:00 [2022] Gymkhana 1 <https://www.innosoftdays.com/events/gymkhana-1/> capture 20241106213203
- 2022-11-08T15:30:00 [2022] Charla de Red Hat <https://www.innosoftdays.com/events/redhat/> capture 20250214050833 (also 20241106205953)
- 2022-11-08T16:30:00 [2022] Charla de CoverMananger <https://www.innosoftdays.com/events/charla-oficina-software-libre-covermanage/> capture 20241106210633
- 2022-11-09T12:30:00 [2022] Brawlhalla <https://www.innosoftdays.com/events/brawlhalla/> capture 20250209141314
- 2022-11-09T15:00:00 [2022] Gymkhana 2 <https://www.innosoftdays.com/events/gymkhana/> capture 20241106203732
- 2022-11-10T08:00:00 [2022] Innosoft Days día 3 <https://www.innosoftdays.com/events/dia-dos-innosoft-days-2/> capture 20250214044945 (also 20241110150616)
- 2022-11-10T13:00:00 [2022] Grupo <https://www.innosoftdays.com/events/grupo/> capture 20250214045914 (also 20241106205224)
- 2022-11-10T17:30:00 [2022] Charla de MapTools Project Manager <https://www.innosoftdays.com/events/charla-del-sr-frank-azhrei-edwards/> capture 20250209154037 (also 20241110163458)
- 2022-11-10T17:30:00 [2022] Charla de SUSE <https://www.innosoftdays.com/events/charla-opensuse-maptool/> capture 20241110144836
- 2022-11-10T18:30:00 [2022] Charla de Libnamic <https://www.innosoftdays.com/events/charla-del-sr-jesus-bocanegra/> capture 20241110163313
- 2022-11-10T18:30:00 [2022] Charla de la Sra. Clara Grima Ruiz <https://www.innosoftdays.com/events/charla-clara-grima-libnamic/> capture 20250214042111
- 2022-11-11T08:00:00 [2022] Innosoft Days día 4 <https://www.innosoftdays.com/events/innosoft-days-dia-3/> capture 20250214150726 (also 20241110160153)
- 2022-11-11T08:30:00 [2022] Charla de Red Hat <https://www.innosoftdays.com/events/charla-del-sr-fernando-fernandez-mancera/> capture 20250122222422
- 2022-11-11T08:30:00 [2022] Charla del Sr. Manuel Jesús Flores Montaño <https://www.innosoftdays.com/events/charla-manuel-jesus-flores-sugus/> capture 20250214044510 (also 20241110150258)
- 2022-11-11T09:30:00 [2022] Charla de Deloitte <https://www.innosoftdays.com/events/charla-del-sr-antonio-castillo/> capture 20250122213224 (also 20241110151054)
- 2022-11-11T09:30:00 [2022] Charla de METADEV <https://www.innosoftdays.com/events/charla-metadev-deloitte/> capture 20250209135451 (also 20241110141509)
- 2022-11-11T10:30:00 [2022] Charla de Copyright Clearance Center <https://www.innosoftdays.com/events/charla-sra-ana-dominguez-perez-sra-carmen-andrade-perez-sra-beatriz-diaz-fernandez/> capture 20241110151359
- 2022-11-11T10:30:00 [2022] Charla de la Sra. María José Escalona <https://www.innosoftdays.com/events/charla-copyright-escalona-guadaltel/> capture 20241106203220
- 2022-11-11T11:30:00 [2022] Charla de cláusura <https://www.innosoftdays.com/events/charla-de-clausura/> capture 20250214035529 (also 20241110140201)
- 2022-11-11T12:30:00 [2022] Barrilada <https://www.innosoftdays.com/events/barrilada/> capture 20250122215402 (also 20241106210756)
- 2023-11-06T10:00:00 [2023] Stand de sostenibilidad <https://www.innosoftdays.com/events/stand-de-sostenibilidad/> capture 20250122220522
- 2023-11-06T10:30:00 [2023] Stand de igualdad <https://www.innosoftdays.com/events/stand-de-igualdad/> capture 20250214053007 (also 20241110161607)
- 2023-11-06T12:30:00 [2023] Charla de apertura de las jornadas <https://www.innosoftdays.com/events/charla-de-apertura-de-las-jornadas/> capture 20250214053043 (also 20241110161642)
- 2023-11-06T13:00:00 [2023] Producción y composición musical con Inteligencia Artificial <https://www.innosoftdays.com/events/produccion-y-composicion-musical-con-inteligencia-artificial/> capture 20250214050150
- 2023-11-06T15:30:00 [2023] Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 1 <https://www.innosoftdays.com/events/explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-1/> capture 20250213201737
- 2023-11-06T18:00:00 [2023] Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 2 <https://www.innosoftdays.com/events/explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2/> capture 20250209150019 (also 20241110154058)
- 2023-11-07T10:30:00 [2023] Gymkana <https://www.innosoftdays.com/events/gymkana/> capture 20241110155224
- 2023-11-07T17:30:00 [2023] Torneo de Smash Bros <https://www.innosoftdays.com/events/torneo-de-smash-bros/> capture 20250122215831 (also 20241110155716)
- 2023-11-08T10:30:00 [2023] CTF prueba presencial <https://www.innosoftdays.com/events/ctf-prueba-presencial/> capture 20250213193114
- 2023-11-08T12:30:00 [2023] Taller de ciberseguridad <https://www.innosoftdays.com/events/taller-de-ciberseguridad/> capture 20250213195755
- 2023-11-08T16:30:00 [2023] CTF prueba presencial <https://www.innosoftdays.com/events/ctf-prueba-presencial-2/> capture 20250214050110 (also 20241106205540)
- 2023-11-08T17:30:00 [2023] Torneo de ajedrez <https://www.innosoftdays.com/events/torneo-de-ajedrez/> capture 20250122222502 (also 20241110162359)
- 2023-11-09T10:30:00 [2023] Tecnología y arte <https://www.innosoftdays.com/events/tecnologia-y-arte/> capture 20250213181609 (also 20241108135134)
- 2023-11-09T15:30:00 [2023] La IA, motor de la transformación laboral <https://www.innosoftdays.com/events/la-ia-motor-de-la-transformacion-laboral/> capture 20241106200335
- 2023-11-09T16:30:00 [2023] El uso de chat GPT para datos estructurados con Insinno <https://www.innosoftdays.com/events/el-uso-de-chat-gpt-para-datos-estructurados-con-insinno/> capture 20241110163441
- 2023-11-09T16:30:00 [2023] Retos sociales y éticos de la IA <https://www.innosoftdays.com/events/retos-sociales-y-eticos-de-la-ia/> capture 20250213195515
- 2023-11-09T17:30:00 [2023] Transformando la salud con inteligencia artificial <https://www.innosoftdays.com/events/transformando-la-salud-con-inteligencia-artificial/> capture 20250213202130 (also 20241106215943)
- 2024-11-06T09:00:00 [2024] Charla NTT Data – Raúl López García <https://www.innosoftdays.com/events/charla-ntt-data-raul-lopez-garcia/> capture 20250214140347
- 2024-11-06T12:00:00 [2024] Charla Sostenibilidad – Rafael M Guitart <https://www.innosoftdays.com/events/charla-sostenibilidad-rafael-m-guitart/> capture 20241110160808
- 2024-11-06T16:00:00 [2024] Charla Emprendimiento – Ignasi Labastida i Juan <https://www.innosoftdays.com/events/charla-emprendimiento-ignasi-labastida-i-juan/> capture 20250213201150 (also 20241110162214)
- 2024-11-06T17:00:00 [2024] Charla Gestión emocional – Javier Antonio Pérez <https://www.innosoftdays.com/events/charla-gestion-emocional-javier-antonio-perez/> capture 20241106201625
- 2024-11-07T10:30:00 [2024] Charla Emprendimiento – Javier María de Domingo <https://www.innosoftdays.com/events/charla-emprendimiento-javier-maria-de-domingo/> capture 20241106210419
- 2024-11-07T11:00:00 [2024] Charla Proyecto de investigación – Pablo y Alberto <https://www.innosoftdays.com/events/charla-proyecto-de-investigacion-pablo-y-alberto/> capture 20250213182243 (also 20241106200821)
- 2024-11-07T16:00:00 [2024] Charla Energía renovable y emprendimiento – Anabel Carmona Guitiérrez (Maxeon) <https://www.innosoftdays.com/events/charla-energia-renovable-y-emprendimiento-anabel-carmona-guitierrez-maxeon/> capture 20250122214534 (also 20241106205831)
