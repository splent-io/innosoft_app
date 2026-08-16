# Synthesis report (data/extracted/*.json)

Produced by `parse/synthesize.py` from `data/extracted/parts/*.json` (all families, both runs). Deterministic; rerun after fixing a part.

Families merged: events_eventos_etn, events_mec, institucional, media, pages_editions, people, posts_2018_2020, posts_2021, posts_2022, posts_2023_2024.

## Coverage per year

| year | edition | events (merged / raw) | speakers | organisers | posts | pages | media |
|---|---|---|---|---|---|---|---|
| 2017 | V 2017-11-06..2017-11-09 (high) | 19 / 19 | 10 | 0 | 0 | 0 | 14 |
| 2018 | VI 2018-11-12..2018-11-16 (high) | 31 / 58 | 27 | 0 | 7 | 0 | 15 |
| 2019 | VII 2019-11-04..2019-11-06 (high) | 18 / 18 | 13 | 0 | 5 | 0 | 20 |
| 2020 | VIII 2020-11-24..2020-11-27 (high) | 22 / 43 | 14 | 0 | 5 | 1 | 30 |
| 2021 | IX 2021-11-08..2021-11-17 (high) | 34 / 84 | 23 | 0 | 32 | 1 | 6 |
| 2022 | X 2022-11-08..2022-11-11 (high) | 42 / 52 | 27 | 0 | 32 | 15 | 103 |
| 2023 | XI 2023-11-06..2023-11-09 (high) | 22 / 43 | 25 | 144 | 29 | 6 | 145 |
| 2024 | XII 2024-11-05..2024-11-08 (high) | 65 / 82 | 16 | 150 | 20 | 10 | 236 |
| 2025 | XIII 2025-11-04..2025-11-06 (high) | 28 / 28 | 9 | 0 | 0 | 4 | 480 |
| total | 9 | 281 / 427 | 155 (records: 266) | 294 | 130 | 37 | 1049 |

Event sources per year (family: raw records):

- 2017: events_mec 13, pages_editions 6
- 2018: events_mec 21, institucional 30, posts_2018_2020 7
- 2019: events_mec 17, pages_editions 1
- 2020: events_mec 18, institucional 1, pages_editions 2, posts_2018_2020 22
- 2021: events_mec 33, institucional 33, pages_editions 1, posts_2021 17
- 2022: events_mec 29, pages_editions 13, posts_2022 10
- 2023: events_mec 17, pages_editions 2, people 10, posts_2023_2024 14
- 2024: events_eventos_etn 61, events_mec 7, pages_editions 2, posts_2023_2024 12
- 2025: pages_editions 28

## Editions

One entry per year 2017 to 2025 (2017 = V is documented by the MEC event pages and /v-edicion/). Name is always `InnoSoft Days <roman>` with number = year - 2012. Dates and venue come from the highest-confidence source (edition/timetable pages, then the institucional site, then event pages, then posts); summary and description from the same order with posts before event pages. The importer only fills empty fields, so the seeded XIII (2025) edition keeps its own copy.

| year | name | dates | venue | families | confidence |
|---|---|---|---|---|---|
| 2017 | InnoSoft Days V | 2017-11-06..2017-11-09 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | events_mec, pages_editions | high |
| 2018 | InnoSoft Days VI | 2018-11-12..2018-11-16 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | events_mec, institucional, pages_editions, posts_2018_2020 | high |
| 2019 | InnoSoft Days VII | 2019-11-04..2019-11-06 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | events_mec, institucional, pages_editions, posts_2018_2020 | high |
| 2020 | InnoSoft Days VIII | 2020-11-24..2020-11-27 | Online (retransmisión por Twitch, twitch.tv/innosoftdays) | events_mec, institucional, pages_editions, posts_2018_2020 | high |
| 2021 | InnoSoft Days IX | 2021-11-08..2021-11-17 | Escuela Técnica Superior de Ingeniería Informática, Sevilla | events_mec, institucional, pages_editions, posts_2021 | high |
| 2022 | InnoSoft Days X | 2022-11-08..2022-11-11 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | events_mec, pages_editions, posts_2022 | high |
| 2023 | InnoSoft Days XI | 2023-11-06..2023-11-09 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | events_mec, pages_editions, posts_2023_2024 | high |
| 2024 | InnoSoft Days XII | 2024-11-05..2024-11-08 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Campus de  | events_eventos_etn, events_mec, pages_editions, posts_2023_2024 | high |
| 2025 | InnoSoft Days XIII | 2025-11-04..2025-11-06 | Escuela Técnica Superior de Ingeniería Informática (ETSII), Universida | pages_editions | high |

## Events

427 raw records from 9 years became 281 events; 3 container/boilerplate records dropped, 143 records merged into another record.

Clustering (per year, greedy, richest record first, a family never merges with itself): two records merge when the normalised titles match (generic prefixes such as `Conferencia –`, `Taller`, `Charla de la Sra.` removed; exact key, token subset or Jaccard >= 0.6) and the dates are compatible (same day, or one source has no date), or when the speaker is the same person on the same day (multi-speaker strings are split; a conflicting speaker blocks the merge). Same-title records with different dates only merge when the title is unique in both families for that year (a data-entry error in one source, recorded below).

Field rules: longest `description_html` wins and gives `source_url`; `starts_at`/`ends_at` by majority of the fully dated sources then family priority (Eventin/TEC 2024 > MEC > institucional > people > pages > posts; for 2021 the institucional calendar captured on 2021-11-14 beats the MEC copy); `kind` by majority of the specific kinds; `speaker` is the most complete name string, then canonicalised to the merged speaker name; `title` prefers a descriptive, non-ALL-CAPS, prefix-less title; `link` prefers live-site URLs over the dead institucional.us.es ones; `modality` online for 2020.

### Dropped records

- 2020 [events_mec] 'Innosoft Days 2020' (2020-11-24T08:30:00) https://www.innosoftdays.com/events/innosoft-2020/: container entry of the calendar, not an activity
- 2022 [events_mec] 'Innosoft Days día 3' (2022-11-10T08:00:00) https://www.innosoftdays.com/events/dia-dos-innosoft-days-2/: container entry of the calendar, not an activity
- 2022 [events_mec] 'Innosoft Days día 4' (2022-11-11T08:00:00) https://www.innosoftdays.com/events/innosoft-days-dia-3/: container entry of the calendar, not an activity

### Merges (record -> cluster seed, reason)

