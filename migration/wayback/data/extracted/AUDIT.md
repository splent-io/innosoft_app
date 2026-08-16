# Audit of data/extracted/*.json

Produced by `parse/audit.py` (read-only). Verdict: **ready_with_notes**.

## Summary

- Coverage: 1045 fetched HTML captures (751 URLs); 733 referenced by a final item, 311 accounted for in the notes (skipped versions, empty archives, spam, iCal exports of events extracted elsewhere, form/login/legal pages), 1 unaccounted for: https://www.innosoftdays.com/wp-json/tribe/events/v1/.
- Schema: 0 errors, 3 warnings against the README schema (all seven files present, every required key on every item, ISO dates, allowed kinds, edition_year in 2013..2025, starts_at year == edition_year).
- Sanity: 3 findings (see section 3); synthesis cross-checks: 0 findings (see section 4).
- Every CDX-index HTML URL with status 200 was fetched (0 unfetched), so the extraction covers everything the archive holds for these hosts.
- Things the importer should know: the events of the 2024 EGC course seminars (Seminario FLOSS 25 Oct, SPL 14-15 Nov, Pipeline 21-22 Nov, Futuro 12-13 Dec 2024) are attached to edition 2024 although they fall outside the 5-8 Nov edition dates (three of them beyond +-30 days); 12 events keep a date-only starts_at and 16 have none; media.json entries mostly point at images the archive never captured (see the CDX figure in section 3); the three English 'Images of ... November 6/7/8' posts are dated 2024-11-09 but carry edition_year 2023 on purpose (2023 photos translated a year later).

## 1. Coverage of the fetched HTML captures

