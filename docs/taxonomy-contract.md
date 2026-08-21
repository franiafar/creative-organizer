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

---

# Contrato de taxonomía de Creative Organizer

**Propietario:** Fran

**Estado:** Bloqueado

**Regla de cambio:** No modificar ninguna regla sin la autorización explícita de Fran para ese cambio exacto.

## Raíz de salida y carpetas de mercado

- La carpeta de lanzamiento seleccionada por el usuario es la carpeta madre. Se conserva su nombre y no se crea otro wrapper.
- Los mercados se ordenan según la columna `Country` copiada de la trafficking sheet cuando es válida; los mercados faltantes se agregan de forma determinista.
- Las carpetas se nombran `1 - BR`, `2 - AR`, etc. La numeración no lleva ceros a la izquierda.
- Se agrega un código de idioma solo cuando hace falta distinguir múltiples entregas lingüísticas o cuando una regla de mercado lo exige, como `1 - IN EN`, `2 - IN HI` y `3 - IN RO`.
- Si un mercado tiene solo Static, se nombra `1 - BR - Static`. Si tiene solo Motion, `1 - BR - Motion`.
- Si tiene ambos tipos, se nombra `1 - BR` y contiene hijos inmediatos `Static` y `Motion`, escritos completos y con mayúscula inicial.

## Alcance del procesamiento

- En mega launches se procesan solamente Meta y TikTok/TT, detectados desde las carpetas fuente y campos anclados del filename.
- YouTube, spreadsheets, trackers, ZIPs y cualquier material fuera de alcance quedan exactamente donde estaban. No se envían a `Otros`.
- No se crea una carpeta de plataforma por defecto. Los archivos Meta y TikTok de un mismo creativo pueden convivir cuando sus filenames siguen siendo distintos.
- Se agrega un nivel `Meta` o `TikTok` únicamente cuando la taxonomía específica por plataforma difiere o cuando evita una pérdida de información por colisión.
- Solo se crean carpetas respaldadas por archivos observados. No se generan conceptos, tipos, idiomas, formatos o plataformas vacíos desde una plantilla global.

## Dimensiones semánticas y técnicas

Se preservan dimensiones semánticas a cualquier profundidad: concepto, ejecución, CTA, CTA Alt, Test A/B, hook, personaje, audiencia, copy o variante de entrega, además de cualquier carpeta fuente cuya distinción esté corroborada por archivos vecinos.

Se ignoran como niveles creativos los wrappers técnicos: `Regions`, país e idioma, `Stills`, `Static`, `Video`, `Motion`, etiquetas de export como `Motion 11`, aspect ratios como `9x16`, `4x5` y `1x1`, resoluciones, duración, plataforma, fecha, IDs, tokens de mercado y extensión.

La metadata técnica puede permanecer en el filename. Solo se convierte en carpeta si hace falta evitar una colisión o preservar una diferencia semántica comprobada.

## Inferencia de taxonomía

1. Se analiza la ruta fuente completa y cada componente se clasifica como alcance, mercado, idioma, semántica, tipo de medio o metadata técnica.
2. Las carpetas fuente semánticas se preservan en su orden original, sin importar si aparecen antes o después de la carpeta de tipo de medio.
3. Los campos del filename se interpretan mediante anclas, no posiciones fijas. Se reconocen fechas, IDs numéricos de producción, tokens compactos de mercado-idioma, plataforma, marcadores de medio, duración, aspect ratio, resolución y extensión.
4. El bloque descriptivo restante se usa como evidencia del nombre creativo. Static y Motion comparten el mismo parser.
5. Se comparan todos los archivos del lanzamiento. Las estructuras repetidas corroboran límites, pero nunca borran una distinción de carpeta fuente.
6. Se reconcilian las evidencias de ruta y filename. Una ruta semántica clara tiene prioridad sobre un filename genérico, duplicado o contradictorio.
7. Si la evidencia no permite seleccionar una ruta semántica segura, se conserva la separación original o se marca el archivo como no resuelto. Nunca se mezclan creativos inciertos.

## Ejemplos de jerarquía

- Las versiones Static y Motion de `Wrestling_ButNow` comparten el concepto `Wrestling - ButNow`; `9x16` nunca reemplaza al concepto.
- `Something to Wear` sigue siendo un único concepto legible aunque los filenames usen `Something_To_Wear`.
- `Hair Analysis/Hair Analysis CTA` y `Hair Analysis/Hair Analysis CTA Alt` conservan el padre y sus dos variantes; no se aplanan ni mezclan.
- `Hairstyle/Test A` y `Color Analysis/Test A` siguen separados aunque todos los filenames digan `Personal_Color_Analysis`.
- Meta puede tener `1x1`, `4x5` y `9x16`, mientras TikTok tiene solo `9x16`. Son diferencias de formato, no conceptos separados.
- Un concepto puede existir en una plataforma o idioma y no en otro. Cada mercado se infiere a partir de los archivos observados, sin asumir simetría.

## Colisiones, preview, apply y undo

- Nunca se sobrescribe un destino. Antes de agregar sufijos numéricos, se verifica si falta un nivel semántico o de plataforma.
- Los duplicados byte a byte se distinguen de las colisiones de nombre. Solo se elimina un duplicado si se verifica igualdad y Undo puede restaurar el estado previo.
- El preview muestra cada movimiento propuesto con origen, destino, mercado/idioma, plataforma, tipo, ruta semántica, metadata ignorada y confianza o motivo de no resolución.
- Los archivos de baja confianza quedan sin mover o en un estado explícitamente revisable aprobado por Fran; la ambigüedad nunca se oculta dentro de una carpeta plausible.
- Apply es transaccional: ante un fallo, se restauran las ubicaciones previas. Se conserva un registro de Undo confiable para la última ejecución exitosa.
- Se exige idempotencia: volver a previsualizar o aplicar sobre un lanzamiento ya ordenado no inventa niveles, no vuelve a renombrar carpetas ni degrada la taxonomía.

## Matriz mínima de regresión

Se prueban: Static/Motion dual; solo Static; solo Motion; numeración sin cero; India y Canadá multilingües; concepto fuente antes de `Stills/Video`; carpetas de aspect ratio; fallback solo por filename; conceptos de varias palabras; CTA/CTA Alt anidados; Test A/B bajo padres distintos; Meta más TikTok; YouTube y sheets intactos; disponibilidad asimétrica entre plataformas; conflicto entre filename y ruta fuente; colisión de destino; duplicado byte a byte; clasificación no resuelta; preview sin escrituras; segunda ejecución idempotente; rollback ante fallo parcial; y Undo.

---

Made with <3 by Francisco Iafar