- 2018 [events_mec] 'Conferencia – 100B+ rows: manejando grandes cantidades de datos en el cliente' (2018-11-13T11:40:00; Alberto Asuero) -> [institucional] '100B+ rows: manejando grandes cantidades de datos en el cliente' (2018-11-13T11:40:00; Alberto Asuero) [title]
- 2018 [events_mec] 'Conferencia – Blockchain, qué es y cómo funciona' (2018-11-13T15:50:00; Diego Fernández Barrera) -> [institucional] 'Blockchain, qué es y cómo funciona' (2018-11-13T15:30:00; Diego Fernández Barrera) [title]
- 2018 [events_mec] 'Taller Clasificación de imágenes y detección de objetos con YOLO' (2018-11-13T17:30:00; -) -> [institucional] 'Clasificación de imágenes y detección de objetos con YOLO' (2018-11-13T17:30:00; Jesús Utrera y Joaquín Salguero) [title]
- 2018 [posts_2018_2020] 'Taller “Clasificación de imágenes y detección de objetos con YOLO”' (no date; Jesús Utrera, Joaquín Salguero) -> [institucional] 'Clasificación de imágenes y detección de objetos con YOLO' (2018-11-13T17:30:00; Jesús Utrera y Joaquín Salguero) [title]
- 2018 [events_mec] 'Competición de ideas open source y modelos de negocio de Bitnami' (2018-11-13T18:30:00; -) -> [posts_2018_2020] 'Competición de ideas open source y modelos de negocio de Bitnami' (2018-11-13T18:30:00; Jurado: Daniel Liszka, Pablo Trinidad, Jesús González) [title]
- 2018 [institucional] 'Competición de ideas open source y modelos de negocio de Bitnami' (2018-11-13T18:30:00; -) -> [posts_2018_2020] 'Competición de ideas open source y modelos de negocio de Bitnami' (2018-11-13T18:30:00; Jurado: Daniel Liszka, Pablo Trinidad, Jesús González) [title]
- 2018 [events_mec] 'Conferencia – De b2/cafelog a WordPress' (2018-11-13T13:50:00; Rafael Poveda) -> [institucional] 'De b2/cafelog a WordPress' (2018-11-13T13:50:00; Rafael Poveda) [title]
- 2018 [events_mec] 'Conferencia – Frontend también es diseño' (2018-11-13T10:40:00; Raúl Yeguas) -> [institucional] 'Frontend también es diseño' (2018-11-13T10:40:00; Raúl Yeguas) [title]
- 2018 [institucional] 'Gymkhana' (2018-11-13T12:40:00; -) -> [posts_2018_2020] 'Gymkhana' (no date; -) [title]
- 2018 [events_mec] 'Conferencia – Ingeniería informática: pasado, presente y futuro' (2018-11-16T10:30:00; Mónica Romero Nájera) -> [institucional] 'Ingeniería informática: pasado, presente y futuro' (2018-11-16T10:30:00; Mónica Romero Nájera) [title]
- 2018 [events_mec] 'Conferencia Introducción a Singular / Sass' (2018-11-13T15:50:00; Inmaculada Rodríguez Vizcaína) -> [institucional] 'Introducción a Sngular / Introducción a Sass' (2018-11-13T15:30:00; Inmaculada Rodríguez Vizcaína y María del Carmen García Peral) [speaker+title]
- 2018 [events_mec] 'Conferencia – La informática en el descubrimiento del escutoide' (2018-11-12T20:30:00; Clara Grima) -> [institucional] 'La informática en el descubrimiento del escutoide' (2018-11-12T20:30:00; Clara Grima) [title]
- 2018 [events_mec] 'Conferencia – Los Nuevos Retos en la Ingeniería de Software Aplicada' (2018-11-13T11:40:00; Jesús Bermejo) -> [institucional] 'Los Nuevos Retos en la Ingeniería de Software Aplicada' (2018-11-13T11:40:00; Jesús Bermejo) [title]
- 2018 [events_mec] 'Conferencia – Los estudios de Ingeniería de Software: pasado presente y futuro' (2018-11-12T19:30:00; Amador Durán) -> [institucional] 'Los estudios de Ingeniería de Software: pasado presente y futuro' (2018-11-12T19:30:00; Amador Durán y José Luis Sevillano) [title]
- 2018 [events_mec] 'Mesa redonda: el impacto de la ingeniería del software en la industria local' (2018-11-16T11:20:00; -) -> [institucional] 'Mesa redonda: el impacto de la ingeniería del software en la industria local' (2018-11-16T11:20:00; -) [title]
- 2018 [events_mec] 'Conferencia – Mujeres en ingeniería' (2018-11-12T20:30:00; Rocío Berenguel Gallardo) -> [institucional] 'Mujeres en ingeniería' (2018-11-12T20:30:00; Rocío Berenguel Gallardo) [title]
- 2018 [events_mec] 'Conferencia – OAS-Tools/Generator' (2018-11-13T13:50:00; Rafael Fresno) -> [institucional] 'OAS-Tools/Generator' (2018-11-13T13:50:00; Rafael Fresno) [title]
- 2018 [events_mec] 'Conferencia – PostgreSQL: la base de datos libre más potente del mercado' (2018-11-13T16:30:00; -) -> [institucional] 'PostgreSQL: la base de datos libre más potente del mercado' (2018-11-13T16:30:00; Emilio Pérez y José Segovia) [title]
- 2018 [events_mec] 'Proyección – Capítulo “Toda tu historia” de Black Mirror y tertulia' (2018-11-13T08:40:00; -) -> [posts_2018_2020] 'Proyección del capítulo “Toda tu historia” de Black Mirror' (no date; -) [title]
- 2018 [institucional] 'Capítulo “Toda tu historia” de Black Mirror y tertulia' (2018-11-13T08:40:00; -) -> [posts_2018_2020] 'Proyección del capítulo “Toda tu historia” de Black Mirror' (no date; -) [title]
- 2018 [events_mec] 'Conferencia – Roadmap de oportunidades tecnológicas' (2018-11-13T12:40:00; David Borrego) -> [institucional] 'Roadmap de oportunidades tecnológicas' (2018-11-13T12:40:00; David Borrego y Ana Aparicio) [title]
- 2018 [events_mec] 'Conferencia – Seguridad en entornos IoT' (2018-11-16T10:30:00; Ramón Salado) -> [institucional] 'Seguridad en entornos IoT' (2018-11-16T10:30:00; Ramón Salado) [title]
- 2018 [events_mec] 'Testing de aplicaciones en Kubernetes' (2018-11-13T08:40:00; Juan Ariza Toledano) -> [posts_2018_2020] 'Testing de aplicaciones en Kubernetes' (no date; Javier Aguadero, Carlos Rodríguez, Juan Ariza) [title]
- 2018 [institucional] 'Testing de aplicaciones en Kubernetes' (2018-11-13T08:40:00; Juan Ariza Toledano, Carlos Rodríguez Hernández, Javier Aguadero García) -> [posts_2018_2020] 'Testing de aplicaciones en Kubernetes' (no date; Javier Aguadero, Carlos Rodríguez, Juan Ariza) [title]
- 2018 [posts_2018_2020] 'Concurso de programación TOURNAMETSII' (no date; -) -> [institucional] 'Torneo de programación TOURNAMETSII' (2018-11-13T17:30:00; -) [title]
- 2018 [events_mec] 'Conferencia – Wide Wild West 2.0' (2018-11-13T10:40:00; Luis Pablo del Árbol Pérez) -> [institucional] 'Wide Wild West 2.0' (2018-11-13T10:40:00; Luis Pablo del Árbol Pérez) [title]
- 2018 [events_mec] 'Conferencia – ¿Por qué ellas no escogen carreras técnicas?' (2018-11-13T17:30:00; Inmaculada Alcón Piñero) -> [institucional] '¿Por qué ellas no escogen carreras técnicas?' (2018-11-13T17:30:00; Inmaculada Alcón Piñero) [title]
- 2020 [posts_2018_2020] 'Acto de clausura de InnoSoft Days 2020' (2020-11-27; -) -> [events_mec] 'Acto de clausura' (2020-11-27T21:40:00; Yoana Dimitrova) [title]
- 2020 [posts_2018_2020] 'Aportaciones de Investigación y Transferencia en Ciencia de Datos' (2020-11-26T11:50:00; Pepe Riquelme, Manuel Carranza) -> [events_mec] 'Aportaciones de investigación y Transferencia en ciencia de datos' (2020-11-26T11:50:00; Pepe Riquelme) [title]
- 2020 [posts_2018_2020] 'Desarrollo Impulsado por la Ingeniería del Caos' (2020-11-24; Nicolás Afonso, Alicia Melgarejo) -> [pages_editions] 'Behaviour Driven Development and Chaos Engineering' (2020-11-24T19:00:00; Nicolás Afonso Alonso) [speaker+date]
- 2020 [posts_2018_2020] 'Como hacer los equipos data science 10 veces más rápido' (2020-11-26; Federico Castanedo) -> [events_mec] 'Como hacer los equipos de Data Science 10 veces más productivo' (2020-11-26T19:00:00; Federico Castanedo Sotela) [title]
- 2020 [institucional] 'Hacia una Inteligencia Artificial Regenerativa y Redistributiva (keynote speech)' (2020-11-27T20:30:00; Verónica Dahl) -> [events_mec] 'Hacia una Inteligencia Artificial Regenerativa y Redistributiva (keynote speech)' (2020-11-27T20:30:00; Verónica Dahl) [title]
- 2020 [posts_2018_2020] 'Hacia una Inteligencia Artificial Regenerativa y Redistributiva' (2020-11-27; Verónica Dahl) -> [events_mec] 'Hacia una Inteligencia Artificial Regenerativa y Redistributiva (keynote speech)' (2020-11-27T20:30:00; Verónica Dahl) [title]
- 2020 [posts_2018_2020] 'Inauguración de InnoSoft Days 2020' (2020-11-24; -) -> [pages_editions] 'Inauguración Innososft Days 2020' (2020-11-24T09:00:00; Yoana Dimitrova) [title]
- 2020 [posts_2018_2020] 'Introducción a la Computación Cuántica' (2020-11-26T15:30:00; Rafael Corchuelo) -> [events_mec] 'Introducción a la Computación Cuántica' (2020-11-26T15:30:00; Rafael Corchuelo) [title]
- 2020 [events_mec] 'Iniciación a la clasificación de imágenes usando redes convolucionales' (2020-11-24T15:30:00; Antonio Jesús García Nieto) -> [posts_2018_2020] 'Introducción a la clasificación de imágenes utilizando redes convolucionales' (2020-11-24T15:30:00; Antonio Jesús García Nieto) [title+time]
- 2020 [posts_2018_2020] 'Introducción a soluciones open-source de “Machine Learning”' (2020-11-27; Miguel Ángel Cabrera) -> [events_mec] 'Introducción a soluciones open-source de “Machine Learning”' (2020-11-27T09:30:00; Miguel Ángel Cabrera) [title]
- 2020 [posts_2018_2020] 'Limiting Global Warning by Improving Data-Centre Software' (2020-11-26; Alejandro Fernández) -> [events_mec] 'Limiting Global Warning by Improving Data-Centre Software' (2020-11-26T10:40:00; Alejandro Fdez Montes) [title]
- 2020 [events_mec] 'Odoo, ERP con alma de framework' (2020-11-27T11:50:00; Fernando La Chica) -> [posts_2018_2020] 'Oddo, ERP con alma de framework' (2020-11-27T11:40:00; Fernando La Chica, Francisco Javier Llamas) [title]
- 2020 [posts_2018_2020] 'Presentación del día' (2020-11-26; -) -> [events_mec] 'Presentación del día' (2020-11-26T09:00:00; -) [title]
- 2020 [posts_2018_2020] 'Procesos Inteligentes en la Industria 4.0' (2020-11-26; Mayte Gómez) -> [events_mec] 'Procesos Inteligentes en la Industria 4.0' (2020-11-26T13:30:00; Mayte Gómez) [title]
- 2020 [posts_2018_2020] 'Scape Room' (2020-11-26; -) -> [events_mec] 'Scape Room' (2020-11-26T18:00:00; -) [title]
- 2020 [events_mec] 'Aprendizaje Automático con Swift' (2020-11-27T16:00:00; -) -> [posts_2018_2020] 'Taller Aprendizaje automático con Swift' (2020-11-27T16:00:00; GUMUS (Grupo de Usuarios de Macintosh de la Universidad de Sevilla)) [title]
- 2020 [events_mec] 'Taller Hackatón' (2020-11-24T15:30:00; -) -> [posts_2018_2020] 'Taller de Hackatón' (2020-11-24T15:30:00; -) [title]
- 2020 [posts_2018_2020] 'Trading algorítmico con criptomonedas' (2020-11-27; Gonzalo Fernández, Antonio García) -> [events_mec] 'Trading algorítmico con criptomonedas' (2020-11-27T18:00:00; Gonzalo Fernández de la Torre) [title]
- 2020 [posts_2018_2020] 'Universidad Empresarial: El binomio perfecto' (2020-11-24; María José Escalona) -> [events_mec] 'Universidad Empresarial: el binomio perfecto' (2020-11-24T10:40:00; Maria José Escalona) [title]
- 2020 [posts_2018_2020] '¿Quién es quién en una sociedad digital?' (2020-11-26; Mª Iluminada Baturone, Mª Rosario Arjona) -> [events_mec] '¿Quién es quién en una sociedad digital?' (2020-11-26T09:30:00; Mª Iluminada Baturone Castillo) [title]
- 2021 [events_mec] 'Ahora estoy acabando la carrera y …' (2021-11-17T10:30:00; Maria José Escalona) -> [posts_2021] 'Ahora estoy acabando la carrera y …' (2021-11-17T10:30:00; María José Escalona) [title]
- 2021 [institucional] 'Ahora estoy acabando la carrera y …' (2021-11-17T10:30:00; -) -> [posts_2021] 'Ahora estoy acabando la carrera y …' (2021-11-17T10:30:00; María José Escalona) [title]
- 2021 [events_mec] 'Becario en Ciberseguridad: cómo no morir en el intento' (2021-11-17T15:30:00; Paco Profe) -> [posts_2021] 'Becario en Ciberseguridad: como no morir en el intento' (2021-11-17T15:30:00; Francisco Pérez Fernández) [title]
- 2021 [institucional] 'Becario en Ciberseguridad: cómo no morir en el intento' (2021-11-17T15:30:00; -) -> [posts_2021] 'Becario en Ciberseguridad: como no morir en el intento' (2021-11-17T15:30:00; Francisco Pérez Fernández) [title]
- 2021 [institucional] 'Ceremonia de Apertura' (2021-11-08T08:30:00; -) -> [events_mec] 'Ceremonia de Apertura' (2021-11-08T08:30:00; -) [title]
- 2021 [institucional] 'Ceremonia de cierre' (2021-11-17T17:15:00; -) -> [events_mec] 'Ceremonia de cierre' (2021-11-17T17:15:00; -) [title]
- 2021 [institucional] 'Ciberinvestigando a los intrusos informáticos de un banco' (2021-11-08T11:30:00; -) -> [events_mec] 'Ciberinvestigando a los intrusos informáticos de un banco' (2021-11-08T11:30:00; -) [title]
- 2021 [institucional] 'Ciberseguridad en Containers y Kubernetes' (2021-11-17T08:30:00; -) -> [events_mec] 'Ciberseguridad en Containers y Kubernetes' (2021-11-17T08:30:00; Vicente Herrera) [title]
- 2021 [events_mec] 'Ciberseguridad y hacking ético' (2021-11-15T18:30:00; Francisco Ramírez) -> [posts_2021] 'Ciberseguridad y hacking ético' (2021-11-15T18:30:00; Francisco José Ramírez López) [title]
- 2021 [institucional] 'Ciberseguridad y hacking ético' (2021-11-15T18:30:00; -) -> [posts_2021] 'Ciberseguridad y hacking ético' (2021-11-15T18:30:00; Francisco José Ramírez López) [title]
- 2021 [events_mec] 'Ciberseguridad, ¿qué esperan los alumnos y donde estudiar lo que ellos esperan?' (2021-11-15T10:30:00; Angel Jesús Varela Vaca) -> [posts_2021] 'Ciberseguridad, ¿Qué esperan los alumnos y donde estudiar lo que ellos esperan?' (2021-11-15T10:30:00; Ángel Jesús Varela Vaca) [title]
- 2021 [institucional] 'Ciberseguridad, ¿qué esperan los alumnos y donde estudiar lo que ellos esperan?' (2021-11-15T10:30:00; -) -> [posts_2021] 'Ciberseguridad, ¿Qué esperan los alumnos y donde estudiar lo que ellos esperan?' (2021-11-15T10:30:00; Ángel Jesús Varela Vaca) [title]
- 2021 [events_mec] 'Ciberseguridad: Retos y necesidades' (2021-11-10T15:30:00; Francisco Valencia) -> [posts_2021] 'Ciberseguridad: Retos y necesidades' (2021-11-10T15:30:00; Francisco Valencia) [title]
- 2021 [institucional] 'Ciberseguridad: Retos y necesidades' (2021-11-10T15:30:00; -) -> [posts_2021] 'Ciberseguridad: Retos y necesidades' (2021-11-10T15:30:00; Francisco Valencia) [title]
- 2021 [institucional] 'Ciberseguridad: luchando contra el lado oscuro de la fuerza' (2021-11-17T16:15:00; -) -> [events_mec] 'Ciberseguridad: luchando contra el lado oscuro de la fuerza' (2021-11-17T16:15:00; Sergio Medina) [title]
- 2021 [events_mec] 'Comienzo en la ciberseguridad ¿Por dónde empiezo?' (2021-11-15T09:30:00; Manuel Jesús Flores Montaño) -> [posts_2021] 'Comienzo en la ciberseguridad ¿Por dónde empiezo?' (2021-11-15T09:30:00; Manuel Jesús Flores Montaño) [title]
- 2021 [institucional] 'Comienzo en la ciberseguridad ¿Por dónde empiezo?' (2021-11-15T09:30:00; -) -> [posts_2021] 'Comienzo en la ciberseguridad ¿Por dónde empiezo?' (2021-11-15T09:30:00; Manuel Jesús Flores Montaño) [title]
- 2021 [events_mec] 'De mayor quiero ser pentester' (2021-11-08T10:30:00; David Sánchez) -> [posts_2021] 'De mayor quiero ser pentester' (2021-11-08T10:30:00; David Sánchez) [title]
- 2021 [institucional] 'De mayor quiero ser pentester' (2021-11-08T10:30:00; -) -> [posts_2021] 'De mayor quiero ser pentester' (2021-11-08T10:30:00; David Sánchez) [title]
- 2021 [events_mec] 'Futuro sin contraseñas' (2021-11-10T11:30:00; Daniel Garcia) -> [posts_2021] 'El futuro sin contraseñas' (2021-11-10T11:30:00; Daniel García) [title]
- 2021 [institucional] 'Futuro sin contraseñas' (2021-11-10T11:30:00; -) -> [posts_2021] 'El futuro sin contraseñas' (2021-11-10T11:30:00; Daniel García) [title]
- 2021 [events_mec] 'Firma digital e identidad digital' (2021-11-17T11:30:00; -) -> [posts_2021] 'Firma digital e identidad digital' (2021-11-17T11:30:00; Jesús López y Benito Galán Algora) [title]
- 2021 [institucional] 'Firma digital e identidad digital' (2021-11-17T11:30:00; -) -> [posts_2021] 'Firma digital e identidad digital' (2021-11-17T11:30:00; Jesús López y Benito Galán Algora) [title]
- 2021 [events_mec] 'Hablemos de ciberseguridad, hablemos de framework de ciberseguridad' (2021-11-08T18:30:00; -) -> [posts_2021] 'Hablemos de ciberseguridad, hablemos de framework de ciberseguridad' (2021-11-08; Adrián Ramírez) [title]
- 2021 [institucional] 'Hablemos de ciberseguridad, hablemos de framework de ciberseguridad' (2021-11-08T18:30:00; -) -> [posts_2021] 'Hablemos de ciberseguridad, hablemos de framework de ciberseguridad' (2021-11-08; Adrián Ramírez) [title]
- 2021 [events_mec] 'Identificación de ciber-inseguridades' (2021-11-17T09:30:00; Rafael Martínez Gasca) -> [posts_2021] 'Identificación de ciber inseguridades' (2021-11-17T09:30:00; Rafael Martínez Gasca) [title]
- 2021 [institucional] 'Identificación de ciber-inseguridades' (2021-11-17T09:30:00; -) -> [posts_2021] 'Identificación de ciber inseguridades' (2021-11-17T09:30:00; Rafael Martínez Gasca) [title]
- 2021 [events_mec] 'Identificación y Preservación de Evidencias Digitales' (2021-11-10T10:30:00; -) -> [posts_2021] 'Identificación y preservación de evidencias digitales' (2021-11-10T10:30:00; Alberto Castro Ortiz) [title]
- 2021 [institucional] 'Identificación y Preservación de Evidencias Digitales' (2021-11-10T10:30:00; -) -> [posts_2021] 'Identificación y preservación de evidencias digitales' (2021-11-10T10:30:00; Alberto Castro Ortiz) [title]
- 2021 [events_mec] 'Introducción a OWASP y herramientas de pentesting' (2021-11-10T16:30:00; Paula Garrido Lerman y Jesús Manuel Sánchez Alanís) -> [posts_2021] 'Introducción a OWASP y herramientas de pentesting' (2021-11-10T16:30:00; Paula Garrido Lerma y Jesús Manuel Sánchez Alanís) [title]
- 2021 [institucional] 'Introducción a OWASP y herramientas de pentesting' (2021-11-10T16:30:00; -) -> [posts_2021] 'Introducción a OWASP y herramientas de pentesting' (2021-11-10T16:30:00; Paula Garrido Lerma y Jesús Manuel Sánchez Alanís) [title]
- 2021 [events_mec] 'Introducción a Computación Cuántica' (2021-11-10T16:30:00; José Martínez García) -> [posts_2021] 'Introducción a la computación cuántica' (2021-11-10T16:30:00; José Martínez García) [title]
- 2021 [institucional] 'Introducción a Computación Cuántica' (2021-11-10T16:30:00; -) -> [posts_2021] 'Introducción a la computación cuántica' (2021-11-10T16:30:00; José Martínez García) [title]
- 2021 [institucional] 'Introducción al hacking 1' (2021-11-15T08:30:00; -) -> [events_mec] 'Introducción al hacking 1' (2021-11-15T08:30:00; Antoni Cobos Domínguez) [title]
- 2021 [institucional] 'Introducción al hacking 2' (2021-11-15T09:30:00; -) -> [events_mec] 'Introducción al hacking 2' (2021-11-15T09:30:00; Antoni Cobos Domínguez) [title]
- 2021 [institucional] 'Introducción al hacking 3' (2021-11-15T10:30:00; -) -> [events_mec] 'Introducción al hacking 3' (2021-11-10T10:30:00; Antoni Cobos Domínguez) [date-conflict]
- 2021 [institucional] 'Introducción al hacking 4' (2021-11-15T11:30:00; -) -> [events_mec] 'Introducción al hacking 4' (2021-11-15T11:30:00; Antoni Cobos Domínguez) [title]
- 2021 [events_mec] 'Lo que nadie me contó durante la universidad' (2021-11-08T08:45:00; Alberto Fernández) -> [posts_2021] 'Lo que nadie me contó sobre la universidad' (2021-11-08T08:45:00; Alberto Fernández Valiente) [title]
- 2021 [institucional] 'Lo que nadie me contó durante la universidad' (2021-11-08T08:45:00; -) -> [posts_2021] 'Lo que nadie me contó sobre la universidad' (2021-11-08T08:45:00; Alberto Fernández Valiente) [title]
- 2021 [institucional] 'Programación competitiva' (2021-11-10T08:30:00; -) -> [events_mec] 'Programación competitiva' (2021-11-10T08:30:00; David Brincau Cano) [title]
- 2021 [institucional] 'Quedada musical mañana' (2021-11-08T09:30:00; -) -> [events_mec] 'Quedada musical mañana' (2021-11-08T09:30:00; -) [title]
- 2021 [institucional] 'Quedada musical tarde' (2021-11-08T17:30:00; -) -> [events_mec] 'Quedada musical tarde' (2021-11-08T17:30:00; -) [title]
- 2021 [institucional] 'Recorrido de las programadoras' (2021-11-15T17:30:00; -) -> [events_mec] 'Recorrido de las programadoras' (2021-11-15T17:30:00; -) [title]
- 2021 [institucional] 'Restos, servicios y salidas' (2021-11-17T10:30:00; -) -> [events_mec] 'Restos, servicios y salidas' (2021-11-17T10:30:00; -) [title]
- 2021 [events_mec] 'Seguridad cloud-native' (2021-11-10T11:30:00; Alba Ferri) -> [posts_2021] 'Seguridad cloud-native' (2021-11-10T11:30:00; Alba Ferri) [title]
- 2021 [institucional] 'Seguridad cloud-native' (2021-11-10T11:30:00; -) -> [posts_2021] 'Seguridad cloud-native' (2021-11-10T11:30:00; Alba Ferri) [title]
- 2021 [events_mec] 'Seguridad en los servicios en la nube' (2021-11-15T18:30:00; Andrés Marchante) -> [posts_2021] 'Seguridad en los servicios en la nube' (2021-11-15T18:30:00; Andrés Marchante Tirado) [title]
- 2021 [institucional] 'Seguridad en los servicios en la nube' (2021-11-15T18:30:00; -) -> [posts_2021] 'Seguridad en los servicios en la nube' (2021-11-15T18:30:00; Andrés Marchante Tirado) [title]
- 2021 [institucional] 'Torneo Rocket League' (2021-11-17T08:30:00; -) -> [events_mec] 'Torneo Rocket League' (2021-11-17T08:30:00; -) [title]
- 2021 [institucional] 'Torneo Rocket league' (2021-11-10T08:30:00; -) -> [events_mec] 'Torneo Rocket league' (2021-11-10T08:30:00; -) [title]
- 2022 [events_mec] 'Charla de Accenture' (2022-11-08T11:30:00; Rafael Poveda Santos, José Carlos Gómez) -> [posts_2022] 'Accenture y el uso de software libre para el desarrollo y venta de servicios asociados' (2022-11-08; Rafael Poveda, Ángeles Sánchez, Rubén Ruíz) [title]
- 2022 [events_mec] 'Charla de cláusura' (2022-11-11T11:30:00; -) -> [posts_2022] 'Acto de clausura' (2022-11-11; -) [title]
- 2022 [posts_2022] 'Torneo de ajedrez' (no date; -) -> [pages_editions] 'Ajedrez' (2022-11-10T11:30:00; -) [title]
- 2022 [posts_2022] 'Barrilada de clausura' (2022-11-11; -) -> [events_mec] 'Barrilada' (2022-11-11T12:30:00; -) [title]
- 2022 [posts_2022] 'Torneo de Brawlhalla' (no date; -) -> [events_mec] 'Brawlhalla' (2022-11-09T12:30:00; -) [title]
- 2022 [events_mec] 'Charla de SUSE' (2022-11-10T17:30:00; Daniel García Moreno) -> [posts_2022] 'OpenSUSE' (no date; Daniel García) [speaker-only]
- 2022 [events_mec] 'Charla de Red Hat' (2022-11-11T08:30:00; Fernando Fernández Mancera) -> [posts_2022] 'Software Libre en la sociedad más libre' (no date; Fernando Fernández Mancera) [title]
- 2022 [events_mec] 'Charla de NTT DATA' (2022-11-08T11:30:00; Jesús Alcaide Marín) -> [posts_2022] 'Software libre en NTT Data' (2022-11-08; Jesús Alcaide Marín) [title]
- 2023 [events_mec] 'Charla de apertura de las jornadas' (2023-11-06T12:30:00; -) -> [posts_2023_2024] 'Charla de apertura de las jornadas' (2023-11-06; -) [title]
- 2023 [events_mec] 'Producción y composición musical con Inteligencia Artificial' (2023-11-06T13:00:00; -) -> [people] 'Charla de la producción y composición musical con IA' (2023-11-06T13:00:00; José María García, Alberto Perea, Guillermo Martín) [title]
- 2023 [posts_2023_2024] 'Producción y composición musical con Inteligencia Artificial' (no date; -) -> [people] 'Charla de la producción y composición musical con IA' (2023-11-06T13:00:00; José María García, Alberto Perea, Guillermo Martín) [title]
- 2023 [people] 'El uso de Chat GPT para datos estructurados con Insinno' (2023-11-09T16:30:00; Jose María González Vázquez) -> [events_mec] 'El uso de chat GPT para datos estructurados con Insinno' (2023-11-09T16:30:00; José González) [title]
- 2023 [events_mec] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 1' (2023-11-06T15:30:00; Carlos Müller Cejas, Soraya Peceño Capilla) -> [posts_2023_2024] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 1' (2023-11-06; Isabel Arrans Vega, Matthew Bwye Lera, Soraya Peceño Capilla, Carlos Guillermo Müller Cejas) [title]
- 2023 [people] 'Explorando el futuro profesional de los nuevos ingenieros software. Parte1' (2023-11-06T15:30:00; Soraya Peceño, Carlos Müller) -> [posts_2023_2024] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 1' (2023-11-06; Isabel Arrans Vega, Matthew Bwye Lera, Soraya Peceño Capilla, Carlos Guillermo Müller Cejas) [title]
- 2023 [events_mec] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 2' (2023-11-06T18:00:00; Pablo Cala, Carlos Pérez Fernández, José Ignacio Morales Conde) -> [posts_2023_2024] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 2' (2023-11-06; Pablo Cala, Carlos Pérez, José Ignacio Morales) [title]
- 2023 [people] 'Explorando el futuro profesional de los nuevos Ingenieros de Software: Parte 2' (2023-11-06T18:00:00; Pablo Cala, Carlos Pérez, José Ignacio Morales) -> [posts_2023_2024] 'Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 2' (2023-11-06; Pablo Cala, Carlos Pérez, José Ignacio Morales) [title]
- 2023 [events_mec] 'Gymkana' (2023-11-07T10:30:00; -) -> [posts_2023_2024] 'Gymkana de Sostenibilidad' (2023-11-07T10:30:00; -) [title]
- 2023 [people] 'La IA, motor de la transformación laboral' (2023-11-09T15:30:00; Ricardo Arjona Antolin) -> [events_mec] 'La IA, motor de la transformación laboral' (2023-11-09T15:30:00; Ricardo Arjona) [title]
- 2023 [posts_2023_2024] 'La IA, motor de la transformación laboral' (no date; -) -> [events_mec] 'La IA, motor de la transformación laboral' (2023-11-09T15:30:00; Ricardo Arjona) [title]
- 2023 [people] 'Retos sociales y éticos de la IA' (2023-11-09T16:30:00; Fernando Soler Toscano) -> [events_mec] 'Retos sociales y éticos de la IA' (2023-11-09T16:30:00; Fernando Soler) [title]
- 2023 [posts_2023_2024] 'Retos sociales y éticos de la IA' (no date; -) -> [events_mec] 'Retos sociales y éticos de la IA' (2023-11-09T16:30:00; Fernando Soler) [title]
- 2023 [posts_2023_2024] 'Superando barreras de escalado en las large lenguage models (LLM)' (no date; -) -> [people] 'Superando barreras de escalado en las large lenguage models (LLM)' (2023-11-09T17:30:00; Antonio J. Domínguez) [title]
- 2023 [people] 'Taller de ciberseguridad' (2023-11-08T12:30:00; Isabel Cayrasso) -> [events_mec] 'Taller de ciberseguridad' (2023-11-08T12:30:00; Isabel Cayrasso Buzón) [title]
- 2023 [posts_2023_2024] 'Taller de Ciberseguridad' (no date; Isabel Cayrasso) -> [events_mec] 'Taller de ciberseguridad' (2023-11-08T12:30:00; Isabel Cayrasso Buzón) [title]
- 2023 [events_mec] 'Tecnología y arte' (2023-11-09T10:30:00; Rocío García Robles, Olga Albillos Castillo, Helena Hernández Acuaviva, Leila Pontiga Gaytán, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diánez, Guillermo Rodríguez) -> [posts_2023_2024] 'Tecnología y Arte' (2023-11-08; Rocío García Robles, Olga Albillo, Helena Hernández Acuaviva, Agda Carvalho, Leila Pontiga, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diáñez) [date-conflict]
- 2023 [people] 'Tecnología y arte' (2023-11-09T10:30:00; Rocío García Robles, Olga Albillos Castillo, Helena Hernández Acuaviva, Leila Pontiga Gaytán, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diánez, Guillermo Rodríguez) -> [posts_2023_2024] 'Tecnología y Arte' (2023-11-08; Rocío García Robles, Olga Albillo, Helena Hernández Acuaviva, Agda Carvalho, Leila Pontiga, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diáñez) [date-conflict+title]
- 2023 [events_mec] 'Torneo de Smash Bros' (2023-11-07T17:30:00; -) -> [posts_2023_2024] 'Torneo Smash Bros' (2023-11-07T17:30:00; -) [title]
- 2023 [people] 'Transformando la salud con inteligencia artificial' (2023-11-09T17:30:00; Carlos Luis Parra Calderón) -> [events_mec] 'Transformando la salud con inteligencia artificial' (2023-11-09T17:30:00; Carlos Luis Parra Calderón) [title]
- 2023 [posts_2023_2024] 'Transformando la salud con inteligencia artificial' (no date; -) -> [events_mec] 'Transformando la salud con inteligencia artificial' (2023-11-09T17:30:00; Carlos Luis Parra Calderón) [title]
- 2024 [events_eventos_etn] 'Ceremonia Apertura' (2024-11-06T10:40:00; -) -> [posts_2023_2024] 'Ceremonia de apertura' (2024-11-06; -) [title]
- 2024 [events_mec] 'Charla Gestión emocional – Javier Antonio Pérez' (2024-11-06T17:00:00; Javier Antonio Pérez) -> [events_eventos_etn] 'Charla Igualdad – José Antonio Pérez' (2024-11-06T17:00:00; José Antonio Pérez) [title]
- 2024 [events_mec] 'Charla Energía renovable y emprendimiento – Anabel Carmona Guitiérrez (Maxeon)' (2024-11-07T16:00:00; Anabel Carmona Guitiérrez) -> [events_eventos_etn] 'Charla Sostenibilidad – Anabel Carmona Gutiérrez' (2024-11-07T16:00:00; Anabel Carmona Gutiérrez) [title]
- 2024 [events_eventos_etn] '4i.ai: Andrés y Adolfo' (no date; Andrés y Adolfo) -> [posts_2023_2024] 'Charla de 4i.ai' (2024-11-05; -) [title]
- 2024 [events_eventos_etn] 'Charla Emprendimiento – Ignasi Labastida i Juan' (2024-11-06T11:00:00; Ignasi Labastida i Juan) -> [posts_2023_2024] 'Charla de Ignasi Labastida' (2024-11-06; Ignasi Labastida) [title]
- 2024 [events_mec] 'Charla Emprendimiento – Ignasi Labastida i Juan' (2024-11-06T16:00:00; Ignasi Labastida i Juan) -> [posts_2023_2024] 'Charla de Ignasi Labastida' (2024-11-06; Ignasi Labastida) [title]
- 2024 [events_eventos_etn] 'Irene M Morgado' (no date; Irene M Morgado) -> [posts_2023_2024] 'Charla de Irene Morgado' (2024-11-05; Irene Morgado) [title]
- 2024 [events_eventos_etn] 'Charla Sostenibilidad – Rafael M Guitart' (2024-11-06T12:00:00; Rafael M Guitart) -> [posts_2023_2024] 'Charla de Rafael Guitart' (2024-11-06; Rafael Guitart) [title]
- 2024 [events_mec] 'Charla Sostenibilidad – Rafael M Guitart' (2024-11-06T12:00:00; Rafael M Guitart) -> [posts_2023_2024] 'Charla de Rafael Guitart' (2024-11-06; Rafael Guitart) [title]
- 2024 [events_eventos_etn] 'Charla Laboral – Raúl López García' (2024-11-06T09:00:00; Raúl López García) -> [posts_2023_2024] 'Charla de Raúl López' (2024-11-06; Raúl López) [title]
- 2024 [events_mec] 'Charla NTT Data – Raúl López García' (2024-11-06T09:00:00; Raúl López García) -> [posts_2023_2024] 'Charla de Raúl López' (2024-11-06; Raúl López) [title]
- 2024 [events_eventos_etn] 'Jose Luis Fontenla y María Mendoza' (2024-11-05T12:40:00; José Luis Fontenla y María Mendoza) -> [posts_2023_2024] 'Charla de Rewoox' (2024-11-05; -) [title]
- 2024 [events_mec] 'Charla Emprendimiento – Javier María de Domingo' (2024-11-07T10:30:00; Javier María de Domingo) -> [events_eventos_etn] 'Emprendimiento: Javier María de Domingo Morales' (2024-11-07T10:30:00; Javier María de Domingo Morales) [title]
- 2024 [events_eventos_etn] 'Torneo CS2 (Final)' (no date; -) -> [pages_editions] 'Final Torneo CS2' (2024-11-06T13:30:00; -) [title]
- 2024 [events_eventos_etn] 'Taller de Cibers Virus' (2024-11-06T16:00:00; -) -> [posts_2023_2024] 'Taller de cibervirus' (2024-11-06; -) [title]
- 2024 [events_mec] 'Charla Proyecto de investigación – Pablo y Alberto' (2024-11-07T11:00:00; Pablo y Alberto) -> [events_eventos_etn] 'VOLUM: Pablo Pérez y Alberto Olmo' (2024-11-07T09:30:00; Pablo Pérez y Alberto Olmo) [title]
- 2024 [posts_2023_2024] 'Yincana' (2024-11-05; -) -> [events_eventos_etn] 'Yincana inauguración Innosoft Days' (2024-11-05T10:30:00; -) [title]

