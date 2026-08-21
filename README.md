# Creative Organizer

Aplicación para macOS que ordena entregas de Paid Media dentro de la carpeta madre del lanzamiento. Primero genera un preview explicable y, al confirmar, mueve únicamente creativos de Meta y TikTok que puede clasificar con seguridad. No duplica la carpeta madre, no sobrescribe archivos y conserva un undo de la última ejecución exitosa.

## Descarga e instalación

[Descargar siempre la última versión](https://github.com/franiafar/creative-organizer/releases/latest/download/Creative-Organizer.zip). El enlace apunta automáticamente al release más reciente; el historial completo está en [Releases](https://github.com/franiafar/creative-organizer/releases).

Descomprimí el ZIP y abrí `Creative Organizer.app`. Si macOS muestra una alerta la primera vez, hacé Control + click sobre la app, elegí `Abrir` y confirmá. La app ya incluye lo necesario: no hace falta instalar Python ni Xcode.

## Uso diario

Opcionalmente, copiá la columna `Country` completa de la trafficking sheet antes de abrir la app. La primera aparición válida de cada mercado define el orden; los mercados ausentes se agregan de forma determinista. Luego elegí la carpeta madre del lanzamiento, revisá el preview y confirmá `Organizar`. Preview es de solo lectura: muestra origen, destino propuesto, mercado/idioma, plataforma, tipo, jerarquía semántica, metadata técnica ignorada, evidencia y confianza. Los casos ambiguos quedan sin mover y explican el motivo.

## Estructura de salida

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

Un mercado con un único tipo se llama, por ejemplo, `1 - BR - Static` o `2 - AR - Motion`. Si tiene ambos tipos, el mercado se llama `1 - BR` y contiene hijos inmediatos `Static` y `Motion`. India siempre muestra idioma; otros mercados, como Canadá, lo muestran cuando hay múltiples entregas lingüísticas.

## Qué preserva y qué ignora

Se conserva la jerarquía semántica completa, incluso cuando aparece antes o después de `Stills`/`Video`: concepto, ejecución, CTA, CTA Alt, Test A/B, hook, personaje, audiencia, copy y variantes de entrega. Por ejemplo, `Hairstyle/Test A` y `Color Analysis/Test A` nunca se mezclan aunque sus filenames sean iguales o contradictorios. La ruta fuente semántica tiene prioridad sobre el filename.

Los wrappers técnicos no crean niveles: `Regions`, país/idioma, `Stills`, `Static`, `Video`, `Motion`, `Motion 11`, formatos `1x1`, `4x5`, `9x16`, resoluciones, duración, fecha, IDs, mercado y plataforma. El parser anclado de filename es el mismo para Static y Motion; puede enriquecer `Wrestling` con `ButNow` para producir `Wrestling - ButNow` o recuperar `Something To Wear` cuando no hay carpeta de concepto.

La organización procesa solo Meta y TikTok/TT. YouTube, spreadsheets, trackers, ZIPs y cualquier material no soportado quedan exactamente donde estaban; no existe una carpeta `Otros`. Tampoco se crean carpetas vacías desde una plantilla global. Meta y TikTok conviven sin nivel de plataforma cuando sus filenames son distintos; `Meta`/`TikTok` aparece solo si resuelve de forma segura una colisión entre plataformas.

## Colisiones, duplicados y seguridad

Creative Organizer nunca sobrescribe. Ante una colisión intenta primero una separación justificable por plataforma; si no alcanza, deja los archivos en origen para revisión. Los duplicados byte a byte también se conservan en ambos lugares: no se elimina información para “limpiar” el árbol.

Apply es transaccional. Si un movimiento falla, los movimientos ya hechos vuelven a sus rutas originales. La segunda ejecución sobre un lanzamiento ya ordenado es idempotente y no agrega niveles ni renumera carpetas. `Undo` revierte la última ejecución exitosa, restaura la jerarquía fuente y luego consume ese registro; repetir Undo no modifica nada.

## Desarrollo y pruebas

El motor está en `Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py` y la interfaz nativa activa en `Organizador.m`. La suite usa solamente la biblioteca estándar y directorios temporales:

```sh
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/creative-organizer-test-pycache python3 -m py_compile 'Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py'
```

El runtime objetivo es Python 3.9. Al publicar una etiqueta `vX.Y.Z`, GitHub prepara el ZIP instalable del release.
