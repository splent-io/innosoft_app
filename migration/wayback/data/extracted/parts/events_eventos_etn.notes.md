# events_eventos_etn

Two 2024 event plugins on innosoftdays.com (Astra theme), both describing InnoSoft Days XII (5-8 Nov 2024) plus the follow-up seminars (Nov/Dec 2024).

- `/event/<slug>/` = The Events Calendar (tribe): dated schedule, categories, posters as featured image, venue = ETSII. Body class `single-tribe_events`.
- `/eventos/<slug>/` = Eventin (etn_*): rooms, 12h times, speaker photo as featured image, longer descriptions, posters inside the body. Body class `single-etn`.
- `/etn_category/<slug>/` = Eventin archive listings (ponente, taller, torneo): title, excerpt, image, link. Used as stubs for the `/eventos/` pages that were never fetched.
- `/etn_category-N/` and `/mec-category/<year>/` = empty archives ("Etn Category" / "¡No hay eventos!").

## Coverage

- Captures in scope: 116 = 53 /event/ (36 URLs) + 35 /eventos/ (33 URLs) + 4 /etn_category/ listings (3 URLs) + 24 empty category archives.
- Events written: 61 (all edition_year 2024). Speakers: 16. Media: 39. Editions: 1 (2024, XII).
- Listing-only stubs (no single page captured, undated unless merged): 13: 4i-ai-andres-y-adolfo, irene-m-morgado, jose-antonio-perez, mentoria-turno-manana-3, pensamiento-computacional, rafael-m-guitart, sol-y-ciberseguridad-anabel-carmona-gutierrez, toneo-lol-final, torneo-cs2-final, torneo-pokemon-showdown, torneo-pokemon-showdown-final, torneo-rocket-league, yincana-turno-tarde.
- Every URL with several captures (2024 vs 2025 versions) describes the same 2024 event; the latest capture is used, so no event is duplicated across versions.

## Merge of the two plugins

Both plugins published the same activities. ETN records were merged into their TEC counterpart with an explicit slug map (matched by person, date and start time). Merged event: title = TEC (typos fixed: Cibersegurirdad, Iguldad) unless the ETN title has a topic prefix; date/time/room from ETN (later, room-level) unless the ETN date differs from TEC; description = ETN plus TEC when it adds text; poster = TEC featured image, else the ETN body poster; source_url = TEC page. Secondary (ETN) URL per merged event:

| event | TEC source_url | ETN url merged in |
|---|---|---|
| Yincana inauguración Innosoft Days | https://www.innosoftdays.com/event/yincana-inauguracion-innosoft-days/ | https://www.innosoftdays.com/eventos/yincana-turno-manana/ |
| Torneo CS2 (primera ronda) | https://www.innosoftdays.com/event/torneo-cs2-primera-ronda/ | https://www.innosoftdays.com/eventos/torneo-cs2-cuartos-y-semis/ |
| Yincana Inauguración Innosoft Days | https://www.innosoftdays.com/event/yincana-inauguracion-innosoft-days-2/ | https://www.innosoftdays.com/eventos/yincana-turno-tarde/ (listing stub) |
| Torneo LOL (primera ronda) | https://www.innosoftdays.com/event/torneo-lol-primera-ronda/ | https://www.innosoftdays.com/eventos/torneo-lol-cuartos-y-semis/ |
| Charla Laboral – Raúl López García | https://www.innosoftdays.com/event/charla-laboral-raul-lopez-garcia/ | https://www.innosoftdays.com/eventos/raul-lopez-garcia/ |
| Charla Emprendimiento – Ignasi Labastida i Juan | https://www.innosoftdays.com/event/charla-emprendimiento-ignasi-labastida-i-juan/ | https://www.innosoftdays.com/eventos/ignasi-labastida-i-juan/ |
| Charla Sostenibilidad – Rafael M Guitart | https://www.innosoftdays.com/event/charla-sostenibilidad-rafael-m-guitart/ | https://www.innosoftdays.com/eventos/rafael-m-guitart/ (listing stub) |
| Charla Igualdad – José Antonio Pérez | https://www.innosoftdays.com/event/charla-iguldad-jose-antonio-perez/ | https://www.innosoftdays.com/eventos/jose-antonio-perez/ (listing stub) |
| Final Torneo LOL | https://www.innosoftdays.com/event/final-torneo-lol/ | https://www.innosoftdays.com/eventos/toneo-lol-final/ (listing stub) |
| VOLUM: Pablo Pérez y Alberto Olmo | https://www.innosoftdays.com/event/charla-investigacion-pablo-perez-y-alberto-olmo/ | https://www.innosoftdays.com/eventos/volum-pablo-perez-y-alberto-olmo/ |
| Emprendimiento: Javier María de Domingo Morales | https://www.innosoftdays.com/event/charla-emprendimiento-javier-maria-de-domingo/ | https://www.innosoftdays.com/eventos/emprendimiento-javier-maria-de-domingo-morales/ |
| Taller de Introducción a la Ciberseguridad | https://www.innosoftdays.com/event/taller-de-introduccion-a-la-cibersegurirdad/ | https://www.innosoftdays.com/eventos/introduccion-a-la-ciberseguridad/ |
| Torneo Rocket League | https://www.innosoftdays.com/event/torneo-rocket-league/ | https://www.innosoftdays.com/eventos/torneo-rocket-league/ (listing stub) |
| Taller Pensamiento Computacional | https://www.innosoftdays.com/event/taller-pensamiento-computacional/ | https://www.innosoftdays.com/eventos/pensamiento-computacional/ (listing stub) |
| Charla Sostenibilidad – Anabel Carmona Gutiérrez | https://www.innosoftdays.com/event/charla-sostenibilidad-anabel-carmona-gutierrez/ | https://www.innosoftdays.com/eventos/sol-y-ciberseguridad-anabel-carmona-gutierrez/ (listing stub) |
| Torneo Pokémon Showdown | https://www.innosoftdays.com/event/torneo-pokemon-showdown/ | https://www.innosoftdays.com/eventos/torneo-pokemon-showdown/ (listing stub) |
| Conectando personas y empresas a través de valores: Carlos Sanchís Pedregosa | https://www.innosoftdays.com/event/charla-emprendimiento-carlos-sanchis-pedregosa/ | https://www.innosoftdays.com/eventos/conectando-personas-y-empresas-a-traves-de-valores-carlos-sanchis-pedregosa/ |
| RRHH: NttData | https://www.innosoftdays.com/event/charla-laboral-rrhh-nttdata/ | https://www.innosoftdays.com/eventos/rrhh-nttdata/ |
| Charla Inteligencia Artificial – David López Carrascal y Juan Antonio Cabeza Sousa | https://www.innosoftdays.com/event/charla-inteligencia-artificial-david-lopez-carrascal-y-juan-antonio-cabeza-sousa/ | https://www.innosoftdays.com/eventos/david-lopez-carrascal-y-juan-antonio-cabeza-sousa/ |
| Final Torneo Pokémon Showdown | https://www.innosoftdays.com/event/final-torneo-pokemon-showdown/ | https://www.innosoftdays.com/eventos/torneo-pokemon-showdown-final/ (listing stub) |
| Ceremonia Clausura | https://www.innosoftdays.com/event/ceremonia-clausura/ | https://www.innosoftdays.com/eventos/ceremonia-de-clausura/ |

