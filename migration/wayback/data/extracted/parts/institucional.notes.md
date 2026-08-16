# institucional

Captures of the university-hosted WordPress (institucional.us.es/innosoft/, ColorMag theme, WordPress 4.8) used before
innosoftdays.com. Every manifest row whose host is institucional.us.es is in scope.
Captures in scope: 10. Extracted: 6. Skipped: 4 (listed below with the reason).

## Years documented by the institutional captures

The captured pages carry the site header of the edition that was current when the archive visited, so the
captures document four editions (not only the capture years):

- VI (2018): /programa/ captured 2019-06-21 still shows '50 años de la Ingeniería del Software', '12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)' and the three programme tables of 2018.
- VII (2019): the home page captured 2020-11-04 still shows the 2019 edition ('La Web cumple 30 años', '4, 5 y 6 de noviembre de 2019 en la ETSII (Sevilla)', welcome text 'InnoSoft Days 2019', poster on imgur, YouTube video).
- VIII (2020): the MEC event page (keynote of Verónica Dahl, 27 Nov 2020 20:30-21:30 on Twitch) with the 2020 header '¡Ok Google, apúntame a Innosoft!', '24, 26 y 27 de noviembre 2020'.
- IX (2021): /programa-ix-edicion/ (MEC monthly calendar) with the header '¡Ponencias sobre ciberseguridad!', '8, 10, 15 y 17 de noviembre 2021'.

## Outputs

- editions.json: 4 editions (2018 high, 2019 high, 2020 medium, 2021 high)
- events.json: 64 events (2018: 30, 2020: 1, 2021: 33)
- speakers.json: 28 speakers (2018 names parsed from the programme cells; 2020 Verónica Dahl from the MEC 'Organizador' field)
- media.json: 27 images (site logos, sponsor/collaborator logos of the footer, the 2019 poster on imgur, the 2020 keynote image)
- posts.json / organisers.json / pages.json: not written (see skipped and gaps)

Kinds per year: 2018 competition=4; 2018 other=3; 2018 social=2; 2018 stand=1; 2018 talk=18; 2018 workshop=2; 2020 talk=1; 2021 ceremony=2; 2021 competition=3; 2021 social=2; 2021 talk=22; 2021 workshop=4

## Extracted captures

- https://institucional.us.es/innosoft/ @20201104204108 | home showing VII (2019): edition, poster, 4, 5 y 6 de noviembre de 2019 en la ETSII (Sevilla)
- https://institucional.us.es/innosoft/events/hacia-una-inteligencia-artificial-regenerativa-y-redistributiva/ @20201127061643 | MEC event VIII (2020): 'Hacia una Inteligencia Artificial Regenerativa y Redistributiva (keynote speech)' 2020-11-27T20:30:00-21:30, speaker Verónica Dahl
- https://institucional.us.es/innosoft/programa/ @20190621101803 | programme VI (2018): 30 events, edition, 12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)
- https://institucional.us.es/innosoft/wp-content/uploads/2018/10/logo_2_negro-e1540204473260.png @20211107222419 | upload binary (site logo): listed in media.json as kind logo under its www.innosoftdays.com path, nothing to parse
- https://institucional.us.es/innosoft/programa-ix-edicion/ @20211107222309 | IX calendar: days with events ['20211108', '20211110', '20211115', '20211117'] (31 events)
- https://institucional.us.es/innosoft/programa-ix-edicion/?event-day=20211115 @20211114223431 | IX calendar: days with events ['20211115', '20211117'] (18 events)

## Skipped captures

- https://institucional.us.es/innosoft/ @20230812010114: empty capture (0 bytes)
- https://institucional.us.es/innosoft/events/hacia-una-inteligencia-artificial-regenerativa-y-redistributiva/ @20201123040053: older capture, main content text identical to the latest capture @20201127061643
- https://institucional.us.es/innosoft/wp-content/plugins/instagram-feed/img/placeholder.png @20211115124111: plugin asset (theme/plugin image), not site content
- https://institucional.us.es/innosoft/wp-content/plugins/tgchannel/css/geometry.png @20211115124005: plugin asset (theme/plugin image), not site content

## Not fetched (in the CDX index but not in the manifest)

- https://institucional.us.es/innosoft/category/noticias/ @20211115123930 (200, 12681 bytes): the news listing was classified 'noise' by cdx_index.py and never fetched, so no post teasers could be extracted (posts.json not written by this family). Rerun fetch.py with that URL if the teasers are wanted.
- The 2024 and 2026 captures of the institutional URLs are 404/302 (site gone), not fetched.

## How the data was read

