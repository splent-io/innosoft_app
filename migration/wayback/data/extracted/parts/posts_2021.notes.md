# posts_2021 (InnoSoft Days IX, 2021)

Parser: `parse/posts_2021.py`. Inputs: manifest rows of kind=post with a `/2021/MM/DD/` URL.

## Coverage

- Captures in scope: 51 (URLs: 32). Every URL extracted; nothing skipped.
- Posts written: 32 (17 announcements, 15 "[RESUMEN]" write-ups). All are 2021, Spanish, category
  "Noticias" except two in "Sin categoría" (computación cuántica announcement + resumen).
- Events written: 17 talks (one per announcement; the resumen of the same talk is merged into
  `description_html`; 15 talks have a resumen, 2 do not).
- Speakers written: 19.
- Editions written: 1 (2021, IX), derived from the posts; confidence medium.
- No pages, organisers or media in this family: none of the 32 posts contains an image, gallery, iframe or featured image.
- Unpaired resumen posts: none.

## Versions per URL

Where a URL has two captures (2024-11 and 2025-01/02) the cleaned `entry-content` is identical up to whitespace
between tags (five posts differ only in newlines around tags in the raw HTML); the latest capture is kept and
its timestamp goes to `source_timestamp`.

| slug | captures | timestamps | kept | content |
|---|---|---|---|---|
| hablemos-ciberseguridad-hablemos-frameworkd-ciberseguridad-dolbuck-s-l | 2 | 20241110142117, 20250214134639 | 20250214134639 | identical |
| lo-nadie-me-conto-la-universidad | 2 | 20241110151549, 20250209144012 | 20250209144012 | identical |
| mayor-quiero-pentester-david-sanchez | 2 | 20241110154015, 20250121052354 | 20250121052354 | identical |
| ciberseguridad-retos-necesidades-francisco-valencia | 2 | 20241108140917, 20250209140318 | 20250209140318 | identical |
| futuro-sin-contrasenas-daniel-garcia | 1 | 20241106214408 | 20241106214408 | identical |
| identificacion-preservacion-evidencias-digitales-alberto-castro | 2 | 20241110155906, 20250209150853 | 20250209150853 | identical |
| introduccion-la-computacion-cuantica-jose-martinez-garcia | 1 | 20250122204919 | 20250122204919 | identical |
| introduccion-owasp-herramientas-pentesting-paula-garrido-lerma-jesus-manuel-sanchez-alanis | 2 | 20241110150018, 20250209142433 | 20250209142433 | identical |
| seguridad-cloud-native-alba-ferri | 1 | 20250214044745 | 20250214044745 | identical |
| ciberseguridad-esperan-los-alumnos-donde-estudiar-lo-esperan-angel-jesus-varela-vaca | 2 | 20241106204953, 20250214045435 | 20250214045435 | identical |
| ciberseguridad-hacking-etico-francisco-ramirez | 2 | 20241110142612, 20250209140552 | 20250209140552 | identical |
| comienzo-la-ciberseguridad-donde-empiezo-manuel-jesus-flores-montano | 1 | 20241110154151 | 20241110154151 | identical |
| seguridad-los-servicios-la-nube-andres-marchante-tirado | 1 | 20250209154231 | 20250209154231 | identical |
| ahora-estoy-acabando-la-carrera-maria-jose-escalona | 1 | 20250213194304 | 20250213194304 | identical |
| becario-ciberseguridad-no-morir-intento-francisco-perez-fernandez | 2 | 20241110141942, 20250214041359 | 20250214041359 | identical |
| firma-digital-e-identidad-digital-jesus-lopez | 2 | 20241106205157, 20250213191232 | 20250213191232 | identical |
| identificacion-ciber-inseguridades-rafael-martinez | 1 | 20241110161533 | 20241110161533 | identical |
| resumen-futuro-sin-contrasenas-daniel-garcia | 2 | 20241110153848, 20250214051030 | 20250214051030 | identical |
| resumen-introduccion-owasp-herramientas-pentesting-paula-garrido-jesus-manuel-sanchez | 2 | 20241110145041, 20250214141438 | 20250214141438 | identical |
| resumen-mayor-quiero-pentester-david-sanchez | 1 | 20250122210637 | 20250122210637 | identical |
| resumen-seguridad-cloud-native-alba-ferri | 1 | 20241110151455 | 20241110151455 | identical |
| resumen-ciberseguridad-hacking-etico-francisco-jimenez | 2 | 20241106220402, 20250213202534 | 20250213202534 | identical |
| resumen-ahora-estoy-acabando-la-carrera-maria-jose-escalona | 1 | 20250209141712 | 20250209141712 | identical |
| resumen-identificacion-ciber-inseguridades-rafael-martinez-gasca | 2 | 20241110141105, 20250214040501 | 20250214040501 | identical |
| resumen-becario-ciberseguridad-no-morir-intento-francisco-perez-fernandez | 2 | 20241106195817, 20250214035915 | 20250214035915 | identical |
| resumen-ciberseguridad-esperan-los-alumnos-donde-estudiar-lo-esperan-angel-jesus-varela-vaca | 2 | 20241108153746, 20250209152059 | 20250209152059 | identical |
| resumen-comienzo-la-ciberseguridad-donde-empiezo-manuel-jesus-flores | 2 | 20241110150909, 20250122212800 | 20250122212800 | identical |
| resumen-hablemos-ciberseguridad-hablemos-framework-ciberseguridad-dolbuck-s-l | 1 | 20250122223353 | 20250122223353 | identical |
| resumen-identificacion-preservacion-evidencias-digitales-alberto-castro | 2 | 20241108144840, 20250122214022 | 20250122214022 | identical |
| resumen-introduccion-la-computacion-cuantica-jose-martinez-garcia | 1 | 20241108151719 | 20241108151719 | identical |
| resumen-lo-nadie-me-conto-la-universidad-alberto-fernandez | 2 | 20241106211014, 20250214051417 | 20250214051417 | identical |
| resumen-seguridad-los-servicios-la-nube-andres-marchante-tirado | 1 | 20250209150657 | 20250209150657 | identical |

