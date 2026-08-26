# Design Taste Library

A local, zero-build gallery for curating web design references. Screenshots go in; a
**controlled design vocabulary**, real colour tokens, and paste-ready build briefs come out.

The problem it solves: "make it look good" gives a model nothing to aim at, so it regresses to
the mean — purple gradients, glossy blobs, icon-grid feature rows. This turns taste you can
recognise into language you can hand to a build.

```bash
git clone <this-repo> && cd taste-vault
python3 serve.py
```

That's it. No dependencies, no build step — one vanilla `index.html`. `serve.py` picks a free
port, opens a browser, and writes `local.json` so copied briefs resolve reference images on your
machine.

---

## What's in a brief

Click a family pill → **Copy brief block**. You get one block assembling:

```
AESTHETIC     the family, and when to deploy it
VOCABULARY    every trait across its entries
REFERENCES    each entry + an absolute path to its screenshot
PALETTE       real hex values, marked measured or estimated
HOUSE DNA     constants that hold regardless of the look
NEVER         the anti-slop guardrail
ONE RISK      a deliberate bold move, to avoid a safe average
HERO ASSET    an image-gen recipe with a [SUBJECT] slot
```

Paste it above your own **intent**, then work in a funnel: 5 versions across different
aesthetics → 3 variations of the winner → 1 refined.

The per-entry **Copy brief** does the same for a single reference. **Copy image prompt** returns
the entry's recipe with the subject filled in.

## Adding entries

Drop screenshots in `inbox/`, then in Claude Code:

```
/taste-add
```

The skill ships with the repo (`.claude/skills/taste-add/`). It reads the image, matches traits
**against the existing vocabulary rather than inventing new ones**, pulls real CSS tokens when
you give it a live URL, and writes a schema-valid entry. Given a video URL it will download the
clip and diff frames to measure whether motion loops, plays once, or is scroll-linked.

It deliberately leaves one field blank: `meta.steal_this`, the single move worth taking. That
judgment is yours, and a generated answer looks done without being true.

```bash
python3 make-thumbs.py     # after adding entries
python3 trait-lint.py      # check for vocabulary drift
```

## Why the vocabulary is controlled

Free-text tags fragment. Left alone you write `warm paper ground` on one entry and
`warm paper background` on another, and a filter that should surface both surfaces neither.

`vocabulary.json` prevents that with four mechanisms:

| | |
|---|---|
| **Facets** | 7 groups (colour, type, layout, component, imagery, texture, motion) so matching compares ~a dozen candidates, not all of them |
| **Aliases** | every rejected phrasing is recorded, so that mistake can never split the bucket again |
| **Promotion** | a trait becomes `canonical` on its second use; single-use traits are notes, not categories |
| **`trait-lint.py`** | flags unknown traits, near-duplicates, and singletons; `--fix` rewrites aliases |

Run the linter over any free-text tag set and you'll see why — near-duplicate pairs pile up fast.

## Making it yours

The repo ships with a working library so you can see the system running. To start your own:

1. Set `library.owner` in `design-taste-library.json`
2. Rewrite `dna.constants` and `dna.never` — **the never-list matters as much as the constants**,
   and both should come from your eye, not mine
3. Either keep the families as starting points, or reset: `"entries": []` and
   `"style_families": []`
4. Delete `images/*.png` and `images/thumbs/*.jpg` for a clean slate

Editing `design-taste-library.json` by hand is always fine — it's the source of truth. Validate
with any JSON Schema tool against `design-taste-library.schema.json`.

**Seed the vocabulary in bulk, not incrementally.** Tag your first ~15 entries freely, then do a
single consolidation pass over all of them. Categories only become visible in aggregate; minting
them one at a time bakes in bad early terms.

## Files

```
index.html                    the whole app — vanilla JS, no build
design-taste-library.json     entries + families + House DNA — source of truth
design-taste-library.schema.json   structure contract (JSON Schema 2020-12)
vocabulary.json               controlled traits: facets, aliases, status
trait-lint.py                 drift checker
make-thumbs.py                grid thumbnails from the full captures
serve.py                      static server + local.json writer
.claude/skills/taste-add/     the ingestion skill
images/                       captures; thumbs/ are generated
inbox/                        drop zone for unprocessed screenshots
```

## Data model

- **entry** — `id, title, formula, description, style_family, kind, platform, source, traits[],
  tokens, brief, image_recipe, meta`
- **`kind`** — `shipped` · `concept` · `mine`. Most Dribbble work is `concept`: beautiful and
  frequently unbuildable. Never prompt a production layout from an unlabelled concept.
- **`tokens.extraction`** — `measured` (read from live CSS) or `estimated` (read off pixels).
  Worth distinguishing: on the one entry measured after being estimated, every hex was wrong
  while every trait was right.
- **family** — `definition` (what it looks like), `deploy_for` (when to reach for it), `risk`,
  `image_style`
- **dna** — `constants[]` with evidence counts + `never[]`, appended to every brief

## Credit

The concept is Chase's — see [Turn Claude Into A Design GENIUS In 3 Simple
Steps](https://youtu.be/7FU98O0JLHs) and [cth9191/taste-vault](https://github.com/cth9191/taste-vault),
which is MIT licensed. House DNA, `deploy_for`, the collection-level brief block, and embedding
image paths in briefs are all borrowed from it. The controlled vocabulary, design tokens, schema
validation, provenance tracking, and motion measurement are additions.

## Licence & the screenshots

Code is MIT. The screenshots in `images/` are of third-party websites, kept as personal design
references — **all rights to those designs remain with their creators**. Several are concept work
by their designers rather than shipped products; `source.attribution` credits them where known.
Swap them for your own inspiration.