Time conflicts between the plugins (ETN kept when same day, it was edited later and carries the room):

- Charla Laboral – Raúl López García: TEC 2024-11-06T09:00..2024-11-06T10:30 vs ETN 2024-11-06T09:00..2024-11-06T09:40 -> kept 2024-11-06T09:00..2024-11-06T09:40
- Charla Emprendimiento – Ignasi Labastida i Juan: TEC 2024-11-06T16:00..2024-11-06T17:00 vs ETN 2024-11-06T11:00..2024-11-06T12:00 -> kept 2024-11-06T11:00..2024-11-06T12:00
- RRHH: NttData: TEC 2024-11-08T09:00..2024-11-08T11:20 vs ETN 2024-11-08T09:00..2024-11-08T10:20 -> kept 2024-11-08T09:00..2024-11-08T10:20
- Ceremonia Clausura: TEC 2024-11-08T14:30..2024-11-08T17:00 vs ETN 2024-11-08T14:30..2024-11-08T16:00 -> kept 2024-11-08T14:30..2024-11-08T16:00

Not merged on purpose (different granularity, both kept): TEC multi-day umbrellas `Stand Sostenibilidad` / `Stand Igualdad` (5-8 Nov) vs ETN per-day `Stand de Sostenibilidad|Igualdad|Finanzas DD/11`; TEC `Mentoría` (6-8 Nov) vs ETN `Mentoría Turno Mañana/Tarde` slots. `Torneo CS2 (Final)` (ETN listing) has no TEC page.

## Per year

- 2024: 61 events, kinds ceremony=2, competition=11, mentoring=5, social=6, stand=11, talk=14, workshop=12

## Skipped captures

Older captures of a URL that has a newer one (same 2024 event, the 2025 version only adds "Este evento ha pasado" and the year in the date):

