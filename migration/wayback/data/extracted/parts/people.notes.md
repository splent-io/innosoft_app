# people family notes

Parser: parse/people.py. Sources: WordPress pages that describe people (speaker info pages of the X edition, the XI schedule table, the Eventin 'Ponente' listing of the XII edition and the organising-team pages).

Captures in scope: 47 (kind=speaker plus URL patterns of the scope). Extracted from 24, skipped 23 (all listed below).

## Outputs

- people.speakers.json: 47 speakers (deduplicated by accent-insensitive name).
- people.organisers.json: 294 organiser rows (one per edition_year + name, roles merged with ' / ').
- people.events.json: 10 talks of the XI edition (2023) taken from the schedule table of /ponentes-xi-edicion/ (times and rooms are only there; the posts family has the same talks without times, dedupe on edition_year + title).

## Per-year counts

- speakers by edition_year (a speaker counts in every year): {2018: 2, 2020: 1, 2021: 3, 2022: 17, 2023: 21, 2024: 10}
- speakers with no edition year: 0
- organisers by edition_year: {2023: 144, 2024: 150}
- events by edition_year: {2023: 10}

## Covered captures

- 20241110163015 https://www.innosoftdays.com/2023/10/30/informacion-sobre-la-ponencia-de-produccion-y-composicion-musical-con-inteligencia-artificial/ : 2023 talk poster post; speakers taken from the XI table row linking it
- 20241108160503 https://www.innosoftdays.com/2023/10/30/informacion-sobre-la-ponencia-del-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2/ : 2023 talk poster post; speakers taken from the XI table row linking it
- 20250209141353 https://www.innosoftdays.com/carlos-perez/ : speaker page: Carlos Pérez
- 20241210210955 https://www.innosoftdays.com/etn_category/ponente/ : Eventin 'Ponente' listing (page 1 of 2): 10 speakers
- 20250214040407 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sr-clara-isabel-grima-ruiz/ : speaker page: Clara Isabel Grima Ruiz
- 20250121053019 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-del-carmen-romero-ternero/ : speaker page: María del Carmen Romero Ternero
- 20241108160035 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-teresa-gomez-lopez/ : speaker page: María Teresa Gómez López
- 20241108145935 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-los-srs-rafael-poveda-santos-y-jose-carlos-gomez/ : speaker page: Rafael Poveda Santos, José Carlos Gómez
- 20250213183911 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-antonio-castillo/ : speaker page: Antonio Castillo
- 20250209141151 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-fernando-fernandez-mancera/ : speaker page: Fernando Fernández Mancera
- 20250214154440 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-frank-azhrei-edwars/ : speaker page: Frank "Azhrei" Edwars
- 20250122210858 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares/ : speaker page: Israel Blancas Álvarez
- 20250214150448 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-jesus-alcaide-marin/ : speaker page: Jesús Alcaide Marín
- 20250209135703 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/ : speaker page: Sancho Lerena
- 20241110163656 https://www.innosoftdays.com/libnamic/ : title names the speaker (newer capture lost the title)
- 20250428164126 https://www.innosoftdays.com/libnamic/ : speaker page: Jesús Bocanegra
- 20250520124523 https://www.innosoftdays.com/manuel-jesus-flores-montano/ : speaker page: Manuel Jesús Flores Montaño
- 20250213202427 https://www.innosoftdays.com/maria-jose-escalona/ : speaker page: María José Escalona
- 20250121044422 https://www.innosoftdays.com/organizacion-xi-edicion/ : organising team 2023: 144 people
- 20241110162250 https://www.innosoftdays.com/organizacion-xii-edicion/ : organising team 2024: 154 people
- 20240913023826 https://www.innosoftdays.com/ponentes-xi-edicion/ : XI schedule table: 21 speakers, 10 talks
- 20250122214109 https://www.innosoftdays.com/prise/ : speaker page: Daniel García
- 20250209143028 https://www.innosoftdays.com/red-hat/ : speaker page: Israel Blancas Álvarez
- 20241110155521 https://www.innosoftdays.com/tragsatec/ : speaker page: Javier Haro

## Skipped captures (with reason)