110 events combine 2+ families; 171 come from a single family.

### Speaker strings canonicalised on events

- 2017: 'Mª Carmen Romero' -> 'María del Carmen Romero Ternero'
- 2018: 'Clara Grima' -> 'Clara Isabel Grima Ruiz'
- 2018: 'Rafael Poveda' -> 'Rafael Poveda Santos'
- 2020: 'Maria José Escalona' -> 'María José Escalona Cuaresma'
- 2020: 'Mª Iluminada Baturone, Mª Rosario Arjona' -> 'Mª Iluminada Baturone Castillo, Mª Rosario Arjona'
- 2020: 'Nicolás Afonso, Alicia Melgarejo' -> 'Nicolás Afonso Alonso, Alicia Melgarejo'
- 2021: 'Angel Jesús Varela Vaca' -> 'Ángel Jesús Varela Vaca'
- 2021: 'Daniel Garcia' -> 'Daniel García'
- 2021: 'Maria José Escalona' -> 'María José Escalona Cuaresma'
- 2021: 'Paula Garrido Lerman y Jesús Manuel Sánchez Alanís' -> 'Paula Garrido Lerma y Jesús Manuel Sánchez Alanís'
- 2022: 'Carlos Pérez' -> 'Carlos Pérez Fernández'
- 2022: 'Clara Grima Ruiz' -> 'Clara Isabel Grima Ruiz'
- 2022: 'Israel Blancas Álvares' -> 'Israel Blancas Álvarez'
- 2022: 'María José Escalona' -> 'María José Escalona Cuaresma'
- 2023: 'Rocío García Robles, Olga Albillos Castillo, Helena Hernández Acuaviva, Leila Pontiga Gaytán, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diánez, Guillermo Rodríguez' -> 'Rocío García Robles, Olga Albillos Castillo, Helena Hernández Acuaviva, Leila Pontiga Gaytán, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diáñez, Guillermo Rodríguez'