- 20241108142021 https://www.innosoftdays.com/event/charla-ciberseguridad-pablo-pino/ (superseded by 20250213184043)
- 20241110143056 https://www.innosoftdays.com/event/charla-iguldad-jose-antonio-perez/ (superseded by 20250213183548)
- 20241108141030 https://www.innosoftdays.com/event/charla-inteligencia-artificial-david-lopez-carrascal-y-juan-antonio-cabeza-sousa/ (superseded by 20250214042239)
- 20241110155603 https://www.innosoftdays.com/event/charla-investigacion-pablo-perez-y-alberto-olmo/ (superseded by 20250122215745)
- 20241110152353 https://www.innosoftdays.com/event/charla-laboral-rrhh-nttdata/ (superseded by 20250213192412)
- 20241106195300 https://www.innosoftdays.com/event/charla-sostenibilidad-anabel-carmona-gutierrez/ (superseded by 20250121035502)
- 20241106205632 https://www.innosoftdays.com/event/final-torneo-lol/ (superseded by 20250214050229)
- 20241106202836 https://www.innosoftdays.com/event/final-torneo-pokemon-showdown/ (superseded by 20250213184336)
- 20241110162431 https://www.innosoftdays.com/event/seminario-futuro-g1/ (superseded by 20250213201506)
- 20241110163600 https://www.innosoftdays.com/event/seminario-futuro-g2/ (superseded by 20250209154545)
- 20241106200422 https://www.innosoftdays.com/event/seminario-futuro-g3/ (superseded by 20250209134915)
- 20241108135316 https://www.innosoftdays.com/event/seminario-spl-g1/ (superseded by 20250122202104)
- 20241110154539 https://www.innosoftdays.com/event/seminario-spl-g3/ (superseded by 20250209150138)
- 20241106220436 https://www.innosoftdays.com/event/stand-sostenibilidad/ (superseded by 20250122223550)
- 20241108152508 https://www.innosoftdays.com/event/taller-pensamiento-computacional/ (superseded by 20250213194505)
- 20241110143323 https://www.innosoftdays.com/event/torneo-cs2-primera-ronda/ (superseded by 20250122204305)
- 20241110144059 https://www.innosoftdays.com/event/torneo-lol-primera-ronda/ (superseded by 20250122204830)
- 20241210205925 https://www.innosoftdays.com/eventos/stand-de-finanzas-06-11/ (superseded by 20250214142631)
- 20241210210906 https://www.innosoftdays.com/eventos/taller-de-cibers-virus/ (superseded by 20250209144931)
- 20241210202217 https://www.innosoftdays.com/etn_category/taller/ (superseded by 20250214134426)

Empty archive pages (no events listed):

- 20250121050411 https://www.innosoftdays.com/etn_category-10/
- 20250121043026 https://www.innosoftdays.com/etn_category-11/
- 20250121062328 https://www.innosoftdays.com/etn_category-12/
- 20250121054435 https://www.innosoftdays.com/etn_category-13/
- 20250121051100 https://www.innosoftdays.com/etn_category-14/
- 20250121043904 https://www.innosoftdays.com/etn_category-15/
- 20250121035740 https://www.innosoftdays.com/etn_category-16/
- 20250121055259 https://www.innosoftdays.com/etn_category-17/
- 20250121041054 https://www.innosoftdays.com/etn_category-2/
- 20250121061203 https://www.innosoftdays.com/etn_category-22/
- 20250121062305 https://www.innosoftdays.com/etn_category-3/
- 20250121060951 https://www.innosoftdays.com/etn_category-4/
- 20250121054959 https://www.innosoftdays.com/etn_category-5/
- 20250121053326 https://www.innosoftdays.com/etn_category-6/
- 20250121051909 https://www.innosoftdays.com/etn_category-7/
- 20250121050329 https://www.innosoftdays.com/etn_category-8/
- 20250121045041 https://www.innosoftdays.com/etn_category-9/
- 20250214054235 https://www.innosoftdays.com/mec-category/2017/
- 20241110155355 https://www.innosoftdays.com/mec-category/2018/
- 20241106204304 https://www.innosoftdays.com/mec-category/2019/
- 20241110151428 https://www.innosoftdays.com/mec-category/2020/
- 20241110142302 https://www.innosoftdays.com/mec-category/2021/
- 20250209140156 https://www.innosoftdays.com/mec-category/2021/
- 20250213193704 https://www.innosoftdays.com/mec-category/2023/

## Oddities

- The site advertised /event/ pages with tribe markup although the survey signature also says eventon; the etn_* classes belong to Eventin, not EventON.
- ETN listing pages `ponente` and `taller` have a page 2 that was not captured, so a few 2024 talks/workshops may be missing entirely.
- ETN `Pizza` events have end time equal to start time (kept as ends_at null). `Torneo CS2/LOL (Cuartos y semis)` are held online (modality online).
- TEC `Ignasi Labastida i Juan` at 16:00 vs ETN 11:00 the same day (kept ETN). TEC titles carry typos fixed in the output (`Cibersegurirdad`, `Iguldad`).
- The `/etn_category/ponente/` listing is tagged kind=speaker in the manifest and may also be used by the speakers family; speakers here come from the event pages and that listing (photo, bio excerpt).
- The same 2024 activities also exist under `/events/<slug>/` (third plugin, out of scope, same slugs as `/event/`), so the report phase should dedupe 2024 by TEC slug.
- The `Yincana Coles` events (7 and 8 Nov, aula F0.31) are the schools gymkhana; classified as competition.
- ETN listing stubs also appear in the listings we did fetch as: 4i-ai-andres-y-adolfo (1), irene-m-morgado (1), jose-antonio-perez (1), mentoria-turno-manana-3 (1), pensamiento-computacional (1), rafael-m-guitart (1), sol-y-ciberseguridad-anabel-carmona-gutierrez (1), toneo-lol-final (1), torneo-cs2-final (1), torneo-pokemon-showdown (1), torneo-pokemon-showdown-final (1), torneo-rocket-league (1), yincana-turno-tarde (1).
