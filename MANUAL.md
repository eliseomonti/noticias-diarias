# Manual de noticias-diarias

Referencia completa del sistema: cómo funciona, cómo se cambia cada cosa, qué problemas ya aparecieron y por qué se decidió lo que se decidió. El `README.md` es el mapa rápido; este archivo es el detalle.

> Este repositorio es público. No pongas acá datos privados: el perfil del lector vive en la tarea programada.

---

## 1. Qué es y dónde vive cada cosa

| Pieza | Dónde | Qué tiene |
|---|---|---|
| Tarea programada "Resumen diario de noticias" | claude.ai/code/routines (cuenta del lector, privada) | Horario, modelo, entorno y una instrucción corta: rol, regla de seguridad, **perfil del lector** y la orden de leer `instrucciones/` |
| Repositorio | github.com/eliseomonti/noticias-diarias (público) | Todo lo demás: fuentes, instrucciones, scripts, plantilla, ediciones |
| Web | https://eliseomonti.github.io/noticias-diarias/ (GitHub Pages, rama `main`, raíz) | Se actualiza ~1 minuto después de cada push |
| Feed RSS | https://eliseomonti.github.io/noticias-diarias/feed.xml | Lo lee el Kindle (KOReader) |
| Aviso al celular | App de Claude | La sesión en la nube lo manda con la herramienta PushNotification |

**Configuración de la tarea**
- Horario: todos los días 7:00 hora argentina (cron `0 10 * * *` en UTC). Suele arrancar unos minutos después (~7:10).
- Modelo: Claude Sonnet 5.5.
- Entorno: "Noticias", con **acceso completo a la red**. El entorno por defecto bloquea los dominios de los medios (error `ENOTFOUND`).
- Sin conectores (no hacen falta: todo pasa por git y la web).
- Cada ejecución consume uso del plan de Claude, como una sesión normal (~3-15 minutos).

---

## 2. Flujo diario

1. La nube clona el repo y arranca la sesión con la instrucción de la tarea.
2. El agente hace `git fetch origin main && git checkout -B main origin/main` y lee `instrucciones/proceso.md`, `editorial.md` y `estructura.md`.
3. Corre `python3 scripts/fuentes.py fuentes.txt 30 /tmp/links.txt > /tmp/digest.txt`: descarga ~85 fuentes y arma un digest de ~1.200 titulares (~300 KB).
4. Lee el digest y los títulos de la edición anterior; amplía con WebFetch/WebSearch cuando hace falta.
5. Escribe solo el cuerpo en `contenido/AAAA-MM-DD.html`.
6. Corre `python3 scripts/publicar.py AAAA-MM-DD`: revisa el contenido; si hay errores, sale con código 1 y el agente corrige; si no, regenera `ediciones/`, `index.html` y `feed.xml`.
7. `git add -A contenido ediciones index.html feed.xml`, commit "Edición AAAA-MM-DD", push a `main`.
8. Manda el aviso (titulares en una línea de menos de 200 caracteres) y termina con un mensaje que lista las fuentes con problemas.

**Regla de propiedad:** el agente solo escribe `contenido/`. Nunca modifica `fuentes.txt`, `instrucciones/`, `scripts/` ni `plantilla/`; si algo de eso falla, lo reporta. `ediciones/`, `index.html` y `feed.xml` son salidas generadas: no se editan a mano.

---

## 3. Contratos entre las piezas

Cada pieza conoce de las otras solo lo que dice esta sección. Si cambiás un contrato, revisá a los dos lados.

### 3.1 `fuentes.txt`

```
SECCION | nombre | url | nota
```
- Secciones: `AR`, `MDP`, `MUNDO`, `TECH`, `DEP`, `VOCES` (opinión), `DATOS` (APIs JSON). Las líneas que empiezan con `#` se ignoran.
- `nombre` tiene que ser único (las notas se asocian por nombre).
- `nota` es opcional y no puede tener `|`. El digest la muestra como `NOTA:` junto al nombre; el agente la trata como instrucción del lector. Se usa para: "agencia de noticias", "no usar WebFetch", "verificador de datos", cómo informar un dato, etc.
- Filtro por título: agregar `#solo=palabra` al final de la URL deja solo las notas cuyo título contiene esa palabra (sin distinguir mayúsculas). Ejemplo: el canal de Gelatina filtrado por `rosemblat`.
- DATOS: el script elige cómo resumir según la URL: `dolarapi`, `open-meteo`, `finance/chart` (Yahoo), `api.bcra.gob.ar`. Cualquier otra API se muestra cruda (JSON recortado a 3.000 caracteres). Para una API nueva con formato propio hay que agregar una función `dato_*` en `scripts/fuentes.py`.