### Titles corrected with the canonical speaker/company spelling

- 2022: 'Charla de CoverMananger' -> 'Charla de CoverManager'
- 2024: 'Charla Energía renovable y emprendimiento – Anabel Carmona Guitiérrez (Maxeon)' -> 'Charla Energía renovable y emprendimiento – Anabel Carmona Gutiérrez (Maxeon)'

## Speakers

266 records -> 155 speakers. Names are matched accent/case-insensitively with subset matching (`Clara Grima` = `Clara Isabel Grima Ruiz`) and one-typo tolerance on 5+ letter tokens; the merge is blocked when the affiliations are incompatible. Aliases applied: `anabel carmona guitierrez` -> `Anabel Carmona Gutiérrez`; `carlos perez` -> `Carlos Pérez`; `israel blancas alvares` -> `Israel Blancas Álvarez`; `javier antonio perez` -> `José Antonio Pérez`; `pablo alberto` -> `Pablo Pérez y Alberto Olmo`; `paco profe` -> `Francisco Pérez Fernández`; `paula garrido lerman` -> `Paula Garrido Lerma`. Dropped records (not a person): andres adolfo. Merged name = the most complete spelling; affiliation/position = the longest; bio = the longest; photo by family priority (people, Eventin, posts...); links unioned; edition_years unioned.