- Header: '#site-description' is the edition tagline (theme); the last <p> of '#header-right-sidebar' is the dates line ('12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)'); starts_on/ends_on are the min/max of the listed days. Venue is the footer 'Localización' (ETSII, Av. Reina Mercedes, Sevilla), except 2020 (Twitch).
- 2018 programme: three <table class='schedule'> (one per day, day in the preceding <h1>). Header row = 'Hora' + rooms; cells are placed on a grid honouring colspan/rowspan, and a rowspan extends ends_at to the end of the last covered row (Blockchain 15:30-17:20, taller YOLO 17:30-19:00, competición Bitnami 18:30-19:30). The <strong> label of the cell gives the kind (Conferencia=talk, Taller=workshop, Proyección=social, Mesa Redonda=talk, Competición=competition); unlabeled cells: Recepción/sorteo=other, Networking=social, otherwise talk. 'Descanso' and 'Fin de ...' rows are not events. Off-schedule activities (Software Room, TOURNAMETSII, Gymkhana, Trivia, Museo interactivo) come from the <ul> above the 13 Nov table (times/rooms parsed from the text when stated).
- 2018 speakers: the parenthesised names at the end of the cell ('Los estudios de Ingeniería de Software... (Amador Durán y José Luis Sevillano)'); parenthesised company names (Abatic) and trailing glued company names ('...(David Borrego y Ana Aparicio)atSistemas', '<p>Bitnami</p>') go to company. Two cells have no name in the text; their Eventbrite slug does (taller YOLO -> Jesús Utrera y Joaquín Salguero; PostgreSQL/Abatic -> Emilio Pérez y José Segovia), accents restored by hand in the parser. The mesa redonda slug says 'mesa-redonda-con-david-benavides' (kept out of speaker, moderator not stated in the page). The 'Reserva tu plaza' Eventbrite/registration URL is the event link.
- 2020 event: MEC single-event template; date from .mec-start-date-label ('Nov 27 2020'), time from .mec-single-event-time (20:30 - 21:30, displayed local time; the Google Calendar link writes the same digits with a Z suffix, MEC does not convert), location 'Twitch Innosoft' with URL twitch.tv/innosoftdays (modality online, link), category '2020', 'Organizador' = Verónica Dahl with her web page (used as speaker; MEC has no speaker module here). Description is empty in the capture. The featured image IA-regenarativa-min.jpg is the poster.
- 2021 calendar: .mec-calendar-events-sec[data-mec-cell] per day, article.mec-event-article with time, title/link, room and a category colour (#fdd700 ceremony, #00a0d2 talk, #a3b745 activities -> competition/social/workshop by title keywords). Merge of the two captures: each day is taken from the LATEST capture that lists it (the ?event-day=20211115 capture hides past days). Days 8 and 10 Nov: 2021-11-07 capture; days 15 and 17 Nov: 2021-11-14 capture, which splits 'Introducción al hacking' (08:30-12:30) into four hourly slots, moves 'Ciberseguridad, ¿qué esperan los alumnos...' from A3.11 to H1.10, drops 'De que hablamos cuando hablamos de ciberseguridad' (17:30 H1.10) and fixes the title 'Identificación de ciber-inseguridades'. Speakers are not on the calendar (the /ponentes-ix-edicion/ page was not captured); event links point at institucional.us.es/innosoft/events/... (not captured either).
- Media URLs: uploads under institucional.us.es/innosoft/wp-content/ are mapped to www.innosoftdays.com/wp-content/ by norm_media_url() (same paths after the move, as the other families do); the site logo logo_2_negro-e1540204473260.png exists in the raw uploads under both hosts. IA-regenarativa-min.jpg (2020/11) is not in the CDX index. Sponsor logos hosted elsewhere (bitnami.com, imgur, elpatriarca.com...) keep their external URL.

## Oddities

- The 2020-11-04 home capture is NOT the 2020 edition: on that date the site still served the 2019 home (widget 'InnoSoft Days 2019', copyright 2018); the 2020 site had its own header by 2020-11-23 (event page).
- The 2019 programme (VII) is not captured: /programa/ was archived in June 2019 and still showed 2018; the 2020 programme page (/programa-viii-edicion/) and the 2019/2020/2021 speakers pages were never archived.
- 2018 tables use inconsistent markup (title in <p> or bare text after <br>, speaker sometimes in the next <p>, 'Reserva tu plaza' inside or outside <p>); the parser works on the cell text after removing the label and the link.
- 2018 cell 'Introducción a Sngular – Inmaculada Rodríguez Vizcaína / Introducción a Sass – María del Carmen García Peral' is one 15:30-16:20 slot with one Eventbrite link: kept as one event with both titles and both speakers (company left null; Sngular only appears inside the first title).
- The 2019 poster is an external image (i.imgur.com/IaHdCku.png), so is the OpenWebinars sponsor logo; the importer cannot resolve them from raw uploads.
- The 2019 home menu had 'INSCRIPCIONES' -> /innosoft/inscipciones/ (sic); not used as registration_url (dead link).
- The two captures of the 2020 event page differ only in nonces/timestamps in scripts; the earlier one is skipped as identical.
- IX calendar day 15: the 2021-11-07 capture listed a single 4-hour 'Introducción al hacking' (A3.11); the later capture lists 'Introducción al hacking 1..4' as hourly slots. Only the later version is kept (no duplicates).

## IX calendar merge (day -> capture used)

- 20211108: https://institucional.us.es/innosoft/programa-ix-edicion/ @20211107222309
- 20211110: https://institucional.us.es/innosoft/programa-ix-edicion/ @20211107222309
- 20211115: https://institucional.us.es/innosoft/programa-ix-edicion/?event-day=20211115 @20211114223431
- 20211117: https://institucional.us.es/innosoft/programa-ix-edicion/?event-day=20211115 @20211114223431