### 3.2 El digest (`scripts/fuentes.py`)

- Ventana: 30 horas; la sección VOCES, 72 horas (`VENTANA` en el script).
- Por feed ordenado por fecha: hasta 20 notas (las 8 más nuevas + 12 repartidas en la ventana). Portadas de Google News (`news.google.com/rss?…` o `/headlines/`): las primeras 25, en orden de importancia.
- Formato:
  ```
  ======== SECCION ========
  ## Nombre (N items, por fecha|por importancia) NOTA: …
  - [dd/mm hh:mm] Título | cubren(3): Medio A, Medio B, Medio C #123
      bajada…
  ```
- La URL de la noticia `#123` está en `/tmp/links.txt` (`grep '^123 ' /tmp/links.txt`).
- `cubren(N)` = medios distintos que publicaron la misma noticia según Google News. Solo significa algo en las portadas; en las búsquedas casi siempre es 1.
- Al final: "ESTADO DE FUENTES" con las que dieron error (con su nota), las vacías y las que usaron respaldo.
- Respaldos automáticos: si open-meteo falla, usa wttr.in; si Yahoo falla, reintenta con `query2`.

### 3.3 `contenido/AAAA-MM-DD.html`

- Solo el cuerpo: empieza con `<h1>Noticias — DD/MM/AAAA</h1>`; sin `<html>`, `<head>`, `<body>`, `<style>`, `<meta>`, `<title>` ni el pie "Todas las ediciones".
- Etiquetas simples: `h1`, `h2`, `p`, `ul`, `ol`, `li`, `strong`, `em`, `a`.
- Es la fuente de verdad de cada edición: las páginas se regeneran a partir de acá.

### 3.4 `scripts/publicar.py`

- `python3 scripts/publicar.py AAAA-MM-DD`: revisa ese contenido y publica todo. `python3 scripts/publicar.py` (sin fecha): solo regenera todo (por ejemplo, después de cambiar la plantilla).
- Errores (no publica, sale con código 1): archivo vacío; etiquetas de página completa; pie incluido; no hay exactamente un `<h1>`; paréntesis vacíos, `href=""`, `href="#…"`, links sin texto; etiquetas abiertas y cerradas en distinta cantidad.
- Avisos (publica igual): expresiones de tiempo relativo ("hoy", "ayer", "este jueves"…).
- Resumen: palabras totales y por sección (`<h2>`), para controlar las proporciones de `estructura.md`.
- Publica: una página por contenido en `ediciones/` (borra las que no tienen contenido), `index.html` con todas, `feed.xml` (RSS 2.0) con las 14 más recientes (`pubDate` a las 07:00 -0300, descripción = cuerpo escapado). Borra contenidos de más de 60 días (hora argentina). Valida que el feed sea XML válido.
- Constantes al principio del archivo: `BASE`, `DIAS`, `EN_FEED`.

### 3.5 `plantilla/`

- `pagina.html`: marcadores `{titulo}`, `{raiz}` (`../` en ediciones, vacío en el índice), `{base}` (URL del sitio), `{cuerpo}` y `{pie}`. Incluye `<meta name="robots" content="noindex">` y el link al CSS.
- `estilo.css`: modo oscuro siempre. Un solo archivo para todas las páginas.
- El feed no usa la plantilla (KOReader recibe solo el cuerpo).

### 3.6 `instrucciones/`

- `proceso.md`: pasos (fecha, material, escribir, publicar, git, aviso, mensaje final).
- `editorial.md`: redacción, relevancia, sesgos y certeza, tipos de material (DATOS, VOCES, TECH, deportes).
- `estructura.md`: extensión, proporciones, secciones (`<h2>` exactos), formato de cada noticia y revisión final.
- Se refieren al "perfil del lector" de la tarea para intereses y orden de los deportes, y a la sección VOCES del digest para saber qué voces vale incluir. No nombran fuentes puntuales: eso va en las notas de `fuentes.txt`.

---