- HTML captures in the manifest (kinds page, event, event-index, post, speaker): 1045 captures, 751 distinct URLs.
- Captures whose URL is referenced by a final JSON item (source_url / sources / used_by / pages.url): 733.
- Captures not referenced by the final JSON but listed in a parts/*.notes.md (skipped, merged, or covered by a family whose part lost the reference in synthesis): 311 captures, 272 URLs.
- Captures neither referenced by the final JSON nor mentioned in any notes file (UNCOVERED): 1 captures, 1 URLs.

### Uncovered captures (not in JSON, not in notes), grouped by kind

#### event (1 URLs, 1 captures)

- https://www.innosoftdays.com/wp-json/tribe/events/v1/ captures 20241113004834

### Captures covered only by the notes (not referenced by any final item), grouped by kind

#### page (109 URLs, 143 captures)

- https://www.innosoftdays.com/?method=ical&id=2234 captures 20241210195839, 20250428143027, 20251011152935 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2237 captures 20250214035100, 20250813152620 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2240 captures 20250620131314 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2254 captures 20250709000600 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2273 captures 20241210215841, 20250420200837 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2282 captures 20251011154859 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2284 captures 20250214041831, 20250708233120 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2286 captures 20241210202519 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2289 captures 20241210202322, 20250622173225 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2291 captures 20241210205659, 20250620132530 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2296 captures 20241210205407, 20251011161615 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2482 captures 20250915181803 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2486 captures 20250714174327 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2508 captures 20250420195035 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2579 captures 20250613095459 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2734 captures 20241210204308, 20251011161054 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2735 captures 20241210204232, 20250619184545 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2737 captures 20250915190313 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2741 captures 20250813163916 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2743 captures 20250214050914, 20251011163347 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2744 captures 20250714185030 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2752 captures 20241210214004, 20251011165900 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2787 captures 20241212043447 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2831 captures 20241210214346, 20250714191245 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=2846 captures 20250214055510, 20251011172605 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3375 captures 20250707221503 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3698 captures 20241212053937, 20250613110821 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3699 captures 20241212053813, 20250915200035 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3703 captures 20241210205148, 20250514205720 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3704 captures 20250214044600, 20251011161507 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=3707 captures 20241210204911, 20250714182333 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=4048 captures 20250425092829 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=4063 captures 20250915184204 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=462558 captures 20250214041314 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=5086 captures 20241210210103 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=5115 captures 20250814074507 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=5131 captures 20250709003533 [notes match by url]
- https://www.innosoftdays.com/?method=ical&id=5134 captures 20241210213537, 20250613104801 [notes match by url]
- https://www.innosoftdays.com/acceder/ captures 20241108155702, 20250214054422 [notes match by url]
- https://www.innosoftdays.com/carrito/ captures 20241210220535 [notes match by url]
- https://www.innosoftdays.com/contactar/ captures 20240616215056, 20240912125332 [notes match by url]
- https://www.innosoftdays.com/en/contact-us/ captures 20241110144513, 20250213184626 [notes match by url]
- https://www.innosoftdays.com/en/xii-edition-organization/ captures 20241106202016 [notes match by url]
- https://www.innosoftdays.com/envia-tu-duda-a-nuestro-equipo/ captures 20241110155044, 20250213193536 [notes match by url]
- https://www.innosoftdays.com/etn_category-10/ captures 20250121050411 [notes match by url]
- https://www.innosoftdays.com/etn_category-11/ captures 20250121043026 [notes match by url]
- https://www.innosoftdays.com/etn_category-12/ captures 20250121062328 [notes match by url]
- https://www.innosoftdays.com/etn_category-13/ captures 20250121054435 [notes match by url]
- https://www.innosoftdays.com/etn_category-14/ captures 20250121051100 [notes match by url]
- https://www.innosoftdays.com/etn_category-15/ captures 20250121043904 [notes match by url]
- https://www.innosoftdays.com/etn_category-16/ captures 20250121035740 [notes match by url]
- https://www.innosoftdays.com/etn_category-17/ captures 20250121055259 [notes match by url]
- https://www.innosoftdays.com/etn_category-2/ captures 20250121041054 [notes match by url]
- https://www.innosoftdays.com/etn_category-22/ captures 20250121061203 [notes match by url]
- https://www.innosoftdays.com/etn_category-3/ captures 20250121062305 [notes match by url]
- https://www.innosoftdays.com/etn_category-4/ captures 20250121060951 [notes match by url]
- https://www.innosoftdays.com/etn_category-5/ captures 20250121054959 [notes match by url]
- https://www.innosoftdays.com/etn_category-6/ captures 20250121053326 [notes match by url]
- https://www.innosoftdays.com/etn_category-7/ captures 20250121051909 [notes match by url]
- https://www.innosoftdays.com/etn_category-8/ captures 20250121050329 [notes match by url]
- https://www.innosoftdays.com/etn_category-9/ captures 20250121045041 [notes match by url]
- https://www.innosoftdays.com/events-tab-pro/ captures 20241210213617 [notes match by url]
- https://www.innosoftdays.com/events/categoria/ceremonia/ captures 20241110161952 [notes match by url]
- https://www.innosoftdays.com/events/categoria/ciberseguridad/dia/2024-11-01/ captures 20250214043431 [notes match by url]
- https://www.innosoftdays.com/events/categoria/ciberseguridad/dia/2024-12-01/ captures 20250121055129 [notes match by url]
- https://www.innosoftdays.com/events/categoria/ciberseguridad/lista/?tribe-bar-date=2024-12-01 captures 20250121042758 [notes match by url]
- https://www.innosoftdays.com/events/categoria/ciberseguridad/mes/ captures 20241212034330 [notes match by url]
- https://www.innosoftdays.com/events/categoria/comunicacion/ captures 20241110162504, 20250214153102 [notes match by url]
- https://www.innosoftdays.com/events/categoria/inteligencia-artificial/ captures 20250213182926 [notes match by url]
- https://www.innosoftdays.com/events/categoria/investigacion/ captures 20241108153151, 20250209151350 [notes match by url]
- https://www.innosoftdays.com/events/categoria/investigacion/mes/ captures 20241210214726 [notes match by url]
- https://www.innosoftdays.com/events/categoria/laboral/ captures 20241110151522 [notes match by url]
- https://www.innosoftdays.com/events/categoria/photocall/ captures 20250122222910 [notes match by url]
- https://www.innosoftdays.com/events/categoria/photocall/2024-12/ captures 20250214043122 [notes match by url]
- https://www.innosoftdays.com/events/categoria/photocall/hoy/ captures 20250214053756 [notes match by url]
- https://www.innosoftdays.com/events/categoria/photocall/lista/ captures 20250214050029 [notes match by url]
- https://www.innosoftdays.com/events/categoria/photocall/mes/ captures 20250214052326 [notes match by url]
- https://www.innosoftdays.com/events/categoria/stand/ captures 20241110150422, 20250209142759 [notes match by url]
- https://www.innosoftdays.com/events/categoria/torneos/ captures 20241106202645, 20250122204659 [notes match by url; referenced by a parts/*.json but not by the final JSON]
- https://www.innosoftdays.com/events/categoria/torneos/2024-12/ captures 20250214034754 [notes match by url]
- https://www.innosoftdays.com/events/categoria/torneos/hoy/ captures 20250214040933 [notes match by url]
- https://www.innosoftdays.com/events/categoria/torneos/lista/ captures 20250214054347 [notes match by url]
- https://www.innosoftdays.com/events/categoria/torneos/mes/ captures 20250214055017 [notes match by url]
- https://www.innosoftdays.com/events/categoria/yincana/ captures 20241110155439, 20250214051614 [notes match by url]
- https://www.innosoftdays.com/events/etiqueta/investigacion/ captures 20250214042156 [notes match by url]
- https://www.innosoftdays.com/mec-category/2017/ captures 20250214054235 [notes match by url]
- https://www.innosoftdays.com/mec-category/2018/ captures 20241110155355 [notes match by url]
- https://www.innosoftdays.com/mec-category/2019/ captures 20241106204304 [notes match by url]
- https://www.innosoftdays.com/mec-category/2020/ captures 20241110151428 [notes match by url]
- https://www.innosoftdays.com/mec-category/2021/ captures 20241110142302, 20250209140156 [notes match by url]
- https://www.innosoftdays.com/mec-category/2023/ captures 20250213193704 [notes match by url]
- https://www.innosoftdays.com/mi-cuenta/ captures 20241210220800 [notes match by url]
- https://www.innosoftdays.com/miembros/ captures 20241110145229, 20250214043854 [notes match by url]
- https://www.innosoftdays.com/newsletter/ captures 20241106214556, 20250213200626 [notes match by url]
- https://www.innosoftdays.com/organizacion-ix-edicion/ captures 20241106203625 [notes match by url]
- https://www.innosoftdays.com/password-reset/ captures 20241110161309, 20250121055214 [notes match by url]
- https://www.innosoftdays.com/politica-de-cookies/ captures 20250121041536 [notes match by url]
- https://www.innosoftdays.com/programa-2/ captures 20241110150726, 20250122212140 [notes match by url]
- https://www.innosoftdays.com/registrar/ captures 20250213201424 [notes match by url]
- https://www.innosoftdays.com/registrar-2/ captures 20241210214806 [notes match by url]
- https://www.innosoftdays.com/registrar-2/bienvenidoi/ captures 20241210220612 [notes match by url]
- https://www.innosoftdays.com/registrar-2/tu-membresia/?rcp_action=lostpassword captures 20250121052248 [notes match by url]
- https://www.innosoftdays.com/related-event-widget-pro-2/ captures 20241210210250 [notes match by url]
- https://www.innosoftdays.com/topics/ captures 20240614131416 [notes match by url]
- https://www.innosoftdays.com/usuario/innosoft_editor/ captures 20241108141119 [notes match by url]
- https://www.innosoftdays.com/usuario/innosoft_manager/ captures 20241110144228 [notes match by url]
- https://www.innosoftdays.com/usuario/innosoft_publisher/ captures 20241106210409 [notes match by url]
- https://www.innosoftdays.com/usuario/innosoft_publisher_two/ captures 20241106205850 [notes match by url]
- https://www.innosoftdays.com/usuario/innosoft_seo/ captures 20241110150501 [notes match by url]

#### event-index (2 URLs, 4 captures)

- https://www.innosoftdays.com/en/events/ captures 20241110152805, 20250213192655 [notes match by url]
- https://www.innosoftdays.com/events/ captures 20240616205939, 20241212034646 [notes match by url]

#### post (156 URLs, 158 captures)

- https://www.innosoftdays.com/2024/01/18/turkiye-bolgesinde-tek-pinup-kumarhane-tercih-etme/ captures 20250207234216 [notes match by url]
- https://www.innosoftdays.com/2024/05/15/new-post/ captures 20250208005716 [notes match by url]
- https://www.innosoftdays.com/2024/05/15/new-post-2/ captures 20250208003618 [notes match by url]
- https://www.innosoftdays.com/2024/07/17/paribahis-yuksek-oranlar-engin-musabaka-2/ captures 20250208010613 [notes match by url]
- https://www.innosoftdays.com/2025/01/08/speel-plinko-game-in-online-casinos-in-nederland-ontdek-onze-nederlandse-spelopties/ captures 20250207233724 [notes match by url]
- https://www.innosoftdays.com/2025/01/09/disfruta-de-la-emocion-del-casino-en-linea-con-inflar-globos-app-juega-en-chile-ahora/ captures 20250208012200 [notes match by url]
- https://www.innosoftdays.com/2025/01/09/spielen-sie-plinko-online-im-osterreichischen-casino-entdecken-sie-die-elektrisierende-glucksspielwelt/ captures 20250208012441 [notes match by url]
- https://www.innosoftdays.com/2025/01/10/disfruta-del-emocionante-juego-de-sugar-rush-1000-en-los-mejores-casinos-en-linea-de-argentina/ captures 20250208012311 [notes match by url]
- https://www.innosoftdays.com/2025/01/10/experience-the-thrill-of-plinko-play-online-in-english-and-win-big-from-the-uk/ captures 20250207233436 [notes match by url]
- https://www.innosoftdays.com/2025/01/12/experience-big-bass-splash-play-exciting-online-casino-games-in-english-now-available-in-canada/ captures 20250208010152 [notes match by url]
- https://www.innosoftdays.com/2025/01/12/experimente-o-thrill-do-jogo-online-no-playpix-casino-brasil-jogue-agora/ captures 20250208004858 [notes match by url]
- https://www.innosoftdays.com/2025/01/12/le-bandit-jouez-aux-meilleurs-jeux-de-casino-en-ligne-en-france/ captures 20250207235535 [notes match by url]
- https://www.innosoftdays.com/2025/01/13/descarga-el-juego-de-balloon-app-y-gana-dinero-en-linea-jugando-casino-en-colombia/ captures 20250208001723 [notes match by url]
- https://www.innosoftdays.com/2025/01/13/disfruta-de-sugar-rush-1000-gratis-en-linea-y-lleva-tu-experiencia-de-casino-a-otro-nivel-en-argentina/ captures 20250208003850 [notes match by url]
- https://www.innosoftdays.com/2025/01/13/experimente-fortune-gems-2-gratuitamente-jogue-online-no-casino-no-brasil/ captures 20250208005830 [notes match by url]
- https://www.innosoftdays.com/2025/01/15/descubre-el-big-bass-bonanza-demo-como-jugar-en-linea-en-espana/ captures 20250208012123 [notes match by url]
- https://www.innosoftdays.com/2025/01/15/experience-the-thrill-of-8k8-official-online-casino-in-english-now-available-in-the-philippines/ captures 20250207234133 [notes match by url]
- https://www.innosoftdays.com/2025/01/15/jouez-aux-jeux-de-casino-en-ligne-au-thebes-casino-connexion-france/ captures 20250207235910 [notes match by url]
- https://www.innosoftdays.com/2025/01/15/melden-sie-sich-beim-b7-casino-an-jetzt-onlinecasino-spiele-in-niederlandisch-spielen/ captures 20250208011426 [notes match by url]
- https://www.innosoftdays.com/2025/01/16/disfruta-de-balloon-juego-dinero-apk-juega-al-casino-en-linea-en-espana/ captures 20250208003011 [notes match by url]
- https://www.innosoftdays.com/2025/01/16/experimente-o-demo-slot-jogar-cassino-online-no-fortune-ox-disponivel-no-brasil/ captures 20250208001310 [notes match by url]
- https://www.innosoftdays.com/2025/01/16/online-xanadi-casino-glorqo-online-casinosi-azrbaycanda/ captures 20250208011506 [notes match by url]
- https://www.innosoftdays.com/2025/01/16/speel-de-pirots-2-gokkast-demo-in-het-nederlands-kansspelen-online/ captures 20250208010537 [notes match by url]
- https://www.innosoftdays.com/2025/01/17/erleben-sie-das-glucksspiel-im-lucky-vibe-onlinecasino-die-beste-casinoerfahrung-in-deutschland/ captures 20250208000822 [notes match by url]
- https://www.innosoftdays.com/2025/01/17/jogue-no-jonbet-o-melhor-casino-online-em-portugues-para-brasil/ captures 20250207232909 [notes match by url]
- https://www.innosoftdays.com/2025/01/17/onda-pin-up-azrbaycanin-en-populer-online-kelimsal-kasino-blogu/ captures 20250214042441 [notes match by url]
- https://www.innosoftdays.com/2025/01/17/spielen-sie-mega-joker-slots-online-im-casino-erleben-sie-die-spannung-in-deutschland/ captures 20250207234049 [notes match by url]
- https://www.innosoftdays.com/2025/01/18/experience-the-lucky-charm-of-7-casino-login-and-play-online-in-english-for-australia/ captures 20250207232809 [notes match by url]
- https://www.innosoftdays.com/2025/01/18/logi-sisse-viggoslots-kasiino-ja-alusta-mangida-eestis/ captures 20250208001220 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/22bet-v-ceske-republice-online-hazardni-hry-a-sazeni/ captures 20250208004204 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/beste-nettcasinoer-i-norge-2025-bonuser-og-fordeler-for-spillere/ captures 20250208005252 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/casinoin-ellada-100-eos-200eu-200-dorean-peristrophes/ captures 20250208002059 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/decouvrez-les-sensations-du-vrai-casino-en-ligne-avec-casino-betonred/ captures 20250207233952 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/descubra-o-melhor-horario-para-jogar-reel-love-e-aumentar-suas-vencedoras-no-casino-online/ captures 20250207235949 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/gioca-a-lightning-storm-di-evolution-gaming-il-brivido-del-casino-online-in-italia/ captures 20250207234925 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/hangug-onrain-kajino-coegoyi-cuceon-mic-geomto-anjeonhan-peulraespomgwa-ggomggomhan-bunseogeuro-coejeogyi-seontaegeul-dowadeuribnida/ captures 20250208003050 [notes match by url]
- https://www.innosoftdays.com/2025/01/19/tu-1-gamoaines-totalizatori-add-aseve-megobrebi-icarmoe-carmatebit-quini/ captures 20250207234601 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/22bet-ellada-e-episeme-pule-gia-agores-stoikhematon-kai-kazino-me-asphaleia-kai-poikilia/ captures 20250208005447 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/22bet-v-ceske-republice-oficialni-stranky-a-moznosti-sazeni/ captures 20250208011931 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/aposte-em-nossa-plataforma-de-casino-online-betriot-o-melhor-do-brasil/ captures 20250208002853 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/azrbaycanda-glory-casino-rsmi-internet-sayti-il-qazanc-v-ylncni-bir-araya-gtirin/ captures 20250207234847 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/descubre-todo-sobre-1win-en-argentina-y-su-experiencia-en-casinos-online/ captures 20250208004941 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/discover-the-best-real-money-online-pokies-at-australian-casinos/ captures 20250208004244 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/lemon-casino-oficjalna-strona-internetowa-kasyno-online/ captures 20250208005020 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/mostbet-magyarorszag-125-bonusz-regisztracio-es-bejelentkezes/ captures 20250208000037 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/mukavita-vecdiyti-ucun-mostbet-ortaq-proqrami-azerbaycan/ captures 20250208005217 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/ofitsialnyy-sayt-get-x-igray-v-onlayn-kazino-get-kh/ captures 20250207232715 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/pinko-kazino-ofitsialnyy-sayt-igrat-v-onlayn-kazino-pinco-luchshie-igry-bonusy-i-vyigryshi/ captures 20250207234348 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/sanal-kumar-bahis-ans-talih-oyunlar-ceza-davalar-30/ captures 20250208005752 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/spela-pirots-3-casino-online-en-guide-for-svenska-spelare/ captures 20250208012458 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/tipobet-casino-giris-adresi-tipobet365-ile-guvenilir-bahis-deneyimi/ captures 20250208000327 [notes match by url]
- https://www.innosoftdays.com/2025/01/20/wazamba-casino-ellada-to-kalutero-diadiktuako-kazino-gia-ellenikous-paiktes/ captures 20250208002221 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/1win-giris-turkiyede-online-casino-guvenilir-ve-eglenceli-oyunlarla-en-iyi-deneyimi-sunar/ captures 20250208001137 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/22bet-ellada-e-episeme-pule-tou-kazino-kai-ton-stoikhematon-gia-ellenikous-paiktes/ captures 20250208002814 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/22bet-v-ceske-republice-siroka-kolekce-her-pro-kazdeho/ captures 20250208003457 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/casinoin-ellada-100-eos-200eu-200-dorean-peristrophes-2/ captures 20250207231754 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/crazy-time-lemozione-del-gioco-dal-vivo-nei-casino-online-di-evolution-gaming/ captures 20250208003251 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/experience-avia-masters-stake-play-toprated-casino-games-online-in-english-for-uk-players/ captures 20250207234516 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/exploring-1win-casino-and-sportsbook-thrills-in-india/ captures 20250208003930 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/glory-casino-hesabi-turkiyedeki-profilimiz/ captures 20250208001853 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/igrayte-v-luchshie-onlaynkazino-ukrainy-pryamo-seychas/ captures 20250208011309 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/jogue-no-casino-online-descubra-jon-bet-apostas-no-brasil/ captures 20250207234725 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/laki-dzhet-ofitsialnyy-sayt-lucky-jet/ captures 20250207234805 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/lemon-casino-recenzje-kasyno-online-opinie-i-oceny/ captures 20250208004533 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/mastering-online-pokies-australia-tips-and-strategies-to-win-big/ captures 20250208003809 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/mpes-sto-kosmo-tou-koulokhere-zeus-kai-ade-tou-pragmatic-paikhnidia-kazino-se-leitourgia-diadiktuaka/ captures 20250207235706 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/ofitsialnyy-sayt-kazino-get-x-vkhod-i-registratsiya-v-get-iks/ captures 20250208012421 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/otkroyte-mir-azarta-i-vyigrysha-na-pokerdom-ofitsialnyy-sayt-onlayn-kazino/ captures 20250208005522 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/otkryvayte-novye-gorizonty-igry-top10-luchshikh-onlayn-kazino-v-ukraine/ captures 20250208005911 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/pin-irket-casino-turkiye-deki-kurumsal-nternet/ captures 20250208003655 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/pinco-kazino-ofitsialnyy-sayt-pinko-vkhod-na-zerkalo/ captures 20250208002421 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/pokerdom-ofitsialnyy-sayt-onlayn-kazino-vse-o-registratsii-igrovom-protsesse-i-bonusakh/ captures 20250208003210 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/pokerdom-onlayn-kazino-i-poker-rum-tvoy-shans-na-krupnyy-vyigrysh-i-nezabyvaemye-emotsii/ captures 20250208002341 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/professionalnyy-bukmeker-i-top-kazino-1win/ captures 20250208003538 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/registratsiya-v-bukmekerskoy-kontore-1win-legkiy-start-dlya-vashego-uspekha-v-mire-stavok/ captures 20250207231304 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/riobet-ofitsialnyy-sayt-i-zerkalo-onlayn-kazino/ captures 20250208010726 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/riobet-ofitsialnyy-sayt-i-zerkalo-onlayn-kazino-2/ captures 20250208005638 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/sahabet-casino-giris-adresi-ve-sahabet-guncel-giris-bilgileri/ captures 20250207233218 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/vavada-onlayn-kazino-vse-o-populyarnoy-platforme-dlya-azartnykh-igr/ captures 20250207235127 [notes match by url]
- https://www.innosoftdays.com/2025/01/21/zerkalo-mostbet-vkhod-na-ofitsialnyy-sayt-mostbet-bez-blokirovok/ captures 20250207231557 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/1win-en-argentina-juegos-y-apuestas-para-disfrutar-al-maximo/ captures 20250214053721 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/1win-polnoe-rukovodstvo-po-stavkam-na-sport-v-bukmekerskoy-kontore/ captures 20250214050437 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/1xbet-zerkalo-rabochee-dlya-vkhoda-na-ofitsialnyy-sayt/ captures 20250208004658 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/2025ci-ilin-n-yaxsi-azrbaycan-kazinolari-etibarli-oyun-saytlari-v-secimlriniz/ captures 20250208012359 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/azrbaycanda-glory-casino-platformasinin-trafli-icmali/ captures 20250207233002 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/casibom-ile-eglenceli-ve-guvenilir-casino-ve-bahis-deneyimine-bugun-katilin/ captures 20250208001601 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/connectezvous-sur-betonred-et-jouez-au-casino-en-ligne-des-maintenant/ captures 20250214053645 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/everything-you-need-to-know-about-online-pokies-in-australia/ captures 20250207234302 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/experience-the-thrill-login-to-kings-casino-play-online-in-english-uk/ captures 20250214052747 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/exploring-the-best-online-casinos-in-australia-a-comprehensive-guide-to-popular-platforms/ captures 20250208004616 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/jojobet-spor-bahisleri-ve-casino-heyecani-ile-unutulmaz-mac-deneyimleri-yasayin/ captures 20250208000121 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/mostbet-casino-giris-turkiye-ile-resmi-casino-oyunlari-ve-spor-bahislerine-kolayca-katilin/ captures 20250208001004 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/mostbet-casino-official-online-website-register-and-login-in-bangladesh/ captures 20250208004046 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/mostbet-w-polsce-aplikacja-mobilna-dla-graczy/ captures 20250214044426 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/ofitsialnyy-sayt-onlayn-kazino-get-x-vkhod-i-registratsiya-v-get-kh/ captures 20250208001354 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/onlinecasino-setzen-sie-auf-rot-und-spielen-sie-bet-on-red-in-deutschland/ captures 20250207233049 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/onwin-casino-giris-yapmanin-en-kolay-yolu-onwinguncel-giris-ile-sansinizi-deneyin/ captures 20250208004006 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/otkroyte-mir-azarta-i-vyigrysha-na-pokerdom-ofitsialnyy-sayt-onlayn-kazino-2/ captures 20250208012519 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/pin-ap-kazino-ofitsialnyy-sayt-pin-up-casino-igrat-onlayn-vkhod-zerkalo-luchshee-mesto-dlya-azartnykh-razvlecheniy-i-bolshikh-vyigryshey-vsego-v-neskolko-klikov/ captures 20250207232106 [notes match by url]
- https://www.innosoftdays.com/2025/01/22/pin-up-casino-n-yaxsi-onlayn-kazino-platformasi-azrbaycanda-pinup/ captures 20250208002619 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/descubre-la-emocion-de-los-mejores-bonos-y-juegos-en-el-casino-online-1win/ captures 20250208001436 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/discover-the-thrills-and-excitement-of-glory-casino-bangladesh-your-ultimate-gaming-destination/ captures 20250207235749 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/grandpashabet-canli-casino-ve-bahis-harika-firsatlarla-eglence-dolu-bir-deneyim-sunuyor/ captures 20250207235257 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/hrajte-online-plinko-hru-v-kasine-prihlaste-sa-dnes/ captures 20250207233522 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/jouez-aux-jeux-de-casino-en-ligne-sur-winbay-france-decouvrez-le-meilleur-des-paris-en-france/ captures 20250208011231 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/lemon-casino-kompleksowa-recenzja-lemon-kasyno/ captures 20250208012236 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/mcw-casino-trusted-online-casino-and-sports-betting-in-bangladesh/ captures 20250207231042 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/mostbet-ofitsialnyy-sayt-gde-delat-stavki-na-sport-i-igrat-v-sloty/ captures 20250208005603 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/ninecasino-avis-profitez-de-450-eu-de-bonus-et-250-free-spins/ captures 20250208001810 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/pelaa-ilmaista-gates-of-olympus-demoa-suihkivilla-nettikasinolla-kaikki-tietoa-suomenkielisesta-casinopelista-talla-sivulla/ captures 20250208003334 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/pocket-option-ofitsialnyy-sayt-dlya-torgovli-binarnymi-optsionami/ captures 20250214054018 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/registratsiya-v-bukmekerskoy-kontore-1win/ captures 20250208010842 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/spielen-sie-mit-winspirit-entdecken-sie-das-fesselnde-onlinecasino-erlebnis-in-deutschland/ captures 20250208010802 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/uchitsya-igrat-v-poker-stavki-v-kazino-onlayn/ captures 20250208001641 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/vauhdikas-casinot-kokeile-viggoslotsin-pelattavaksi-verkossa/ captures 20250208010343 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/vavada-onlayn-kazino-osobennosti-igry-i-preimushchestva/ captures 20250208004407 [notes match by url]
- https://www.innosoftdays.com/2025/01/23/wazamba-casino-ellada-to-kalutero-diadiktuako-kazino-gia-ellenes-paiktes/ captures 20250208000728 [notes match by url]
- https://www.innosoftdays.com/2025/01/24/gioca-al-casino-online-vincispin-in-italiano-lesperienza-di-gioco-definitiva-per-il-mercato-italiano/ captures 20250208012046 [notes match by url]
- https://www.innosoftdays.com/2025/01/24/gransino-casino-online-casino-spelen-voor-nederlanders/ captures 20250208003130 [notes match by url]
- https://www.innosoftdays.com/2025/01/24/spielen-sie-mit-stil-zino-onlinecasino-die-coolste-spielplattform-fur-deutschland/ captures 20250208011546 [notes match by url]
- https://www.innosoftdays.com/2025/01/28/bahis-lisanslar-lisansl-bahis-siteleri-130/ captures 20250207230633 [notes match by url]
- https://www.innosoftdays.com/2025/01/28/pin-up-da-kumar-oynamak-yasal-m-1919/ captures 20250208010112 [notes match by url]
- https://www.innosoftdays.com/2025/01/28/turkye-buyuk-mllet-mecls-8/ captures 20250207235006 [notes match by url]
- https://www.innosoftdays.com/2025/01/29/bettilt-bahis-sitesi-eki-guvenilir-mi-kullanc/ captures 20250208010030 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/1xslots-1khslots-2025-polnyy-obzor-onlayn-kazino/ captures 20250208002657 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/b9-game-in-pakistan-your-ultimate-guide-to-mastering-the-number-one-betting-casino-game/ captures 20250208000622 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/banger-casino-online-in-bangladesh-2025-explore-free-play-and-real-money-gaming-excitement/ captures 20250207232615 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/bezpieczenstwo-w-kasynach-online-casinoli-w-polsce-kluczowe-aspekty-i-porady/ captures 20250207234643 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/hangug-onrain-kajino-coegoyi-geimgwa-boneoseuro-jeulgineun-anjeonhago-sinnaneun-dobag-gyeongheom/ captures 20250207233304 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/hangug-onrain-kajino-wanbyeog-gaideu-coegoyi-saiteu-cuceon-mic-anjeonhan-peulrei-bangbeob-ggultib-daegonggae/ captures 20250207235336 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/kasyno-online-casinoli-w-polsce-wplaty-i-wyplaty-jak-dziala-system-platnosci/ captures 20250207230532 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/mobilnoe-prilozhenie-onlayn-kazino-1xslots-1khslots-udobstvo-i-dostupnost/ captures 20250208003733 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/mobilnoe-prilozhenie-onlayn-kazino-1xslots-1khslots-udobstvo-i-dostupnost-2/ captures 20250208004124 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/olimp-kazino-ofitsialnyy-sayt-v-kazakhstane-olimp-casino/ captures 20250208010422 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/olimp-kazino-ofitsialnyy-sayt-v-kazakhstane-olimp-casino-2/ captures 20250208012009 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/otkroyte-mir-azarta-i-strategii-s-pokerdom-onlayn-kazino-i-poker-rum-2024-goda/ captures 20250208005407 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/otkroyte-mir-azarta-i-strategii-s-pokerdom-onlayn-kazino-i-poker-rum-2024-goda-2/ captures 20250208005327 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/otkroyte-mir-azarta-i-vyigrysha-s-ofitsialnym-saytom-onlayn-kazino-riobet-riobet-2/ captures 20250208002932 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/pinko-kazino-ofitsialnyy-sayt-igrat-onlayn-vkhod-zerkalo/ captures 20250208010307 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/pinko-kazino-ofitsialnyy-sayt-igrat-onlayn-vkhod-zerkalo-2/ captures 20250208011739 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/pinko-kazino-ofitsialnyy-sayt-pinco-dlya-igry-onlayn-s-udobnym-zerkalom-i-bystrym-vkhodom-2/ captures 20250208004323 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/pokerdom-ofitsialnyy-sayt-populyarnogo-onlayn-kazino-s-shirokim-vyborom-igr/ captures 20250207232445 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/riobet-zerkalo-2024-dostup-k-ofitsialnomu-saytu-kazino-riobet/ captures 20250208002734 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/riobet-zerkalo-2024-dostup-k-ofitsialnomu-saytu-kazino-riobet-2/ captures 20250208002259 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/vavada-kazino-ofitsialnyy-sayt-igrayte-v-luchshie-igry-bezopasno-i-s-udovolstviem/ captures 20250207233834 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/vavada-onlayn-kazino-mir-azarta-i-vyigryshey-u-vas-pod-rukoy/ captures 20250208004449 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/vavada-onlayn-kazino-otzyvy-i-osobennosti-populyarnoy-platformy/ captures 20250208010919 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/vavada-onlayn-kazino-otzyvy-i-osobennosti-populyarnoy-platformy-2/ captures 20250208003415 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/zooma-zerkalo-r7-casino-ofitsialnyy-sayt-p7-kazino/ captures 20250208002541 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/zuma-kazino-studiya-2-mama-ro-apartamenty/ captures 20250207235413 [notes match by url]
- https://www.innosoftdays.com/2025/02/01/zuma-kazino-studiya-2-mama-ro-apartamenty-2/ captures 20250208010458 [notes match by url]
- https://www.innosoftdays.com/2025/02/02/zooma-sayt-prikhodyat-sms-na-telefon-s-kodom-podtverzhdeniya-s-raznykh-saytov/ captures 20250208002501 [notes match by url]
- https://www.innosoftdays.com/2025/02/02/zooma-sayt-prikhodyat-sms-na-telefon-s-kodom-podtverzhdeniya-s-raznykh-saytov-2/ captures 20250208004820 [notes match by url]
- https://www.innosoftdays.com/2025/02/04/zooma-telegram-novosti-izzi-kazino-platezhi-i-tekhpodderzhka/ captures 20250208001520 [notes match by url]
- https://www.innosoftdays.com/2025/02/05/download-the-becric-app-place-sports-bets-play-casino-games-in-english-for-indian-players/ captures 20250208011818 [notes match by url]
- https://www.innosoftdays.com/es/2025/10/20/hola-mundo/ captures 20251109033629, 20260217172859, 20260511022317 [notes match by url]

#### speaker (5 URLs, 6 captures)

- https://www.innosoftdays.com/etn-speaker-category/ captures 20241110151703, 20250213191612 [notes match by url]
- https://www.innosoftdays.com/etn-speaker-category/organizer/ captures 20241210212248 [notes match by url]
- https://www.innosoftdays.com/etn-speaker-category/uncategorized/ captures 20241210211650 [notes match by url]
- https://www.innosoftdays.com/forums/topic/buy-levonorgestrel-ohio-componentes-levonorgestrel-etinilestradiol/ captures 20240625100208 [notes match by url]
- https://www.innosoftdays.com/wp-content/plugins/innosoft2021/assets/css/ponentes.css captures 20221107001944 [notes match by url]

## 2. Schema validation

Errors: 0. Warnings: 3.

### Warnings

- post 2024-11-09T14:11:01 'Images of Monday, November 6' (https://www.innosoftdays.com/en/2024/11/09/images-of-monday-november-6/): post year 2024 != edition_year 2023
- post 2024-11-09T14:23:55 'Images from Tuesday, November 7' (https://www.innosoftdays.com/en/2024/11/09/images-from-tuesday-november-7/): post year 2024 != edition_year 2023
- post 2024-11-09T14:36:52 'Images of Wednesday, November 8' (https://www.innosoftdays.com/en/2024/11/09/images-of-wednesday-november-8/): post year 2024 != edition_year 2023

## 3. Sanity checks

Findings: 3.

- event outside edition 2024 +-30 days: 2024-12-12T17:40:00 'Seminario Futuro (G3)' (https://www.innosoftdays.com/event/seminario-futuro-g3/) [NOT mentioned in REPORT.md]
- event outside edition 2024 +-30 days: 2024-12-13T10:40:00 'Seminario Futuro (G2)' (https://www.innosoftdays.com/event/seminario-futuro-g2/) [NOT mentioned in REPORT.md]
- event outside edition 2024 +-30 days: 2024-12-13T12:40:00 'Seminario Futuro (G1)' (https://www.innosoftdays.com/event/seminario-futuro-g1/) [NOT mentioned in REPORT.md]

### Informational

- events per edition_year: 2017: 19, 2018: 31, 2019: 18, 2020: 22, 2021: 34, 2022: 42, 2023: 22, 2024: 65, 2025: 28
- events without starts_at: 16; events with date-only starts_at: 12
- events dated outside their edition's own starts_on..ends_on (within +-30 days or not): 14: [2022] 2022-10-27T00:00:00 '¡Haz tu Wordle Diario!'; [2023] 2023-10-20 'Game Jam InnoSoft 2023'; [2023] 2023-10-23 'Concurso de imágenes generadas con IA'; [2024] 2024-10-25 'Seminario FLOSS (free/libre and open-source software)'; [2024] 2024-11-14T17:40:00 'Seminario SPL (G3)'; [2024] 2024-11-15T10:40:00 'Seminario SPL (G2)'; [2024] 2024-11-15T12:40:00 'Seminario SPL (G1)'; [2024] 2024-11-21T17:40:00 'Seminario Pipeline (G3)'; [2024] 2024-11-22T10:40:00 'Seminario Pipeline (G2)'; [2024] 2024-11-22T12:40:00 'Seminario Pipeline (G1)'; [2024] 2024-12-12T17:40:00 'Seminario Futuro (G3)'; [2024] 2024-12-13T10:40:00 'Seminario Futuro (G2)'; [2024] 2024-12-13T12:40:00 'Seminario Futuro (G1)'; [2025] 2025-11-03T16:00:00 'eSports: TFT'
- speakers per edition_year: 2017: 10, 2018: 27, 2019: 13, 2020: 14, 2021: 23, 2022: 27, 2023: 25, 2024: 16, 2025: 9
- organisers per edition_year: 2023: 144, 2024: 150
- posts per edition_year: 2018: 7, 2019: 5, 2020: 5, 2021: 32, 2022: 32, 2023: 29, 2024: 20
- HTML fields: no <script>, <style>, class=, style=, on*= or web.archive.org URLs found
- image references: poster/photo/featured URLs on the two site hosts with no media entry: 0; external (hotlinked) ones: 4; <img> in HTML fields: 416 distinct, 0 site-hosted without media entry, 15 external hotlinks (not in media.json by design)
- event speaker names with no speaker record: 12: Jesús González (2018); Jurado: Daniel Liszka (2018); Pablo Trinidad (2018); Alicia Melgarejo (2020); Daniel Arteaga (2020); Francisco Javier Llamas (2020); GUMUS (Grupo de Usuarios de Macintosh de la Universidad de Sevilla) (2020); Jorge Avendaño (2020); Mª Rosario Arjona (2020); Sergio Martín (2020); Adolfo (2024); Andrés (2024)
- media URLs with no capture at all in the CDX index (any size variant, any status): 996 of 1049

## 4. Synthesis cross-checks (parts -> final, notes delegations -> final)

Findings: 0.

### Informational

- parts events: 427 records; final: 281; records with no final counterpart by URL, year+title or year+start: 6
- parts event with no final counterpart: events_mec: [2020] 2020-11-24T08:30:00 'Innosoft Days 2020' (https://www.innosoftdays.com/events/innosoft-2020/) [explained in REPORT.md]
- parts event with no final counterpart: events_mec: [2022] 2022-11-10T08:00:00 'Innosoft Days día 3' (https://www.innosoftdays.com/events/dia-dos-innosoft-days-2/) [explained in REPORT.md]
- parts event with no final counterpart: events_mec: [2022] 2022-11-11T08:00:00 'Innosoft Days día 4' (https://www.innosoftdays.com/events/innosoft-days-dia-3/) [explained in REPORT.md]
- parts event with no final counterpart: events_mec: [2024] 2024-11-07T11:00:00 'Charla Proyecto de investigación – Pablo y Alberto' (https://www.innosoftdays.com/events/charla-proyecto-de-investigacion-pablo-y-alberto/) [explained in REPORT.md]
- parts event with no final counterpart: posts_2018_2020: [2018] None 'Concurso de programación TOURNAMETSII' (https://www.innosoftdays.com/2018/11/11/equipos-del-concurso-programacion-tournametsii/) [explained in REPORT.md]
- parts event with no final counterpart: posts_2022: [2022] None 'Torneo de ajedrez' (https://www.innosoftdays.com/2022/10/23/its-a-me-innosoft-days-2022/) [explained in REPORT.md]
- parts speakers: 266 records; final: 155; names with no final counterpart (exact, subset or one-typo): 4
- parts speaker with no final counterpart: events_eventos_etn: 'Andrés y Adolfo' [2024] [explained in REPORT.md]
- parts speaker with no final counterpart: events_mec: 'Javier Antonio Pérez' [2024] [explained in REPORT.md]
- parts speaker with no final counterpart: events_mec: 'Mª Carmen Romero' [2017] [explained in REPORT.md]
- parts speaker with no final counterpart: events_mec: 'Paco Profe' [2021] [explained in REPORT.md]
- parts organisers: 294 records; final: 294; lost: 0
- parts posts: 130 records; final: 130; lost: 0
- parts pages: 37 records; final: 37; lost: 0
- parts media: 1927 records (all families, overlapping); final: 1049; images (any size variant) with no final entry: 0
- pages_editions calendar slots delegated to other families: 155; without a final event (year+title or year+start): 0
- pages_editions speakers delegated to other families: 16; without a final speaker: 0

