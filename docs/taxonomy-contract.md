# Creative Organizer Taxonomy Contract

**Owner:** Fran
**Status:** Locked
**Change rule:** Do not alter any rule without Fran's explicit authorization for that exact change.

## Output root and market folders

- Treat the user-selected launch folder as the mother folder. Preserve its user-provided name and do not create another wrapper.
- Order markets from the copied trafficking-sheet country column when valid; append missing markets deterministically.
- Name folders `1 - BR`, `2 - AR`, and so on. Do not zero-pad the number.
- Add a language code only when needed to distinguish multiple language deliveries or when a market rule requires it, such as `1 - IN EN`, `2 - IN HI`, and `3 - IN RO`.
- If a market has only Static, name it `1 - BR - Static`. If it has only Motion, name it `1 - BR - Motion`.
- If a market has both types, name it `1 - BR` and create immediate `Static` and `Motion` children. Spell both labels completely with initial capitals.

## Processing scope

- In mega launches, process only Meta and TikTok/TT. Recognize the platform from source folders and anchored filename fields.
- Leave YouTube, spreadsheets, trackers, ZIPs, and other out-of-scope material exactly where it is. Do not send it to `Otros` merely because it is out of scope.
- Do not create a platform folder by default. Allow Meta and TikTok files for the same creative to coexist when their filenames remain distinct.
- Add a `Meta` or `TikTok` level only when platform-specific taxonomy differs or a collision would otherwise lose information.
- Build only folders supported by observed files. Do not create empty concepts, types, languages, formats, or platforms from a global template.

## Semantic versus technical dimensions

Preserve semantic dimensions at arbitrary depth: concept, execution, CTA, CTA Alt, Test A/B, hook, character, audience, copy or delivery variant, and any source folder whose distinctions are corroborated by neighboring files.

Ignore technical wrappers when building the creative path: `Regions`, country and language folders, `Stills`, `Static`, `Video`, `Motion`, export labels such as `Motion 11`, aspect ratios such as `9x16`, `4x5`, and `1x1`, pixel resolutions, duration, platform, date, IDs, market tokens, and extension.

Technical metadata may remain in filenames. Promote it to a folder only to prevent a collision or preserve a proven semantic difference.

## Taxonomy inference

1. Parse the complete source path and classify each component as scope, market, language, semantic, media type, or technical metadata.
2. Preserve semantic source folders in their original order, regardless of whether they appear before or after the media-type folder.
3. Parse filename fields using anchors rather than fixed positions. Recognize dates, numeric production IDs, compact market-language tokens, platform, media markers, duration, aspect ratio, resolution, and extension.
4. Treat the remaining contiguous descriptor span as filename evidence for the creative name. Apply the same parser to Static and Motion.
5. Compare all files in the launch. Use repeated structures to corroborate boundaries, never to erase a source-folder distinction.
6. Reconcile path and filename evidence. Let a clear semantic path outrank a generic, duplicated, or contradictory filename.
7. If evidence cannot safely select one semantic path, retain the original separation or mark the file unresolved. Never merge uncertain creatives.

## Hierarchy examples

- `Brazil/Portuguese/Wrestling/Stills/9x16/...Wrestling_ButNow_BRPT_Meta_Still_9x16.jpg` and its Motion equivalent must share the creative label `Wrestling - ButNow`; `9x16` must not replace the concept.
- `Something to Wear` is one human-readable concept even when filenames use `Something_To_Wear`. Preserve source-folder wording and use filename evidence only to enrich it.
- `Hair Analysis/Hair Analysis CTA` and `Hair Analysis/Hair Analysis CTA Alt` remain a parent with two child variants. Do not flatten or merge them.
- `Hairstyle/Test A` and `Color Analysis/Test A` remain separate even when every filename says `Personal_Color_Analysis`; explicit semantic folders outrank misleading filenames.
- Meta may contain `1x1`, `4x5`, and `9x16` while TikTok contains only `9x16`. These are format differences, not separate creative concepts.
- A concept can exist on one platform or language and not another. Infer each market from observed files rather than assuming symmetry.

## Collision, preview, apply, and undo

- Never overwrite a destination. Before adding numeric suffixes, determine whether a missing semantic or platform level explains the collision.
- Treat byte-identical duplicates separately from name collisions. Remove a duplicate only when equality is verified and undo can restore the prior state.
- Preview every planned move with source, destination, detected market/language, platform, media type, semantic path, ignored metadata, and confidence or unresolved reason.
- Keep low-confidence files unmoved or place them in an explicitly reviewable state approved by Fran; do not hide ambiguity in a plausible folder.
- Make apply transactional: on failure, restore prior locations. Preserve one reliable undo record for the latest successful run.
- Require idempotency: previewing or applying an already organized launch must not invent levels, rename folders again, or degrade its taxonomy.

## Minimum regression matrix

Test: dual Static/Motion; Static-only; Motion-only; no zero padding; multilingual India and Canada; source concept before `Stills/Video`; aspect-ratio folders; filename-only fallback; multiword concepts; nested CTA/CTA Alt; sibling Test A/B under different parents; Meta plus TikTok; YouTube and sheets untouched; asymmetric platform availability; filename conflict with source path; destination collision; byte-identical duplicate; unresolved classification; preview without writes; second-run idempotency; partial-failure rollback; and undo.