## 4. Tareas comunes, paso a paso

### Sumar o sacar una fuente
1. Buscar el feed: `<link rel="alternate" type="application/rss+xml">` en el HTML del sitio, o probar `/feed`, `/feed/`, `/rss`, `/rss.xml`. En sitios Arc (Infobae, La Nación, Clarín, Cronista…): `/arc/outboundfeeds/rss/?outputType=xml` o `/arc/outboundfeeds/rss/category/SECCION/`. Preferir feeds de **sección** (Política, Economía): los generales de los medios grandes cubren pocas horas.
2. Si no hay feed o bloquea: búsqueda de Google News `https://news.google.com/rss/search?q=site:DOMINIO+when:1d&hl=es-419&gl=AR&ceid=AR:es-419` (en inglés: `hl=en-US&gl=US&ceid=US:en`).
3. Agregar la línea a `fuentes.txt` con su nota si hace falta.
4. Probar: `python3 scripts/fuentes.py fuentes.txt 30 /tmp/links.txt > /tmp/digest.txt` y mirar la sección y el "ESTADO DE FUENTES".
5. Commit y push (o editar `fuentes.txt` directo en la web de GitHub).

Ojo: algo que funciona desde una PC en Argentina puede estar bloqueado desde la nube. Se ve en "Fuentes con problemas" del mensaje final de la ejecución siguiente.

### Sumar una voz (VOCES)
- YouTube: `https://www.youtube.com/feeds/videos.xml?channel_id=UC…`. El `channel_id` aparece como `"externalId":"UC…"` en el HTML de `youtube.com/@usuario`. Si el canal es compartido con otros conductores, filtrar con `#solo=apellido`.
- Columnistas o personas que salen en medios: búsqueda de Google News con exclusiones para el chimento, por ejemplo `q=%22Nombre+Apellido%22+-boda+-rating+when:3d`, con la nota "búsqueda en Google News: usá solo las notas sobre lo que dijo o analizó…".
- No hace falta tocar las instrucciones: las voces válidas son las de la sección VOCES.

### Cambiar el criterio, las secciones o los pasos
Editar `instrucciones/editorial.md`, `estructura.md` o `proceso.md`. Rige desde la próxima ejecución.

### Cambiar el estilo o el HTML
Editar `plantilla/estilo.css` o `plantilla/pagina.html`, correr `python3 scripts/publicar.py` (sin fecha) para regenerar todas las páginas, commit y push.

### Cambiar el perfil, los intereses, el horario o el modelo
En claude.ai/code/routines → "Resumen diario de noticias" → editar. El perfil va ahí porque es privado. Mantener la instrucción corta: lo que no sea perfil, seguridad o arranque va en `instrucciones/`.

### Probar localmente
```
python3 scripts/fuentes.py fuentes.txt 30 /tmp/links.txt > /tmp/digest.txt   # no modifica el repo
python3 scripts/publicar.py AAAA-MM-DD                                          # sí modifica ediciones/, index.html, feed.xml
```
Para probar `publicar.py` sin ensuciar el repo, hacerlo en una copia (`cp -r`) o descartar después con `git checkout -- ediciones index.html feed.xml`.

### Lanzar una ejecución de prueba
En claude.ai/code/routines → la tarea → la opción de ejecutarla ahora. Rehace de cero la edición del día (la anterior queda en el historial de git). El resultado y el registro de la sesión se ven en el historial de ejecuciones de la tarea.

### Recuperar algo roto
- Una edición: `git log -- contenido/AAAA-MM-DD.html` y `git checkout COMMIT -- contenido/AAAA-MM-DD.html`, después `python3 scripts/publicar.py`.
- Un archivo del lector: el agente lo recupera solo del historial si falta, y lo avisa.

---

## 5. Problemas conocidos