### Merged speakers (2+ spellings or families)

- Alba Ferri (2021): Alba Ferri [events_mec, posts_2021] | Sysdig
- Alberto Asuero (2018): Alberto Asuero [events_mec, institucional]
- Alberto Fernández Valiente (2021): Alberto Fernández, Alberto Fernández Valiente [events_mec, posts_2021]
- Alberto Olmo (2024): Alberto Olmo [events_eventos_etn, people] | Universidad de Sevilla
- Amador Durán (2018): Amador Durán [events_mec, institucional]
- Ana Rosa González Diáñez (2023): Ana Rosa González Diánez, Ana Rosa González Diáñez [events_mec, people, posts_2023_2024]
- Anabel Carmona Gutiérrez (2024): Anabel Carmona Gutiérrez [events_eventos_etn, events_mec, people] | Maxeon Solar Technologies
- Andrés Marchante Tirado (2021): Andrés Marchante, Andrés Marchante Tirado [events_mec, posts_2021] | Dell
- Ángel Jesús Varela Vaca (2021): Angel Jesús Varela Vaca, Ángel Jesús Varela Vaca [events_mec, posts_2021] | Universidad de Sevilla
- Antonio Castillo (2022): Antonio Castillo [events_mec, people] | Deloitte
- Carlos Guillermo Müller Cejas (2023): Carlos Guillermo Müller Cejas, Carlos Müller, Carlos Müller Cejas [events_mec, people, posts_2023_2024] | Universidad de Sevilla
- Carlos Luis Parra Calderón (2023): Carlos Luis Parra Calderón [events_mec, people] | Hospital Universitario Virgen del Rocío
- Carlos Pérez Fernández (2022, 2023): Carlos Pérez, Carlos Pérez Fernández [events_mec, people, posts_2023_2024] | CoverManager
- Clara Isabel Grima Ruiz (2018, 2022): Clara Grima, Clara Grima Ruiz, Clara Isabel Grima Ruiz [events_mec, institucional, people, posts_2022] | Universidad de Sevilla
- Daniel García (2021, 2022): Daniel Garcia, Daniel García [events_mec, people, posts_2021] | PRiSE
- Daniel García Moreno (2022): Daniel García, Daniel García Moreno [events_mec, posts_2022] | OpenSUSE
- David Borrego (2018): David Borrego [events_mec, institucional] | atSistemas
- David Sánchez (2021): David Sánchez [events_mec, posts_2021] | Sputnik Ciberseguridad
- Diego Fernández Barrera (2018): Diego Fernández Barrera [events_mec, institucional]
- Fernando Fernández Mancera (2022): Fernando Fernández Mancera [events_mec, people, posts_2022] | Red Hat
- Fernando Soler Toscano (2023): Fernando Soler, Fernando Soler Toscano [events_mec, people]
- Francisco José Ramírez López (2021): Francisco José Ramírez López, Francisco Ramírez [events_mec, posts_2021] | Deloitte
- Francisco Pérez Fernández (2021): Francisco Pérez Fernández [events_mec, posts_2021] | NTT DATA
- Francisco Valencia (2021): Francisco Valencia [events_mec, posts_2021] | Secure&IT
- Guillermo Rodríguez (2023): Guillermo Rodríguez [events_mec, people]
- Helena Hernández Acuaviva (2023): Helena Hernández Acuaviva [events_mec, people, posts_2023_2024]
- Ignasi Labastida i Juan (2024): Ignasi Labastida, Ignasi Labastida i Juan [events_eventos_etn, events_mec, posts_2023_2024] | Creative Commons España / SPARC Europe
- Inmaculada Alcón Piñero (2018): Inmaculada Alcón Piñero [events_mec, institucional]
- Inmaculada Rodríguez Vizcaína (2018): Inmaculada Rodríguez Vizcaína [events_mec, institucional]
- Irene M Morgado (2024): Irene M Morgado, Irene Morgado [events_eventos_etn, people, posts_2023_2024]
- Irene Ugolini Sánchez-Barroso (2023): Irene Ugolini Sánchez-Barroso [events_mec, people, posts_2023_2024]
- Isabel Cayrasso Buzón (2023): Isabel Cayrasso, Isabel Cayrasso Buzón [events_mec, people, posts_2023_2024] | GeseRisk
- Israel Blancas Álvarez (2022): Israel Blancas Álvarez [events_mec, people] | Red Hat
- Javier Haro (2022): Javier Haro [events_mec, people] | Tragsatec
- Javier María de Domingo Morales (2024): Javier María de Domingo, Javier María de Domingo Morales [events_eventos_etn, events_mec, people]
- Jesús Alcaide Marín (2022): Jesús Alcaide Marín [events_mec, people, posts_2022] | NTT DATA
- Jesús Bermejo (2018): Jesús Bermejo [events_mec, institucional]
- Jesús Bocanegra (2022): Jesús Bocanegra [events_mec, people] | Libnamic
- Jesús Manuel Sánchez Alanís (2021): Jesús Manuel Sánchez Alanís [events_mec, posts_2021] | BeOneSec
- José Antonio Pérez (2024): Jose Antonio Pérez, José Antonio Pérez [events_eventos_etn, events_mec, people]
- José Carlos Gómez (2022): José Carlos Gómez [events_mec, people] | Accenture
- José Ignacio Morales Conde (2023): José Ignacio Morales, José Ignacio Morales Conde [events_mec, people, posts_2023_2024]
- José Luis Fontenla (2024): Jose Luis Fontenla, José Luis Fontenla [events_eventos_etn, people] | Rewoox
- Jose María González Vázquez (2023): Jose María González Vázquez, José González [events_mec, people] | Insinno
- José Martínez García (2021): José Martínez García [events_mec, posts_2021]
- Juan Ariza Toledano (2018, 2019): Juan Ariza Toledano [events_mec, institucional] | Bitnami
- Leila Pontiga Gaytán (2023): Leila Pontiga, Leila Pontiga Gaytán [events_mec, people, posts_2023_2024]
- Luis Pablo del Árbol Pérez (2018): Luis Pablo del Árbol Pérez [events_mec, institucional]
- Manuel Jesús Flores Montaño (2021, 2022): Manuel Jesús Flores Montaño [events_mec, people, posts_2021, posts_2022] | Universidad Pablo de Olavide
- María del Carmen Romero Ternero (2017, 2022): María del Carmen Romero Ternero, Mª Carmen Romero [events_mec, people, posts_2022] | Universidad de Sevilla
- María José Escalona Cuaresma (2020, 2021, 2022): Maria José Escalona, María José Escalona, María José Escalona Cuaresma [events_mec, people, posts_2021, posts_2022] | Universidad de Sevilla
- María Mendoza (2024): María Mendoza [events_eventos_etn, people] | Rewoox
- María Teresa Gómez López (2022): María Teresa Gómez López [events_mec, people, posts_2022] | Universidad de Sevilla
- Mónica Romero Nájera (2018): Mónica Romero Nájera [events_mec, institucional]
- Olga Albillos Castillo (2023): Olga Albillo, Olga Albillos Castillo [events_mec, people, posts_2023_2024]
- Pablo Cala (2023): Pablo Cala [events_mec, people, posts_2023_2024] | MCCM Innovations
- Pablo Pérez (2024): Pablo Pérez [events_eventos_etn, people] | Universidad de Sevilla
- Paula Garrido Lerma (2021): Paula Garrido Lerma [events_mec, posts_2021] | BeOneSec
- Rafael Fresno (2018): Rafael Fresno [events_mec, institucional]
- Rafael M Guitart (2024): Rafael Guitart, Rafael M Guitart [events_eventos_etn, events_mec, people, posts_2023_2024]
- Rafael Martínez Gasca (2021): Rafael Martínez Gasca [events_mec, posts_2021] | Universidad de Sevilla
- Rafael Poveda Santos (2018, 2022): Rafael Poveda, Rafael Poveda Santos [events_mec, institucional, people, posts_2022] | Accenture
- Ramón Salado (2018): Ramón Salado [events_mec, institucional]
- Raúl López García (2024): Raul López García, Raúl López, Raúl López García [events_eventos_etn, events_mec, people, posts_2023_2024] | NTT Data
- Raúl Yeguas (2018): Raúl Yeguas [events_mec, institucional]
- Ricardo Arjona Antolin (2023): Ricardo Arjona, Ricardo Arjona Antolin [events_mec, people] | EC2CE
- Rocío Berenguel Gallardo (2018): Rocío Berenguel Gallardo [events_mec, institucional]
- Rocío García Robles (2023): Rocío García Robles [events_mec, people, posts_2023_2024] | Universidad de Sevilla
- Sancho Lerena (2022): Sancho Lerena [events_mec, people] | Ártica (Pandora FMS)
- Soraya Peceño Capilla (2023): Soraya Peceño, Soraya Peceño Capilla [events_mec, people, posts_2023_2024]
- Verónica Dahl (2020): Verónica Dahl [events_mec, institucional]