## Talks (events)

Date/time/room parsed from the announcement prose ("La ponencia tendrá lugar el día 10 de Noviembre de 2021, de
11:30 a 12:30, en el aula A0.11 de la ETSII"). Speaker full names, company and position come from a curated table
in the parser, quoting the announcement or the resumen (e.g. Dolbuck's speaker Adrián Ramírez, CEO, is only named
in the resumen; Francisco Pérez Fernández's employer NTT DATA likewise). `link` is the Eventbrite ticket URL.
`source_url` is the announcement post; the resumen URL is in the last column.

| starts_at | room | title | speaker | company | announcement slug | resumen slug |
|---|---|---|---|---|---|---|
| 2021-11-08 | A2.16 | Hablemos de ciberseguridad, hablemos de framework de ciberseguridad | Adrián Ramírez | Dolbuck S.L. | hablemos-ciberseguridad-hablemos-frameworkd-ciberseguridad-dolbuck-s-l | resumen-hablemos-ciberseguridad-hablemos-framework-ciberseguridad-dolbuck-s-l |
| 2021-11-08T08:45:00 – 09:30 | H0.12 | Lo que nadie me contó sobre la universidad | Alberto Fernández Valiente |  | lo-nadie-me-conto-la-universidad | resumen-lo-nadie-me-conto-la-universidad-alberto-fernandez |
| 2021-11-08T10:30:00 | ? | De mayor quiero ser pentester | David Sánchez | Sputnik Ciberseguridad | mayor-quiero-pentester-david-sanchez | resumen-mayor-quiero-pentester-david-sanchez |
| 2021-11-10T10:30:00 – 11:30 | A0.11 | Identificación y preservación de evidencias digitales | Alberto Castro Ortiz | OnRetrieval | identificacion-preservacion-evidencias-digitales-alberto-castro | resumen-identificacion-preservacion-evidencias-digitales-alberto-castro |
| 2021-11-10T11:30:00 – 12:30 | A0.11 | El futuro sin contraseñas | Daniel García | PRiSE | futuro-sin-contrasenas-daniel-garcia | resumen-futuro-sin-contrasenas-daniel-garcia |
| 2021-11-10T11:30:00 – 12:30 | B1.35 | Seguridad cloud-native | Alba Ferri | Sysdig | seguridad-cloud-native-alba-ferri | resumen-seguridad-cloud-native-alba-ferri |
| 2021-11-10T15:30:00 – 16:30 | H0.12 | Ciberseguridad: Retos y necesidades | Francisco Valencia | Secure&IT | ciberseguridad-retos-necesidades-francisco-valencia | no resumen |
| 2021-11-10T16:30:00 – 17:30 | H1.10 | Introducción a OWASP y herramientas de pentesting | Paula Garrido Lerma y Jesús Manuel Sánchez Alanís | BeOneSec | introduccion-owasp-herramientas-pentesting-paula-garrido-lerma-jesus-manuel-sanchez-alanis | resumen-introduccion-owasp-herramientas-pentesting-paula-garrido-jesus-manuel-sanchez |
| 2021-11-10T16:30:00 – 17:30 | H0.12 | Introducción a la computación cuántica | José Martínez García |  | introduccion-la-computacion-cuantica-jose-martinez-garcia | resumen-introduccion-la-computacion-cuantica-jose-martinez-garcia |
| 2021-11-15T09:30:00 – 10:30 | H0.12 | Comienzo en la ciberseguridad ¿Por dónde empiezo? | Manuel Jesús Flores Montaño | Universidad Pablo de Olavide | comienzo-la-ciberseguridad-donde-empiezo-manuel-jesus-flores-montano | resumen-comienzo-la-ciberseguridad-donde-empiezo-manuel-jesus-flores |
| 2021-11-15T10:30:00 – 11:30 | H1.10 | Ciberseguridad, ¿Qué esperan los alumnos y donde estudiar lo que ellos esperan? | Ángel Jesús Varela Vaca | Universidad de Sevilla | ciberseguridad-esperan-los-alumnos-donde-estudiar-lo-esperan-angel-jesus-varela-vaca | resumen-ciberseguridad-esperan-los-alumnos-donde-estudiar-lo-esperan-angel-jesus-varela-vaca |
| 2021-11-15T18:30:00 – 19:30 | A3.10 | Ciberseguridad y hacking ético | Francisco José Ramírez López | Deloitte | ciberseguridad-hacking-etico-francisco-ramirez | resumen-ciberseguridad-hacking-etico-francisco-jimenez |
| 2021-11-15T18:30:00 – 19:30 | H1.10 | Seguridad en los servicios en la nube | Andrés Marchante Tirado | Dell | seguridad-los-servicios-la-nube-andres-marchante-tirado | resumen-seguridad-los-servicios-la-nube-andres-marchante-tirado |
| 2021-11-17T09:30:00 – 10:30 | Salón de Grados | Identificación de ciber inseguridades | Rafael Martínez Gasca | Universidad de Sevilla | identificacion-ciber-inseguridades-rafael-martinez | resumen-identificacion-ciber-inseguridades-rafael-martinez-gasca |
| 2021-11-17T10:30:00 – 11:30 | Salón de Grados | Ahora estoy acabando la carrera y … | María José Escalona | Universidad de Sevilla | ahora-estoy-acabando-la-carrera-maria-jose-escalona | resumen-ahora-estoy-acabando-la-carrera-maria-jose-escalona |
| 2021-11-17T11:30:00 – 12:30 | Salón de Grados | Firma digital e identidad digital | Jesús López y Benito Galán Algora | Viafirma | firma-digital-e-identidad-digital-jesus-lopez | no resumen |
| 2021-11-17T15:30:00 – 16:30 | Salón de Grados | Becario en Ciberseguridad: como no morir en el intento | Francisco Pérez Fernández | NTT DATA | becario-ciberseguridad-no-morir-intento-francisco-perez-fernandez | resumen-becario-ciberseguridad-no-morir-intento-francisco-perez-fernandez |

## Oddities

- "Ciberseguridad y hacking ético" (Francisco José Ramírez López): the announcement says "14 de Noviembre de 2021,
  de 18:30 a 19:30, aula A3.10". 14 Nov 2021 was a Sunday (the post itself was published that Sunday) and every
  other talk falls on Mon 8, Wed 10, Mon 15 or Wed 17; the parser corrects it to 2021-11-15 (`date_fix`).
  The resumen slug also misnames him ("francisco-jimenez").
- "Hablemos de ciberseguridad, hablemos de framework de ciberseguridad" (Dolbuck S.L.): only the day (Mon 8 Nov,
  "la última del primer día") and the room (A2.16) are stated, no time. `starts_at` is the date only.
- "De mayor quiero ser pentester" (David Sánchez): start time 10:30 on Mon 8 Nov, no end time and no room stated.
- Two talks have two speakers: OWASP (Paula Garrido Lerma + Jesús Manuel Sánchez Alanís, students at BeOneSec) and
  Firma digital (Jesús López + Benito Galán Algora, Viafirma); `speaker` joins them with " y " and speakers.json
  has one row each sharing the announcement bio.
- Speaker names differ between announcement and resumen (Rafael Martínez / Rafael Martínez Gasca, Alberto Castro /
  Alberto Castro Ortiz, Alberto Fernández / Alberto Fernández Valiente, Francisco Ramírez / Francisco José Ramírez
  López); the fullest form is used everywhere.
- Talks were hybrid: in person at ETSII (Eventbrite ticket for US members) and streamed on Twitch for everyone else.
  `modality` is `in_person`; the Twitch channels are mentioned in the description.
- `clean_html` rewrites the Twitch links from http to https (the host contains "innosoftdays"), harmless.
- Post `date` is `article:published_time` converted from UTC to Europe/Madrid (matches the visible dd/mm/yyyy).
- Three resumen posts use h1/h2 headings inside the body; h1 is demoted to h2 in `content_html` so the post title
  stays the only h1.
- Events are sorted by `starts_at`; the edition `description_html` carries a generated programme list.
- Events with missing time or room: 2 (listed above).

## Per-year counts

| year | captures | posts | events | speakers |
|---|---|---|---|---|
| 2021 | 51 | 32 | 17 | 19 |