| Síntoma | Causa | Solución vigente |
|---|---|---|
| `ENOTFOUND` al descargar | Entorno de la nube sin red completa | Usar el entorno "Noticias" |
| WebFetch no lee BBC, Reuters, El País, Clarín, Olé, TyC, The Verge, Ars Technica, Times of Israel | Bloquean lecturas automáticas | Nota "no usar WebFetch" en esas fuentes: título, bajada y corroborar en otro medio |
| Merval "HTTP 429" | Yahoo Finance limita a las IP de la nube | Respaldo `query2`; si falla, el agente lo toma de "Google News Merval" con atribución |
| Clima con "(wttr.in, respaldo)" | open-meteo limita a IP compartidas (429) | Respaldo automático a wttr.in |
| Fuente con 403 desde la nube | El sitio bloquea centros de datos (La Capital, Times of Israel) | Entrar por Google News `site:` |
| Pocas notas de un medio grande | Su feed general cubre 2-3 horas | Usar feeds de sección |
| Feed con basura (por ejemplo, notas en inglés de "trucos caseros" en El Cronista general) | Contenido SEO | Usar feeds de sección |
| Notas viejas en búsquedas `when:1d` | Google News no respeta del todo el filtro | El script descarta todo lo que está fuera de la ventana |
| Claude Docs no aparece en la tarea | El conector no está disponible en tareas programadas | Se publica con GitHub Pages |
| No llega el aviso | Permiso de notificaciones de la app de Claude | Activarlo en el celular |
| No se puede reemplazar un archivo del Kindle por USB | El Kindle usa MTP, que no permite sobrescribir | Borrar el archivo y copiar el nuevo |

---

## 6. Kindle (KOReader)

- Archivo: `koreader/news/feed_config.lua` en el almacenamiento interno:
  ```lua
  return {
      {
          "https://eliseomonti.github.io/noticias-diarias/feed.xml",
          limit = 3,                       -- últimas 3 ediciones
          download_full_article = false,   -- el feed ya trae la edición completa
          include_images = false,
          enable_filter = false,
          filter_element = "",
      },
  }
  ```
- Uso: Wi-Fi → Herramientas → Descargador de noticias → Descargar noticias. Las ediciones quedan en `koreader/news/`. La descarga es manual.
- Desde Linux (KDE) el Kindle se ve por MTP: `kioclient ls 'mtp:/'`. Para reemplazar un archivo: `kioclient remove` y después `kioclient copy`.

---

## 7. Decisiones y su porqué

- **Web pública en GitHub Pages:** gratis y simple. Un sitio privado de verdad requiere otro hosting con login, y KOReader no puede iniciar sesión. Pages desde un repo privado necesita GitHub Pro y el sitio igual es público.
- **`noindex` y no `robots.txt`:** el sitio es de proyecto (`/noticias-diarias/`) y los buscadores solo leen el `robots.txt` de la raíz del dominio. `noindex` saca las páginas de los resultados; quien tenga el link las sigue viendo. La página del repo en github.com sigue siendo indexable.
- **Web + Kindle, sin lector de RSS:** al lector no le gustan los lectores RSS clásicos; el feed existe solo para el Kindle. Telegram descartado.
- **Fuentes por RSS, Google News y APIs** en vez de navegar sitios: es más rápido y estable, y muchos sitios bloquean lecturas automáticas.
- **Agencias como base de los hechos:** Reuters, AP, EFE y Noticias Argentinas.
- **Balance de líneas editoriales:** medios de distintas líneas en AR; en VOCES, miradas críticas del kirchnerismo (Pagni, Longobardi) y cercanas al peronismo (Rosemblat, Rebord), además de Solo Fonseca; en Medio Oriente, Al Jazeera y Times of Israel; en EE.UU., NYT/Guardian y WSJ.
- **Descartados** (evaluados el 26/11/2026): medios estatales (RT, Global Times, People's Daily); canales de TV (C5N, A24, Crónica); diarios provinciales (lo nacional llega por Google News); pagos o redundantes (FT, Economist, Washington Post, Politico, Axios, iProfesional, Radio Mitre); feeds muertos (CNN, Spiegel International, El Tiempo); Punto Noticias (solo con basura en Google News); LPO (mucho rumor); regionales lejanos y ciencia (fuera de foco). Sin feed posible: Boletín Oficial, INDEC (sus datos llegan por la API del BCRA), AFP.
- **Pospuestos:** sección o tarea de empleo tech, lista de intereses detallada, más medios de Brasil (Folha) o Medio Oriente (Haaretz, Al-Monitor).
- **Arquitectura (27/11/2026):** antes, la instrucción de la tarea tenía todo (~30 KB, incluido el script completo con control por hash) y cada cambio obligaba a reenviarla. Ahora cada responsabilidad está en un archivo del repo; la tarea solo tiene lo privado y el arranque. Los cambios se hacen con commits.
