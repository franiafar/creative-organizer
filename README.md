# Creative Organizer

Aplicacion para macOS que ordena carpetas de creativos por mercado, tipo de pieza y variante creativa. Trabaja sobre los archivos que ya existen: los mueve y renombra, pero no los duplica.

## Descarga

[Descargar siempre la ultima version](https://github.com/franiafar/creative-organizer/releases/latest/download/Creative-Organizer.zip)

El link es permanente: cuando publiquemos una nueva version, descarga automaticamente esa version.

Tambien podes ver el historial de versiones en [Releases](https://github.com/franiafar/creative-organizer/releases).

## Instalar en Mac

1. Descarga `Creative-Organizer.zip` desde el link de arriba.
2. Hace doble click sobre el ZIP para descomprimirlo.
3. Abri `Creative Organizer.app`.

Si macOS muestra una alerta la primera vez, hace Control + click sobre la app, elegi `Abrir` y confirmalo. No hace falta instalar Python, Xcode ni herramientas de desarrollo: la app ya trae todo lo necesario.

## Uso diario

1. Opcional: en la trafficking sheet, copia la columna `Country` completa. La app usara la primera aparicion de cada mercado para asignar el orden de las carpetas.
2. Abri `Creative Organizer.app` y elegi `Organizar`.
3. Selecciona la carpeta madre del lanzamiento. No elijas una carpeta de pais individual ni un ZIP suelto.
4. Espera el mensaje de confirmacion: muestra los mercados que detecto y la carpeta queda lista para publicar.

Los mercados que no aparezcan en el paste de la trafficking sheet quedan despues de los incluidos, en orden alfabetico.

## Resultado

La app crea una estructura de carpetas practica para subir las piezas por mercado. Por ejemplo:

```text
13 Jul Ramadam TT
├── 01 - US
│   ├── Static
│   └── Motion
├── 02 - IN EN - St
│   └── Caricature
└── 03 - AR - Mt
    └── Female
```

Cuando un mercado tiene un unico tipo de pieza, lo aclara en el nombre: `- St` para static y `- Mt` para motion. Si tiene ambos, genera las carpetas `Static` y `Motion`. Las separaciones útiles dentro de los creativos, como CTA, Men/Women o personajes, se preservan; las carpetas genéricas como `Motion 11` se omiten.

## Reglas que reconoce

La app reconoce códigos de dos letras y nombres completos de países, incluyendo formatos como `Australia`, `Canada`, `UK`, `GB`, `AU EN` o nombres compactos. Para mercados con varios idiomas, usa el código de idioma solo cuando hace falta identificar la variante. India siempre muestra idioma: `IN EN`, `IN HI` o `IN RO`.

Los ZIPs, spreadsheets y otros archivos que no correspondan a un creativo de mercado se agrupan dentro de `Otros`. Los archivos de sistema vacíos o de macOS no se conservan como carpetas intermedias.

## Deshacer

Al abrir la app, elegi `Deshacer el ordenamiento anterior` para revertir **solamente el ultimo** lanzamiento que organizo Creative Organizer. No pide volver a elegir una carpeta: recuerda internamente el ultimo lanzamiento. Usalo antes de organizar otra carpeta si queres volver atras.

## Guia visual

[Ver la guia visual de instalacion y uso](https://creative-organizer-guide.dept-7420.chatgpt.site)

## Desarrollo

- `Creative Organizer.app/Contents/Resources/Organizador.m`: interfaz nativa de macOS.
- `Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py`: reglas de deteccion y movimiento de creativos.

Al publicar una etiqueta con formato `vX.Y.Z`, GitHub arma automaticamente un nuevo ZIP instalable en Releases.
