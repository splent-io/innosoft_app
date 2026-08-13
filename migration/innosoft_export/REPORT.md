# InnoSoft Days migration briefing

Export of https://www.innosoftdays.com (WordPress + Elementor + Polylang + Forminator + MetaSlider), taken 2026-08-13 via public REST API and rendered HTML.

## Site structure

6 content pages, each in an EN/ES pair (Polylang; EN at root, ES under /es/):

| Page | EN (id) | ES (id) |
|---|---|---|
| Home | home (214) | inicio (48) |
| About | about-us (271) | sobre-nosotros (29) |
| Events | events (224) | eventos (25) |
| Schedule | schedule (254) | cronograma (27) |
| Photos | fotos-2 (1668) | fotos (420) |
| Feedback | feedback (440) | cuestionario (459) |

Plus exactly 1 blog post, which is the untouched default "¡Hola, mundo!" sample post (blog unused, drop it), and 534 media items (494 jpeg, 22 png, 18 heic).

All pages are built from Elementor heading/image widgets. There is no semantic table, list, or article markup anywhere; every text is an h2 heading widget. No countdown, no CTAs, no sponsor logo strips.

## Edition coverage

The site covers ONLY the latest edition, InnoSoft Days XIII, 3-6 November 2025 (in-person days Tue Nov 4 and Thu Nov 6 at ETSII, Universidad de Sevilla; online eSports Mon Nov 3 to Wed Nov 5). No archive of earlier editions exists. All uploads are from 2025/10 and 2025/11.

## ES/EN verdict (source of truth per page)

- Home: equivalent; EN is cleaner (ES has a paragraph/heading ordering slip). EN hero title has a casing typo "Edition xiiI".
- About: EN is fuller (ES lacks the second paragraph about organizing tasks). Use EN as source, translate to ES.
- Events: identical set of 13 events in both; treat as equal bilingual sources. ES uses Spanish poster artwork variants.
- Schedule: mostly identical (25 in-person + 3 online slots each), but ES fixes an EN error, see conflicts below. Cross-check both.
- Photos: image sets are byte-identical between languages (418 unique photos each).
- Feedback: parallel 27-question Forminator forms (EN form 444, ES form 443).

## Counts

- Events page: 13 events (8 talks, 3 workshops, 2 ceremonies). 9 named speakers.
- Schedule: 28 slots (25 in-person, 3 online) + 2 QR poster images.
- Photos: 418 unique photos. Highlight slider 58; Tuesday tab 101 in 10 activity groups; Thursday tab 259 in 8 groups (largest: Closing Ceremony 106, Zeller 62, CaixaBank 36).
- Media library: 534 items (the gallery photos plus posters and site imagery).
- Downloaded content images: 29 (hero, site logo, home images, 26 event posters EN+ES).

## Companies / organiser

No sponsor section exists. Companies appear only as talk providers: NTT Data, Indra, CaixaBank Tech. Academic guests: Andreas Zeller (CISPA), Universidad de Sevilla faculty (Pablo Reina Jiménez, Pedro Almagro Blanco). Organiser is collective: students of the Software Engineering degree, within the Evolution and Configuration Management course; no individual names or roles listed anywhere. Contact: innosoftdays@gmail.com plus 8 social profiles (Facebook, X, Instagram, LinkedIn, YouTube, Twitch, TikTok, Spotify podcast).

## Oddities and data conflicts

1. Schedule EN vs ES conflicts (unresolved on the site):
   - Escape Room rooms: EN A2.12 / A2.15, ES "AS45" for both sessions.
   - CaixaBank Tech (Thu): EN 9:30-12:30 double-books A4.33 with eSports Minecraft; ES 11:30-12:30 fits. ES looks corrected.
   - Online TFT: EN 16:00-16:30 vs ES 16:00-20:30.
2. Manuel Carranza talk shows start 08:30 with no end, same time and room as the Opening Ceremony (it is effectively the ceremony keynote). Gymkhana also has no end time.
3. No in-person Wednesday program. "QR FOR DIFFERENT SCHEDULES" is two QR poster images with no hyperlinks (dead-end for web users).
4. Gallery images have empty alt text everywhere; photo group membership comes only from h6 headings in tab order.
5. 18 gallery photos (IMG_19xx) have no true original JPEG (they were HEIC uploads; only the -scaled JPEG exists). photos.json falls back to the -scaled variant, verified with HEAD.
6. The blog contains only the WordPress sample post; the feed/blog should not be migrated.
7. Six activity types (tournaments, eSports, escape room, game jam, gymkhana, sustainable challenge) exist ONLY on the Schedule page and photo gallery, never on the Events page; the new CMS should not repeat that inconsistency.
8. Photos page title/slug mismatch: EN page is slug "fotos-2" titled "Photos"; ES is "fotos".

## Recommended mapping to a feature-based CMS

- events feature: one Event entity per activity (name ES/EN, type talk/workshop/ceremony/competition/esports/social, description ES/EN, speaker(s), company, poster image, external links). Merge the 13 Events-page entries with the schedule-only activities so every activity is an Event (about 21 distinct activities).
- schedule feature: ScheduleSlot referencing an Event (date, start, end, room, modality in_person/online). 28 slots for the 2025 edition. Room as plain text; resolve the 4 EN/ES conflicts editorially (prefer ES for CaixaBank).
- edition feature: an Edition entity (number XIII, year 2025, date range, venue) that events/slots/galleries hang off, enabling the multi-year archive the current site lacks.
- gallery feature: Album per activity per edition (18 albums + 1 highlights album), images from photos.json fullsize_url; captions absent, generate from album names.
- about feature: static bilingual page from about.json content_html plus core values list, map embed, contact block.
- sponsors/partners feature: seed with NTT Data, Indra, CaixaBank Tech (logo extraction from posters needed; no standalone logo assets exist on the site).
- feedback: replicate as a form feature or link out; 27 questions per language captured in feedback.json.
- footer/social: site-level config (8 social URLs, contact email, copyright).
