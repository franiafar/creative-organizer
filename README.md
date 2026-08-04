# Creative Organizer

Aplicacion para macOS que reorganiza creativos de lanzamientos sin duplicar archivos.

## Uso

1. Copia la columna `Country` de la trafficking sheet si queres respetar ese orden.
2. Abre `Creative Organizer.app`.
3. Elige `Ordenar` y selecciona la carpeta del lanzamiento.

Los mercados que no figuren en la columna copiada se agregan despues, en orden alfabetico.

La aplicacion crea carpetas por mercado, por ejemplo `01 - IN HI - St`, y conserva variantes intermedias como `Alt CTA/CaricatureRefreshKawaii - Female`. Separa `Static` y `Motion` cuando corresponde, envia archivos sin clasificar a `Otros` y elimina archivos de sistema como `.DS_Store`.

`Deshacer el ordenamiento anterior` revierte solamente la ultima organizacion realizada desde la aplicacion.

## Descargar la ultima version

La ultima version instalable siempre se descarga desde:

`https://github.com/franiafar/creative-organizer/releases/latest/download/Creative-Organizer.zip`

Descomprime el archivo y abre `Creative Organizer.app`.

La aplicacion incluye todo lo necesario para funcionar. No requiere instalar Python, Xcode ni herramientas de desarrollo.

## Publicar una version

Al crear y subir una etiqueta con formato `vX.Y.Z`, GitHub genera el ZIP y publica una release automaticamente.

## Codigo

- `Creative Organizer.app/Contents/Resources/Organizador.m`: interfaz nativa de macOS.
- `Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py`: reglas de deteccion y movimiento de creativos.