- 20241106202016 https://www.innosoftdays.com/en/xii-edition-organization/ : English translation of /organizacion-xii-edicion/ (same names, roles in English)
- 20241110151703 https://www.innosoftdays.com/etn-speaker-category/ : Eventin speaker taxonomy archive with no entries (only term names / 'nothing found')
- 20250213191612 https://www.innosoftdays.com/etn-speaker-category/ : Eventin speaker taxonomy archive with no entries (only term names / 'nothing found')
- 20241210212248 https://www.innosoftdays.com/etn-speaker-category/organizer/ : Eventin speaker taxonomy archive with no entries (only term names / 'nothing found')
- 20241210211650 https://www.innosoftdays.com/etn-speaker-category/uncategorized/ : Eventin speaker taxonomy archive with no entries (only term names / 'nothing found')
- 20240625100208 https://www.innosoftdays.com/forums/topic/buy-levonorgestrel-ohio-componentes-levonorgestrel-etinilestradiol/ : not a people page (asset / bbPress spam topic wrongly classified as kind=speaker)
- 20241106200244 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sr-clara-isabel-grima-ruiz/ : older version of the same page (same cards, smaller thumbnails)
- 20250214044108 https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-teresa-gomez-lopez/embed/ : WordPress oEmbed stub of https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-teresa-gomez-lopez/
- 20241108141828 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-antonio-castillo/ : older version of the same page (same cards, smaller thumbnails)
- 20241110143843 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-fernando-fernandez-mancera/ : older version of the same page (same cards, smaller thumbnails)
- 20241212044006 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-fernando-fernandez-mancera/embed/ : WordPress oEmbed stub of https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-fernando-fernandez-mancera/
- 20241110163640 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-frank-azhrei-edwars/ : older version of the same page (same cards, smaller thumbnails)
- 20241106203805 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares/ : older version of the same page (same cards, smaller thumbnails)
- 20221107115639 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/ : older version of the same page (same cards, smaller thumbnails)
- 20221107131153 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/?hss_channel=tw-72764810 : query-string duplicate of https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/
- 20221107131041 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/?utm_content=227246656&utm_medium=social&utm_source=twitter&hss_channel=tw-72764810 : query-string duplicate of https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/
- 20221108075315 https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/?utm_content=227248821&utm_medium=social&utm_source=twitter&hss_channel=tw-72764810 : query-string duplicate of https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/
- 20241110163551 https://www.innosoftdays.com/maria-jose-escalona/ : older version of the same page (same cards, smaller thumbnails)
- 20241106203625 https://www.innosoftdays.com/organizacion-ix-edicion/ : placeholder page, no team listed ('aún no están disponibles')
- 20240616212816 https://www.innosoftdays.com/organizacion-xi-edicion/ : older version, same names as 20250121044422
- 20240616223829 https://www.innosoftdays.com/ponentes-xi-edicion/ : older version, identical content to 20240913023826
- 20241106205721 https://www.innosoftdays.com/prise/ : older version of the same page (same cards, smaller thumbnails)
- 20221107001944 https://www.innosoftdays.com/wp-content/plugins/innosoft2021/assets/css/ponentes.css : not a people page (asset / bbPress spam topic wrongly classified as kind=speaker)

## Speakers extracted

