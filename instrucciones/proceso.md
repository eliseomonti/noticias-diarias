# Proceso diario

Los pasos para producir y publicar la edición. Qué contar y cómo está en `editorial.md`; cómo se organiza, en `estructura.md`.

## Qué es de quién

- Vos escribís solo `contenido/{FECHA_ISO}.html`.
- `fuentes.txt`, `instrucciones/`, `scripts/` y `plantilla/` son del lector: nunca los modifiques. Si algo de eso falla, no lo arregles: seguí como puedas y reportalo en el resultado final. Si falta alguno, recuperalo con `git checkout $(git rev-list -n 1 HEAD -- RUTA)~1 -- RUTA` y avisalo.
- `ediciones/`, `index.html` y `feed.xml` los genera `scripts/publicar.py`: no los edites a mano.

## 1. Fecha

`TZ=America/Argentina/Buenos_Aires date +%F` es FECHA_ISO; FECHA es la misma fecha en formato DD/MM/AAAA. La edición cubre las últimas ~24 horas; los indicadores de mercado pueden ser del último cierre hábil (siempre con su fecha).

## 2. Material

a. Ejecutá `python3 scripts/fuentes.py fuentes.txt 30 /tmp/links.txt > /tmp/digest.txt` y leé /tmp/digest.txt completo (por partes). Por sección (DATOS, AR, MDP, MUNDO, TECH, DEP, VOCES) trae titulares con fecha y hora, bajadas y un número #N; la URL de la noticia #N se obtiene con `grep '^N ' /tmp/links.txt`. Al final está el estado de las fuentes (con error, vacías, con respaldo).
b. Lo que sigue a `NOTA:` junto al nombre de una fuente lo escribió el lector en `fuentes.txt`: indica cómo usar esa fuente (por ejemplo, que es una agencia o que no se abra con WebFetch). Seguilo.
c. Edición anterior: leé los títulos (los `<strong>`) del archivo más reciente de `contenido/` anterior a FECHA_ISO. No repitas historias ya cubiertas salvo que haya un hecho nuevo; en ese caso contá solo la novedad, con una frase de contexto.
d. Para ampliar una noticia importante, abrí la nota (URL de links.txt) con WebFetch o buscá con WebSearch, salvo que la nota de la fuente diga que no se use WebFetch: en ese caso usá el título y la bajada para detectar la noticia y, si no alcanzan, corroborá los hechos en otro medio del digest o con WebSearch; si no podés, limitá lo que afirmás.
e. Links: preferí el link directo del medio; si solo tenés el de Google News, usá ese.
f. Si fallan fuentes, seguí con las demás. Publicá SIEMPRE con lo que hayas podido verificar. Solo abortá si no conseguiste ninguna noticia verificable del día.

## 3. Escribir

Escribí `contenido/{FECHA_ISO}.html` con SOLO el cuerpo de la edición, en HTML simple (`<h1>`, `<h2>`, `<p>`, `<ul>`, `<li>`, `<strong>`, `<a>`): sin `<html>`, `<head>`, `<style>`, imágenes, JavaScript ni el pie "Todas las ediciones", porque eso lo agrega la plantilla. Empieza con `<h1>Noticias — {FECHA}</h1>` y sigue con las secciones de `estructura.md`. Si el archivo ya existe (ejecución repetida), rehacelo de cero con el digest actual, sin mirar la versión anterior.

## 4. Publicar

a. Ejecutá `python3 scripts/publicar.py {FECHA_ISO}`. Revisa el contenido del día, lo envuelve con la plantilla, regenera todas las ediciones, `index.html` y `feed.xml`, y borra lo que tenga más de 60 días. Si informa ERRORES, corregí `contenido/{FECHA_ISO}.html` y volvé a ejecutarlo. Usá su resumen (palabras por sección y avisos) para la revisión final de `estructura.md`; si corregís algo, ejecutalo de nuevo.
b. `git add -A contenido ediciones index.html feed.xml` (solo eso), commit con el mensaje "Edición {FECHA_ISO}" y `git push origin HEAD:main`. Si lo rechaza, hacé `git pull --rebase origin main` y reintentá una vez (si el rebase da conflicto, `git rebase --abort`). Si vuelve a fallar, NO lo subas a otra rama: informá el error exacto.
c. Si `publicar.py` falla por un error propio (no por el contenido), no lo arregles: subí igual `contenido/{FECHA_ISO}.html` con `git add contenido`, así se publica en la próxima ejecución, y reportalo.

## 5. Aviso y resultado

a. Después del push, armá el TEXTO DEL AVISO: una sola línea sin markdown: "Noticias DD/MM: " + los 2-3 titulares principales del Panorama muy resumidos, separados por " · ", + " eliseomonti.github.io/noticias-diarias". Contá sus caracteres con Python (len): tienen que ser menos de 200; si no, acortalo. Si la edición no se publicó, el aviso dice eso y el motivo.
b. Enviá el aviso con la herramienta PushNotification (si no aparece cargada, buscala con ToolSearch).
c. Terminá con este mensaje: primera línea, el texto del aviso idéntico; después "Edición: (URL)", "Fuentes con problemas: (según el estado de fuentes del digest)" y "Otros problemas: (o ninguno)". Si no pudiste enviar el aviso, decilo.
