# Creative Organizer

## English

Creative Organizer is a macOS app that organizes Paid Media deliveries inside a launch's existing mother folder. It first generates an explainable preview and, after confirmation, moves only Meta and TikTok creative files that it can classify safely. It does not duplicate the mother folder, overwrite files, or touch unsupported material. It also keeps one undo record for the latest successful run.

### Download and installation

[Download the latest version](https://github.com/franiafar/creative-organizer/releases/latest/download/Creative-Organizer.zip). This link always points to the newest release; the complete version history is available under [Releases](https://github.com/franiafar/creative-organizer/releases).

Unzip the file and open `Creative Organizer.app`. If macOS displays a warning the first time, Control-click the app, choose `Open`, and confirm. The app includes everything it needs; you do not need to install Python or Xcode.

### Daily use

Optionally, copy the complete `Country` column from the trafficking sheet before opening the app. The first valid appearance of each market defines its order; missing markets are added deterministically. Then choose the launch's mother folder, review the preview, and confirm `Organize`.

The preview is read-only. It shows the source, proposed destination, market/language, platform, media type, semantic hierarchy, ignored technical metadata, evidence, and confidence. Ambiguous cases remain unmoved and include an explanation.

### Output structure

The selected folder keeps its name and remains the root. Numbers do not use leading zeros, and `Static` and `Motion` are always written in full:

```text
13 Jul Ramadan Mega Launch
├── 1 - BR
│   ├── Static
│   │   └── Wrestling - ButNow
│   └── Motion
│       └── Wrestling - ButNow
├── 2 - IN EN - Static
│   └── Something to Wear
├── 3 - IN HI - Static
│   └── Something to Wear
└── 4 - AR - Motion
    └── Hair Analysis
        ├── Hair Analysis CTA
        └── Hair Analysis CTA Alt
```

A market with only one media type is named, for example, `1 - BR - Static` or `2 - AR - Motion`. If it contains both types, the market is named `1 - BR` and has immediate `Static` and `Motion` children. India always includes the language; other markets, such as Canada, include it when multiple language deliveries exist.

### What it preserves and ignores

The app preserves the full semantic hierarchy, even when it appears before or after `Stills`/`Video`: concept, execution, CTA, CTA Alt, Test A/B, hook, character, audience, copy, and delivery variants. For example, `Hairstyle/Test A` and `Color Analysis/Test A` never mix, even when their filenames are identical or contradictory. A clear semantic source path outranks the filename.

Technical wrappers do not create levels: `Regions`, country/language, `Stills`, `Static`, `Video`, `Motion`, `Motion 11`, formats such as `1x1`, `4x5`, and `9x16`, resolution, duration, date, IDs, market, and platform. Static and Motion use the same anchored filename parser. It can enrich `Wrestling` with `ButNow` to produce `Wrestling - ButNow`, or recover `Something To Wear` when no concept folder exists.

Only Meta and TikTok/TT creative files are organized. YouTube files, spreadsheets, trackers, ZIPs, and unsupported material remain exactly where they were; the app never creates an `Other` folder. It also does not create empty folders from a global template. Meta and TikTok coexist without a platform level when filenames remain distinct. `Meta` or `TikTok` appears only when needed to resolve a platform collision safely.

### Collisions, duplicates, and safety

Creative Organizer never overwrites files. When a collision occurs, it first looks for a justified platform separation. If that does not solve the collision, the affected files stay in the source for review. Byte-identical duplicates are also preserved in both places; the app does not delete information to “clean up” the tree.

Apply is transactional. If one move fails, completed moves return to their original locations. A second run over an organized launch is idempotent: it does not add levels or renumber folders. `Undo` restores the source hierarchy from the latest successful run and then consumes that record; repeating Undo does nothing.

### Development and testing

The engine lives at `Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py`, and the native interface lives in `Organizador.m`. The test suite uses only the standard library and temporary directories:

```sh
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m py_compile 'Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py'
```

The target runtime is Python 3.9. Publishing a `vX.Y.Z` tag automatically prepares the installable ZIP for the release.

---

## Español

Creative Organizer es una aplicación para macOS que ordena entregas de Paid Media dentro de la carpeta madre existente del lanzamiento. Primero genera un preview explicable y, al confirmar, mueve únicamente creativos de Meta y TikTok que puede clasificar con seguridad. No duplica la carpeta madre, no sobrescribe archivos ni toca material no soportado. También conserva un undo de la última ejecución exitosa.

### Descarga e instalación

[Descargar siempre la última versión](https://github.com/franiafar/creative-organizer/releases/latest/download/Creative-Organizer.zip). El enlace apunta automáticamente al release más reciente; el historial completo está en [Releases](https://github.com/franiafar/creative-organizer/releases).

Descomprimí el ZIP y abrí `Creative Organizer.app`. Si macOS muestra una alerta la primera vez, hacé Control + clic sobre la app, elegí `Abrir` y confirmá. La app ya incluye todo lo necesario: no hace falta instalar Python ni Xcode.

### Uso diario

Opcionalmente, copiá la columna `Country` completa de la trafficking sheet antes de abrir la app. La primera aparición válida de cada mercado define el orden; los mercados ausentes se agregan de forma determinista. Luego elegí la carpeta madre del lanzamiento, revisá el preview y confirmá `Organizar`.

El preview es de solo lectura. Muestra origen, destino propuesto, mercado/idioma, plataforma, tipo, jerarquía semántica, metadata técnica ignorada, evidencia y confianza. Los casos ambiguos quedan sin mover y explican el motivo.

### Estructura de salida

La carpeta elegida conserva su nombre y actúa como raíz. La numeración no lleva ceros a la izquierda y los nombres `Static` y `Motion` siempre se escriben completos:

```text
13 Jul Ramadan Mega Launch
├── 1 - BR
│   ├── Static
│   │   └── Wrestling - ButNow
│   └── Motion
│       └── Wrestling - ButNow
├── 2 - IN EN - Static
│   └── Something to Wear
├── 3 - IN HI - Static
│   └── Something to Wear
└── 4 - AR - Motion
    └── Hair Analysis
        ├── Hair Analysis CTA
        └── Hair Analysis CTA Alt
```

Un mercado con un único tipo se llama, por ejemplo, `1 - BR - Static` o `2 - AR - Motion`. Si tiene ambos tipos, el mercado se llama `1 - BR` y contiene hijos inmediatos `Static` y `Motion`. India siempre muestra idioma; otros mercados, como Canadá, lo muestran cuando existen múltiples entregas lingüísticas.

### Qué preserva y qué ignora

Se conserva la jerarquía semántica completa, incluso cuando aparece antes o después de `Stills`/`Video`: concepto, ejecución, CTA, CTA Alt, Test A/B, hook, personaje, audiencia, copy y variantes de entrega. Por ejemplo, `Hairstyle/Test A` y `Color Analysis/Test A` nunca se mezclan aunque sus filenames sean iguales o contradictorios. Una ruta fuente semántica clara tiene prioridad sobre el filename.

Los wrappers técnicos no crean niveles: `Regions`, país/idioma, `Stills`, `Static`, `Video`, `Motion`, `Motion 11`, formatos `1x1`, `4x5`, `9x16`, resoluciones, duración, fecha, IDs, mercado y plataforma. Static y Motion usan el mismo parser anclado de filename. Puede enriquecer `Wrestling` con `ButNow` para producir `Wrestling - ButNow` o recuperar `Something To Wear` cuando no hay carpeta de concepto.

La organización procesa solo Meta y TikTok/TT. YouTube, spreadsheets, trackers, ZIPs y cualquier material no soportado quedan exactamente donde estaban; no se crea una carpeta `Otros`. Tampoco se generan carpetas vacías desde una plantilla global. Meta y TikTok conviven sin nivel de plataforma cuando sus filenames son distintos. `Meta` o `TikTok` aparece solo cuando resuelve de forma segura una colisión entre plataformas.

### Colisiones, duplicados y seguridad

Creative Organizer nunca sobrescribe. Ante una colisión, intenta primero una separación justificable por plataforma. Si no alcanza, deja los archivos en origen para revisión. Los duplicados byte a byte también se conservan en ambos lugares: no se elimina información para “limpiar” el árbol.

Apply es transaccional. Si un movimiento falla, los movimientos ya hechos vuelven a sus rutas originales. La segunda ejecución sobre un lanzamiento ya ordenado es idempotente: no agrega niveles ni renumera carpetas. `Undo` restaura la jerarquía fuente de la última ejecución exitosa y luego consume ese registro; repetir Undo no modifica nada.

### Desarrollo y pruebas

El motor está en `Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py` y la interfaz nativa está en `Organizador.m`. La suite usa solamente la biblioteca estándar y directorios temporales:

```sh
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m py_compile 'Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py'
```

El runtime objetivo es Python 3.9. Al publicar una etiqueta `vX.Y.Z`, GitHub prepara automáticamente el ZIP instalable del release.

---

Made with <3 by Francisco Iafar