| name | affiliation | position | years | talk(s) | sources |
|---|---|---|---|---|---|
| Carlos Pérez | CoverManager | empresarios en el ámbito de software | 2022,2023 | Charla de CoverMananger; Explorando el futuro profesional de los nuevos Ingenieros de Software: Parte 2 | https://www.innosoftdays.com/carlos-perez/ https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Jose Luis Fontenla | Rewoox | CTO | 2024 | Jose Luis Fontenla y María Mendoza | https://www.innosoftdays.com/etn_category/ponente/ |
| María Mendoza | Rewoox | Directora de Innovación | 2024 | Jose Luis Fontenla y María Mendoza | https://www.innosoftdays.com/etn_category/ponente/ |
| Irene M Morgado |  | Experta en perfiles informáticos | 2024 | Irene M Morgado | https://www.innosoftdays.com/etn_category/ponente/ |
| Anabel Carmona Gutiérrez |  |  | 2024 | Sol y Ciberseguridad: Anabel Carmona Gutiérrez | https://www.innosoftdays.com/etn_category/ponente/ |
| Javier María de Domingo Morales |  |  | 2024 | Emprendimiento: Javier María de Domingo Morales | https://www.innosoftdays.com/etn_category/ponente/ |
| Pablo Pérez | Universidad de Sevilla | Profesor (proyecto de investigación VOLUM) | 2024 | VOLUM: Pablo Pérez y Alberto Olmo | https://www.innosoftdays.com/etn_category/ponente/ |
| Alberto Olmo | Universidad de Sevilla | Profesor (proyecto de investigación VOLUM) | 2024 | VOLUM: Pablo Pérez y Alberto Olmo | https://www.innosoftdays.com/etn_category/ponente/ |
| Jose Antonio Pérez |  | Psicólogo especialista en gestión de emociones | 2024 | Jose Antonio Pérez | https://www.innosoftdays.com/etn_category/ponente/ |
| Rafael M Guitart |  | Profesor, informático (ICTS-Doñana) | 2024 | Rafael M Guitart | https://www.innosoftdays.com/etn_category/ponente/ |
| Raul López García | NTT Data | Digital Transformation Executive | 2024 | Raul López García | https://www.innosoftdays.com/etn_category/ponente/ |
| Clara Isabel Grima Ruiz |  |  | 2018,2022 | Charla de la Sra. Clara Grima Ruiz | https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sr-clara-isabel-grima-ruiz/ |
| María del Carmen Romero Ternero |  |  | 2022 |  | https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-del-carmen-romero-ternero/ |
| María Teresa Gómez López |  |  | 2022 | Charla de la Sra. María Teresa Gómez López | https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-la-sra-maria-teresa-gomez-lopez/ |
| Rafael Poveda Santos | Accenture |  | 2018,2022 | Charla de Accenture | https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-los-srs-rafael-poveda-santos-y-jose-carlos-gomez/ |
| José Carlos Gómez | Accenture |  | 2022 | Charla de Accenture | https://www.innosoftdays.com/informacion-sobre-la-ponencia-de-los-srs-rafael-poveda-santos-y-jose-carlos-gomez/ |
| Antonio Castillo | Deloitte |  | 2022 | Charla de Deloitte | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-antonio-castillo/ |
| Fernando Fernández Mancera | Red Hat |  | 2022 | Charla de Red Hat | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-fernando-fernandez-mancera/ |
| Frank "Azhrei" Edwars | MapTool |  | 2022 | Charla de MapTools Project Manager | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-frank-azhrei-edwars/ |
| Israel Blancas Álvarez | Red Hat |  | 2022 | Charla de Red Hat | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares/ https://www.innosoftdays.com/red-hat/ |
| Jesús Alcaide Marín | NTT DATA |  | 2022 | Charla de NTT DATA | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr-jesus-alcaide-marin/ |
| Sancho Lerena | Ártica (Pandora FMS) | CEO y fundador | 2022 | Charla de Pandora | https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/ |
| Jesús Bocanegra | Libnamic |  | 2022 | Charla de Libnamic | https://www.innosoftdays.com/libnamic/ |
| Manuel Jesús Flores Montaño |  |  | 2021,2022 | Charla del Sr. Manuel Jesús Flores Montaño | https://www.innosoftdays.com/manuel-jesus-flores-montano/ |
| María José Escalona |  |  | 2020,2021,2022 | Charla de la Sra. María José Escalona | https://www.innosoftdays.com/maria-jose-escalona/ |
| José María García |  | estudiantes | 2023 | Charla de la producción y composición musical con IA | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Alberto Perea |  | estudiantes | 2023 | Charla de la producción y composición musical con IA | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Guillermo Martín |  | estudiantes | 2023 | Charla de la producción y composición musical con IA | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Soraya Peceño |  | Ingeniera con 15 años de experiencia | 2023 | Explorando el futuro profesional de los nuevos ingenieros software. Parte1 | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Carlos Müller |  | Profesor de la ETSII | 2023 | Explorando el futuro profesional de los nuevos ingenieros software. Parte1 | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Pablo Cala |  | empresarios en el ámbito de software | 2023 | Explorando el futuro profesional de los nuevos Ingenieros de Software: Parte 2 | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| José Ignacio Morales |  | empresarios en el ámbito de software | 2023 | Explorando el futuro profesional de los nuevos Ingenieros de Software: Parte 2 | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Isabel Cayrasso |  | analista de ciberseguridad en GeseRisk | 2023 | Taller de ciberseguridad | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Rocío García Robles |  | IP1 y promotora del proyecto ASTER | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Olga Albillos Castillo |  | estudiante de doctorado en el grupo de investigación TIC247 | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Helena Hernández Acuaviva |  | Personal Investigador en Formación, docente y doctoranda de la US | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Leila Pontiga Gaytán |  | Artista y Animadora 2D en Talky | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Irene Ugolini Sánchez-Barroso |  | doctoranda de la US | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Ana Rosa González Diánez |  | diseñadora UX/UI, y doctoranda de la US | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Guillermo Rodríguez |  | artista y doctorando de la US | 2023 | Tecnología y arte | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Ricardo Arjona Antolin |  | Ingeniero informático y empresario | 2023 | La IA, motor de la transformación laboral | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Jose María González Vázquez |  | fundador y gerente de Insinno España | 2023 | El uso de Chat GPT para datos estructurados con Insinno | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Fernando Soler Toscano |  | profesor de lógica en las facultades de filosofía y derecho | 2023 | Retos sociales y éticos de la IA | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Carlos Luis Parra Calderón |  | jefe de Sección de Innovación Tecnológica en el Hospital Universitario Virgen del Rocío | 2023 | Transformando la salud con inteligencia artificial | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Antonio J. Domínguez |  | exalumno e investigador de inteligencia artificial | 2023 | Superando barreras de escalado en las large lenguage models (LLM) | https://www.innosoftdays.com/ponentes-xi-edicion/ |
| Daniel García | PRiSE |  | 2021,2022 | Charla de PRiSE | https://www.innosoftdays.com/prise/ |
| Javier Haro | Tragsatec |  | 2022 | Charla de Tragsatec | https://www.innosoftdays.com/tragsatec/ |

