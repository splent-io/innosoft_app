# Content migration from innosoftdays.com (WordPress)

This directory keeps the frozen export of the old WordPress site (edition
XIII, November 2025) so the migration stays reproducible after the old site
goes offline.

- `innosoft_export/events.json` and `schedule.json` fed the real programme
  now seeded by `splent_feature_events` (21 activities with rooms and times).
- `innosoft_export/about.json` fed the product's own AboutSeeder
  (`src/innosoft_app/seeders.py`).
- `innosoft_export/photos.json` lists the 418 gallery photos with verified
  full-size URLs. They are imported into the media library with the one-shot
  script below.
- `innosoft_export/feedback.json` preserves the 27 questions (ES and EN) of
  the feedback questionnaire. The form itself is NOT rebuilt yet; building a
  reusable survey feature is a pending product decision.
- `innosoft_export/media_summary.json` indexes all 534 WordPress media items.
- The edition itself (XIII, 3 to 6 November 2025) and the upcoming XIV are
  seeded by the product's `EditionsSeeder` (`src/innosoft_app/seeders.py`),
  which then attaches every event dated inside an edition to it. Earlier
  editions (institucional.us.es/innosoftdays and the first years of
  innosoftdays.com) are recovered from the web archive in a separate step
  and land in the same model.

## Importing the photo galleries

Curated content arrives with `splent db:seed`. The photo galleries are
imported once, while the old site is reachable, from the product console
(`splent product:console`):

```python
import json
from splent_io.splent_feature_media.services import MediaService

data = json.load(open("migration/innosoft_export/photos.json"))
svc = MediaService()
for img in data["highlight_slider"]:
    svc.import_from_url(img["fullsize_url"], title="InnoSoft Days 2025")
for day in data["days"]:
    for group in day["groups"]:
        title = f"{group['group']} ({day['day_tab']})"
        for img in group["images"]:
            svc.import_from_url(img["fullsize_url"], title=title, in_gallery=True)
```

The import is idempotent by source URL. Afterwards run `splent db:dump` so
the content survives without the old site.
