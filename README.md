# noticias-diarias

Resumen diario de noticias (mundo, Argentina y Mar del Plata) que arma una tarea programada de Claude todos los días a las 7:00 (hora argentina).

- Web: https://eliseomonti.github.io/noticias-diarias/
- Feed RSS (Kindle con KOReader): https://eliseomonti.github.io/noticias-diarias/feed.xml
- Manual completo (contratos entre piezas, tareas paso a paso, problemas conocidos, decisiones): [MANUAL.md](MANUAL.md)

## Cómo está armado

Cada pieza tiene una sola responsabilidad. Para cambiar algo, se toca un solo lugar:

| Quiero cambiar… | Archivo |
|---|---|
| Qué fuentes se leen y cómo usar cada una (nota) | `fuentes.txt` |
| Criterio editorial: relevancia, sesgos, redacción | `instrucciones/editorial.md` |
| Secciones, cantidades y proporciones | `instrucciones/estructura.md` |
| Pasos del proceso (digest, publicar, git, aviso) | `instrucciones/proceso.md` |
| Estilo visual (modo oscuro, tipografía) | `plantilla/estilo.css` |
| Estructura HTML de las páginas (meta, noindex, pie) | `plantilla/pagina.html` |
| Cómo se descargan y resumen las fuentes | `scripts/fuentes.py` |
| Cómo se generan las páginas, el índice y el feed | `scripts/publicar.py` |
| Perfil e intereses del lector, horario | la tarea programada (privada, en claude.ai/code/routines) |

## Flujo diario

1. La tarea clona el repo y lee `instrucciones/`.
2. `scripts/fuentes.py` descarga las fuentes de `fuentes.txt` y arma un digest.
3. El agente elige y redacta, y escribe solo el cuerpo en `contenido/AAAA-MM-DD.html`.
4. `scripts/publicar.py AAAA-MM-DD` revisa el contenido, lo envuelve con `plantilla/` y regenera `ediciones/`, `index.html` y `feed.xml` (borra lo de más de 60 días).
5. El agente hace commit y push, y manda un aviso al celular.

`contenido/` es la fuente de verdad; `ediciones/`, `index.html` y `feed.xml` se generan. Después de cambiar la plantilla, `python3 scripts/publicar.py` (sin fecha) regenera todo.
