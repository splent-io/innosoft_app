# posts_2022 notes

Scope: manifest kind=post with permalink `/2022/MM/DD/slug/` (InnoSoft Days X, 8 to 11 November 2022).
Captures in scope: 46 (32 distinct URLs). Every 2022 post URL present in data/index.jsonl was fetched.
Extracted: 32 posts (latest capture per URL). Older captures skipped: 14 (same URL, entry-content text identical to the latest one; verified programmatically).

## Outputs
- posts: 32
- events: 10
- speakers: 12
- editions: 1 (2022)
- media: 33

## Per-month counts (posts)
- 2022-10: 4
- 2022-11: 28

## Skipped captures (older versions of a URL, content identical to the version used)
- https://www.innosoftdays.com/2022/10/23/its-a-me-innosoft-days-2022/: used 20250122221642, skipped 20241108154018
- https://www.innosoftdays.com/2022/11/04/los-horarios-de-las-charlas-ya-han-sido-publicados/: used 20250122203150, skipped 20241106201355
- https://www.innosoftdays.com/2022/11/05/te-gustaria-estudiar-un-master-gratis/: used 20250213193155, skipped 20241110153624
- https://www.innosoftdays.com/2022/11/05/update-importante-se-ha-actualizado-la-informacion-relativa-a-las-charlas/: used 20250214154321, skipped 20241110163616
- https://www.innosoftdays.com/2022/11/06/apartan-de-la-universidad-de-sevilla-a-un-profesor-acusado-de-acososexual-y-laboral/: used 20250214045514, skipped 20241106205057
- https://www.innosoftdays.com/2022/11/06/cuatro-cientifiques-lgtbq-que-cambiaronla-ciencia/: used 20250213191910, skipped 20241110151905
- https://www.innosoftdays.com/2022/11/06/de-donde-proviene-el-termino-bug/: used 20250213194707, skipped 20241106213323
- https://www.innosoftdays.com/2022/11/06/que-es-el-test-de-finkbeiner/: used 20250214153536, skipped 20241106215805
- https://www.innosoftdays.com/2022/11/08/desarrollo-de-una-aplicacion-pedagogica-enfocado-al-alumnado-trans/: used 20250213193452, skipped 20241110154946
- https://www.innosoftdays.com/2022/11/08/software-libre-en-ntt-data/: used 20250213191527, skipped 20241106205253
- https://www.innosoftdays.com/2022/11/08/un-gran-problema-de-desigualdad-en-silicon-valley/: used 20250209152329, skipped 20241110161838
- https://www.innosoftdays.com/2022/11/09/accenture-y-el-uso-de-software-libre-para-el-desarrollo-y-venta-de-servicios-asociados/: used 20250213193950, skipped 20241110155827
- https://www.innosoftdays.com/2022/11/11/importante-cambio-de-sala-del-evento-de-clausura/: used 20250122211246, skipped 20241106204049
- https://www.innosoftdays.com/2022/11/15/resumen-software-libre-en-la-sociedad-mas-libre/: used 20250213202015, skipped 20241110163416

## How fields were filled
- date: `article:published_time` (UTC) converted to naive Europe/Madrid; matches the visible dd/mm/yyyy of every post.
- content_html: `.entry-content` after un-lazying images (data-src -> src, `<noscript>` twins dropped) and collapsing `wp-block-file` (PDF embed + title link + Descarga button) into one paragraph linking the PDF by its title; then clean_html().
- excerpt: WordPress-style automatic excerpt, first 55 words of the cleaned text (see below).
- featured_image_url: `og:image` (WordPress falls back to the first content image; the posts have no real featured image). Empty for the 27 posts without images.
- categories: WordPress category classes on `<article>` (`Noticias`), plus the tag `Igualdad`; the default `Sin categoría` was dropped (the 17 news-clipping posts are only tagged Igualdad, so that tag is what identifies them).
- lang: es for every post (site language es-ES).

## Events
Only what the posts themselves state. `starts_at` is a full datetime when the post gives a time (gymkhana, 10/11 15:30), a date-only ISO string when only the day is known (NTT DATA and Accenture talks were 'this Tuesday' morning = 2022-11-08; closing ceremony and barrilada on 2022-11-11), and null otherwise (chess and Brawlhalla tournaments, OpenSUSE and Red Hat talks, master raffle stand). The talk timetable of the edition lived on /ponentes-x-edicion/ (family of the event pages), so times for talks should come from there. Talk description_html is the summary post written by the organisation after the talk.
Not turned into events: the daily web games (Ahorcado, Wordle, crucigramas, post 'Sabías que'), the sustainability publication 'Linux Server vs Windows Server' (a student write-up with PDF, not an activity), and the 17 equality news clippings.

## Speakers
Six people confirmed in the 27/10 announcement (ETSII director, three professors, two engineers; no talk titles given) plus the six speakers named in the four talk summaries. Padmini Gopalakrishnan appears only as the subject of a news clipping, not a speaker.

## Excerpt / soft breaks
- excerpt: WordPress-style automatic excerpt (first 55 words of the cleaned text, ellipsis when cut); the SEO meta description was not used because on the PDF posts it glued the title to the 'Descarga' button label.
- 'primera-publicacion-de-sostenibilidad' was pasted from a PDF with a `<br/>` at every wrapped line; breaks that split a sentence (word before, lowercase after) were joined into a space, the rest kept.

## Oddities
- 17 posts dated 6 and 8 November are bare PDF embeds (`wp-block-file`, tag Igualdad, category Sin categoría): equality-themed press clippings; content_html is a single link to the PDF and excerpt equals the title.
- 'primera-publicacion-de-sostenibilidad' has H1 '[RESUMEN] >>LINUX SERVER VS WINDOWS SERVER' (slug and title differ).
- The 27/10 announcement lists Guadaltel twice; kept verbatim in the post, mentioned once in the edition summary.
- The 2024 and 2025 captures of the same post differ only in the WordPress generator version and Wayback chrome.
- Post images are the 1024px WordPress renditions referenced by the page (kept verbatim so the importer can resolve them).
- No organisers or standalone pages in this family.