## Edition years added by cross-checking posts/events captures and other families' parts

- Clara Isabel Grima Ruiz: own [2022] + [2018]
- María del Carmen Romero Ternero: own [] + [2022]
- Rafael Poveda Santos: own [2022] + [2018]
- Manuel Jesús Flores Montaño: own [2022] + [2021]
- María José Escalona: own [2022] + [2020, 2021]
- Daniel García: own [2022] + [2021]

## Oddities and decisions

- The X edition (2022) speaker pages contain only infographic cards (PNG images, 2 or 3 per page: portrait+title, talk, date). The text of the cards is not in the HTML, so bio_html keeps the images (original URLs) and affiliation comes from the MEC event that embeds each page ('Charla de <company>' in the JSON-LD of /x-edicion/ and /events/charla-*). Only Sancho Lerena's cards were fetched (uploads/2022/11/1-22.png ...); his position was read from the image by hand ('CEO y fundador de Ártica').
- Not fetched by the collector, so no cards to read for the other 2022 speakers: uploads/2022/11/1-7, 1-18, 1-20, 1-1, ACCENTURE, deloitte(only html), 1-17, 1-15, 1-14, 1-16, 1-8, 1-10, 1-11, 1-12.png.
- 'Israel Blancas Álvares' (slug typo of /informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares/) and 'Israel Blancas Álvarez' (/red-hat/) are the same Red Hat speaker; merged under the correct spelling.
- 'Frank "Azhrei" Edwars' is kept as written on the site (real name Frank Edwards, MapTool project). 'CoverMananger' normalised to CoverManager, 'Pandora' to 'Ártica (Pandora FMS)'.
- /manuel-jesus-flores-montano/ is an attachment page (image uploaded 2021/10) that the 2022 MEC event 'Charla del Sr. Manuel Jesús Flores Montaño' (2022-11-11) embeds; the image is used as photo_url.
- The two 2023 posts 'Información sobre la ponencia ...' hold only a poster; their speakers come from the XI table row that links them and the poster becomes bio_html/description.
- XI table cell 'Soraya Peceño, Ingeniera ..., Carlos Müller, Profesor de la ETSII, Isabel y Mathew galardonados ...' is split by an explicit override; 'Isabel' and 'Mathew' (no surname there) are not emitted from this family (posts family has Isabel Arrans Vega and Matthew Bwye Lera).
- Eventin listing /etn_category/ponente/ is page 1 of 2 (page 2 not captured). Titles mixing company and first names ('4i.ai: Andrés y Adolfo', 'RRHH: NttData') produce no speaker. Affiliation/position for those rows come from the excerpt text (see ETN_TITLE_OVERRIDES).
- /en/xii-edition-organization/ is the English copy of /organizacion-xii-edicion/ (same 182 list entries, 157 distinct people); Spanish roles are kept. /organizacion-ix-edicion/ is a placeholder ('aún no están disponibles'). Both XI organisation captures list the same 160 names.
- Organisation lists contain usernames ('santizdr', 'peperez.17', 'bogdan.stefan'); entries with fewer than two name tokens, digits, dotted handles or a lowercase start are dropped.
- 'Daniel García' (PRiSE, 2021 and 2022) and 'Daniel García Moreno' (SUSE, 2022, page not captured) are different people; the two-token name makes the year cross-check accept any 'Daniel García' title, so his years may include a SUSE talk.
- Sources of edition years: XI table headings (2023), MEC JSON-LD dates (2022), Eventin listing (2024), plus cross-check by name over post/event capture titles (year from post URL, JSON-LD startDate, Eventin 'Date :', published meta) and over the other families' speakers/events parts when present.
- /informacion-sobre-la-ponencia-de-la-sra-maria-del-carmen-romero-ternero/ is embedded by no captured MEC event (the 2022 round table event points at a preview URL), so her 2022 comes only from the cross-check (posts_2022 names her as Directora de la ETSII).
- photo_url of the 2024 Eventin rows is the event's featured image, which is a portrait for most speakers but a poster/screenshot for Rewoox (Fontenla, Mendoza) and VOLUM (Pérez, Olmo).
- MEC embed map resolved 21 speaker-page URLs to a dated 2022 talk.
