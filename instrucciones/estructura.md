# Estructura de la edición

Cómo se organiza el cuerpo (`contenido/{FECHA_ISO}.html`). La presentación (estilo, modo oscuro, pie) la pone la plantilla.

## Extensión y proporciones

~9-12 minutos de lectura (1.800-2.500 palabras). Proporciones aproximadas: el núcleo (Panorama, Argentina, Mundo, Mar del Plata) al menos el 70% del texto; Tecnología e IA entre el 15% y el 20%; Deportes y Voces, juntos, no más del 10%. Las cantidades son objetivos, no mínimos: si no hay suficientes noticias relevantes, poné menos. Nunca rellenes.

## Secciones

Título `<h1>`: "Noticias — {FECHA}". Usá exactamente estos títulos `<h2>` y ningún otro (por ejemplo, no agregues un `<h2>` "Argentina": Política y Economía van como dos `<h2>` propios):

1. "Panorama": primero una línea con el clima de hoy en Mar del Plata (estado del cielo, máxima, mínima, probabilidad de lluvia; el viento solo si las ráfagas llegan a 50 km/h o más). Después las 3-5 noticias más importantes del día, de cualquier tema (también tecnología, IA o deportes si son noticia de tapa), una línea cada una, de mayor a menor relevancia. Cada una se desarrolla después en su sección.
2. Bloques principales (Argentina, Mundo, Mar del Plata): el bloque de la noticia de Argentina, Mundo o Mar del Plata mejor ubicada en el Panorama va primero y los demás siguen el orden de su primera aparición (las de tecnología, IA o deportes no cuentan para este orden); si no hay una diferencia clara, el orden es Argentina, Mundo, Mar del Plata. Dentro de cada sección, de mayor a menor relevancia: cada noticia del Panorama encabeza su sección.
   - Argentina: "Política argentina" (hasta 5 noticias; incluye las relaciones exteriores de Argentina, por ejemplo un conflicto diplomático con Brasil) y "Economía argentina" (primero una línea de indicadores: dólar oficial, blue, MEP y CCL a precio de venta, riesgo país, Merval, reservas del BCRA e inflación del último mes informado por el INDEC, cada uno con su fecha; después hasta 4 noticias), siempre seguidas.
   - "Mundo" (hasta 7): cubrí en lo posible EEUU, Europa, China/Asia, América Latina y Medio Oriente u otras regiones, según lo que haya pasado. Todas las novedades de un mismo conflicto van en UNA sola noticia.
   - "Mar del Plata" (hasta 4): municipio, ciudad, servicios, temporada/turismo, puerto.
3. "Tecnología e IA", después de los bloques principales: hasta 5 noticias, de mayor a menor relevancia. Priorizá inteligencia artificial (modelos y lanzamientos importantes, regulación, impacto en el trabajo y la economía, seguridad, investigación) y completá con software, ciberseguridad, chips, empresas tecnológicas y mercado laboral tech. Cada una con 2-4 oraciones: qué pasó, por qué importa y, si corresponde, qué significa para Argentina o para quien trabaja en tecnología. Evitá gadgets, ofertas y rumores; si no hay suficientes noticias relevantes, poné menos.
4. Al final y breve:
   - "Deportes — en breve" (4-6 líneas en total, en el orden de prioridad de deportes del perfil del lector y solo con esos deportes). Solo lo relevante, con el resultado o marcador cuando informes un partido.
   - "Voces (opinión)" (1-4 líneas: qué tema analizó cada voz y cuál fue su mirada, atribuido y con link; si varias voces analizaron el mismo tema, juntalas en una línea con sus distintas miradas; solo las voces de la sección VOCES del digest, ningún otro columnista; si no hay nada nuevo, omitila).

## Cada noticia

- Una noticia = un hecho (o las novedades de un mismo conflicto). No juntes en un párrafo hechos sin relación por compartir región o tema ("Temporada y puerto", "España y Europa") para entrar en el límite: elegí los más relevantes.
- Las del núcleo y de Tecnología e IA: título en `<strong>` que diga qué pasó, con sujeto y verbo ("Brasil retiró a su embajador en Buenos Aires", no "Medio Oriente" ni "Presión interna"), + 2-3 oraciones (2-4 en Tecnología e IA: qué pasó y por qué importa) + link a la fuente principal, con el nombre del medio como texto del link.
- Fechas absolutas ("el jueves 26/11"), nunca "hoy", "ayer" ni "este jueves": el lector puede leerlo otro día.
- Nunca dejes paréntesis vacíos "()", links sin texto ni href vacíos; si no tenés el link de algo, nombrá la fuente sin link.

## Revisión final

Antes de publicar, releé la edición y corregí: que cada título coincida con su texto; que el Panorama no afirme nada con más certeza que su nota; que cada ítem del Panorama esté desarrollado y encabece su sección; que las proporciones se acerquen a las de arriba (usá las palabras por sección que informa `publicar.py`); nombres propios e índices exactos (por ejemplo S&P Merval); ortografía ("e" antes de i- o hi-, "u" antes de o- u ho-); y que no queden "hoy" ni "este jueves".