### Speakers kept apart although the names overlap

- 'Daniel García' (PRiSE; [2021, 2022]) vs 'Daniel García Moreno' (OpenSUSE; [2022]): affiliations incompatible

### Event speakers without a speaker record (11)

Names that only appear in an event's `speaker` field with no speaker record under that exact name (for a first name plus a very common surname a longer-name record is not assumed to be the same person: 'Antonio García' of the 2020 trading talk is not 'Antonio Jesús García Nieto'); the importer keeps them as free text on the event.

- 2018: Daniel Liszka
- 2018: Jesús González
- 2018: Pablo Trinidad
- 2020: Alicia Melgarejo
- 2020: Antonio García
- 2020: Daniel Arteaga
- 2020: Francisco Javier Llamas
- 2020: Gonzalo Fernández
- 2020: Jorge Avendaño
- 2020: Mª Rosario Arjona
- 2020: Sergio Martín

## Organisers, posts, pages, media

- organisers: 294 people (2023: 144, 2024: 150), from the people family only (XI and XII organisation pages); deduped per (year, name), roles joined with ' / '.
- posts: 130 (2018: 7, 2019: 5, 2020: 5, 2021: 32, 2022: 32, 2023: 29, 2024: 20); deduped by slug, no slug appeared twice. posts_2025 contributed nothing (151 spam captures and the default 'Hola, mundo' post of the rebuilt 2025 site).
- pages: 37, all from pages_editions, deduped by (url, edition_year) so a page captured in two years (/como-llegar/ 2023 and 2024) keeps both versions; README fields only (source timestamps stay in the part).
- media: 1049 images from 1927 part records; grouped by image (size variants `-WxH`, `-scaled` and the institucional.us.es/innosoft host collapse into one entry whose url is the media family's canonical one: fetched original > largest fetched variant > largest referenced); 867 entries had 2+ records; kinds: {'logo': 46, 'photo': 704, 'poster': 233, 'other': 66}. External images (imgur, bitnami.com, ...) from the institucional family are kept as their own entries.

## Conflicts resolved (22)

- 2018 'Competición de ideas open source y modelos de negocio de Bitnami': kept 2018-11-13T18:30:00..2018-11-13T19:30:00 (institucional); other sources said events_mec: 2018-11-13T18:30:00..2018-11-13T19:00:00
- 2018 'Testing de aplicaciones en Kubernetes': kind workshop chosen among posts_2018_2020=workshop, institucional=workshop, events_mec=talk
- 2018 'Introducción a Sngular / Introducción a Sass': kept 2018-11-13T15:50:00..2018-11-13T16:20:00 (events_mec); other sources said institucional: 2018-11-13T15:30:00..2018-11-13T16:20:00
- 2018 'Blockchain, qué es y cómo funciona': kept 2018-11-13T15:50:00..2018-11-13T16:20:00 (events_mec); other sources said institucional: 2018-11-13T15:30:00..2018-11-13T17:20:00
- 2018 'Clasificación de imágenes y detección de objetos con YOLO': kept 2018-11-13T17:30:00..2018-11-13T18:20:00 (events_mec); other sources said institucional: 2018-11-13T17:30:00..2018-11-13T19:00:00
- 2018 'Gymkhana': kind competition chosen among posts_2018_2020=social, institucional=competition (title suggests competition)
- 2020 'Aprendizaje Automático con Swift': kind workshop chosen among posts_2018_2020=workshop, events_mec=talk (title suggests workshop)
- 2020 'Odoo, ERP con alma de framework': kept 2020-11-27T11:50:00..2020-11-27T12:50:00 (events_mec); other sources said posts_2018_2020: 2020-11-27T11:40:00..?
- 2020 'Taller Hackatón': kind workshop chosen among posts_2018_2020=competition, events_mec=workshop (title suggests workshop)
- 2020 'Scape Room': kind competition chosen among events_mec=competition, posts_2018_2020=social (title suggests competition)
- 2021 'Introducción al hacking 1': kind talk chosen among events_mec=talk, institucional=workshop
- 2021 'Introducción al hacking 2': kind talk chosen among events_mec=talk, institucional=workshop
- 2021 'Introducción al hacking 3': kept 2021-11-15T10:30:00..2021-11-15T11:30:00 (institucional); other sources said events_mec: 2021-11-10T10:30:00..2021-11-10T11:30:00
- 2021 'Introducción al hacking 3': kind talk chosen among events_mec=talk, institucional=workshop
- 2021 'Introducción al hacking 4': kind talk chosen among events_mec=talk, institucional=workshop
- 2023 'Gymkana de Sostenibilidad': kept 2023-11-07T10:30:00..2023-11-07T12:00:00 (events_mec); other sources said posts_2023_2024: 2023-11-07T10:30:00..2023-11-07T12:30:00
- 2024 'Charla Laboral – Raúl López García': kept 2024-11-06T09:00:00..2024-11-06T09:40:00 (events_eventos_etn); other sources said events_mec: 2024-11-06T09:00:00..2024-11-06T10:30:00
- 2024 'Charla Emprendimiento – Ignasi Labastida i Juan': kept 2024-11-06T11:00:00..2024-11-06T12:00:00 (events_eventos_etn); other sources said events_mec: 2024-11-06T16:00:00..2024-11-06T17:00:00
- 2024 'VOLUM: Pablo Pérez y Alberto Olmo': kept 2024-11-07T09:30:00..2024-11-07T10:30:00 (events_eventos_etn); other sources said events_mec: 2024-11-07T11:00:00..2024-11-07T12:00:00
- edition 2023 ends_on: kept 2023-11-09 (pages_editions); posts_2023_2024 said 2023-11-08
- edition 2024 starts_on: kept 2024-11-05 (pages_editions); events_mec said 2024-11-06
- edition 2024 ends_on: kept 2024-11-08 (pages_editions); events_mec said 2024-11-07

## Gaps and open questions

- 2013-2016 (editions I to IV) have no capture at all: the archive holds nothing before the 2017 MEC event pages; only the editions 2017-2025 are produced.
- 2017 (V): only calendar slots (title, time, room, some speakers) from the MEC pages and /v-edicion/; no descriptions, posters or posts.
- 2019 (VII): programme from the MEC pages (ALL CAPS titles kept verbatim) and five blog articles; no speaker bios or posters (2019 poster is an imgur URL).
- 2021 (IX): institucional links point at the dead institucional.us.es site; the MEC copy on innosoftdays.com is preferred where both exist. The /ponentes-ix-edicion/ page and the 2021 organisation were never captured.
- 2022 (X): speaker pages hold only infographic card images (positions/bios missing for 15 speakers); the poster text of Sancho Lerena is hand-transcribed in the parser.
- 2023 (XI): the XI table gives times and rooms; several speakers only have the talk poster as bio.
- 2024 (XII): three plugins published the same programme; TEC/ETN times were preferred over the stale MEC copies (Ignasi Labastida 11:00 vs 16:00, VOLUM 09:30 vs 11:00). Four listing stubs (4i.ai, Irene M Morgado, Mentoría Turno Mañana, Torneo CS2 Final) keep a source_url that was never captured. Umbrella stands/mentoring blocks coexist with per-day slots by design.
- 2025 (XIII): only the Elementor site (schedule, speakers, photo galleries); the product already seeds this edition, the importer only fills empty fields. 508 of the 2025 media URLs (metaslider crops) are not in the raw uploads.
- posts: 2025 has no genuine post; /category/noticias/ (institucional, 2021) was never fetched.
- media: 986 of the 1039 images have no captured variant in the CDX index (see parts/media.notes.md appendix for a second fetch pass); the importer drops images it cannot resolve.
- speakers: names only present on events (list above) have no bio/affiliation; the 'Daniel García' of 2021/2022 (PRiSE) and 'Daniel García Moreno' (SUSE/openSUSE) are kept as two people; 'Carlos Pérez' (CoverManager 2022 and entrepreneur 2023) is one person as the people family decided.
- date-only `starts_at` values (posts that give the day but not the hour) are kept as `YYYY-MM-DD`; the importer parses them as midnight.
- kind `other` covers web games (crosswords, wordle, hangman), screenings and receptions; the importer maps it to talk.
- registration_url values are historical and dead (institucional.us.es/innosoft/inscripciones/ for 2020, /en/tickets-store/ for 2024); kept as extracted, the importer may prefer to skip them.
- speaker 'Mª Carmen Romero' (2017 talk on the security policy of the Universidad de Sevilla) was merged into 'María del Carmen Romero Ternero' (ETSII director, 2022) through the Mª = María normalisation: plausible (same ETSII professor) but not confirmed by any capture.
- 'Yoana Dimitrova' (Presidenta InnoSoft 2020) is the MEC organiser of the 2020 opening/closing ceremonies and comes through as a speaker record; the product may want her under organisation instead.
- 2022: the posts say the gymkhana ran on 10 Nov 15:30 while the MEC calendar has 'Gymkhana 1' (8 Nov) and 'Gymkhana 2' (9 Nov); the three records are kept apart. 2020: 'Presentación del día' of 27 Nov is date-only (posts) while the 26 Nov one has MEC times.
- 2018: end times of the institucional timetable are geometric (row spans) and differ from the MEC per-event times for Blockchain, Sngular/Sass, YOLO and the Bitnami competition; MEC won on priority except where a third source agreed with institucional (Bitnami 19:30).
- Duplicated activities by design (different granularity, all kept): 2024 TEC umbrellas 'Stand Sostenibilidad' / 'Stand Igualdad' / 'Photocall' vs the per-day ETN stands, TEC 'Mentoría' vs the per-turn slots, morning/afternoon 'Yincana Inauguración' turns; 2023 two 'CTF prueba presencial' sessions; 2025 two Escape Room / Game Jam / RogueLikes slots.
