#!/usr/bin/env python3
"""Publica las ediciones.

Cada contenido/AAAA-MM-DD.html (solo el cuerpo, escrito por el agente) se envuelve con
plantilla/pagina.html y se escribe en ediciones/. Además regenera index.html y feed.xml,
borra lo que tenga más de DIAS días y revisa el contenido de la fecha indicada.

Uso:
  python3 scripts/publicar.py AAAA-MM-DD   revisa ese contenido y, si no tiene errores, publica todo
  python3 scripts/publicar.py              solo regenera todo (por ejemplo, después de cambiar la plantilla)

Sale con código 1 si el contenido del día tiene errores (en ese caso no escribe nada).
"""
import datetime as dt
import glob
import html
import os
import re
import sys
import xml.etree.ElementTree as ET
from email.utils import format_datetime

BASE = 'https://eliseomonti.github.io/noticias-diarias/'
DIAS = 60       # antigüedad máxima de una edición
EN_FEED = 14    # ediciones en feed.xml
MIN_PALABRAS = 1200  # por debajo, aviso de edición anormalmente corta
ART = dt.timezone(dt.timedelta(hours=-3))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIE = f'<p><a href="{BASE}">← Todas las ediciones</a></p>'
TIEMPO_RELATIVO = re.compile(r'\b(hoy|ayer|anoche|anteayer|pasado mañana|este (lunes|martes|miércoles|jueves|viernes|sábado|domingo))\b', re.I)
VACIOS = [(r'\(\s*\)', 'paréntesis vacíos'), (r'href=""', 'href vacío'), (r'href="#', 'href con #'),
          (r'<a [^>]*>\s*</a>', 'link sin texto')]
ETIQUETAS = ('a', 'p', 'h1', 'h2', 'h3', 'strong', 'em', 'ul', 'ol', 'li')


def ruta(*partes):
    return os.path.join(RAIZ, *partes)


def leer(*partes):
    with open(ruta(*partes), encoding='utf-8') as f:
        return f.read()


def escribir(rel, texto):
    with open(ruta(rel), 'w', encoding='utf-8') as f:
        f.write(texto)


def ddmmaaaa(iso):
    return dt.date.fromisoformat(iso).strftime('%d/%m/%Y')


def pagina(titulo, cuerpo, raiz, pie):
    t = leer('plantilla', 'pagina.html')
    for clave, valor in (('{titulo}', html.escape(titulo)), ('{raiz}', raiz), ('{base}', BASE), ('{pie}', pie)):
        t = t.replace(clave, valor)
    return t.replace('{cuerpo}', cuerpo.strip())  # el cuerpo va al final: su texto nunca se interpreta


def ediciones():
    """Fechas ISO de contenido/, de la más reciente a la más vieja."""
    fechas = [os.path.basename(p)[:-5] for p in glob.glob(ruta('contenido', '*.html'))]
    return sorted((f for f in fechas if re.fullmatch(r'\d{4}-\d{2}-\d{2}', f)), reverse=True)


def texto(fragmento):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragmento)).split())


def revisar(cuerpo):
    errores, avisos = [], []
    if not cuerpo.strip():
        return ['el archivo está vacío'], [], []
    if re.search(r'<(!doctype|html|head|body|style|meta|title)\b', cuerpo, re.I):
        errores.append('tiene que tener solo el cuerpo: sin <html>, <head>, <body>, <style>, <meta> ni <title>')
    if PIE in cuerpo:
        errores.append('no incluyas el pie "Todas las ediciones": lo agrega la plantilla')
    if len(re.findall(r'<h1[\s>]', cuerpo)) != 1:
        errores.append('tiene que haber exactamente un <h1>')
    for patron, nombre in VACIOS:
        for m in re.finditer(patron, cuerpo):
            linea = cuerpo.count('\n', 0, m.start()) + 1
            errores.append(f'{nombre} en la línea {linea}: {cuerpo[max(0, m.start() - 40):m.end() + 40]!r}')
    for e in ETIQUETAS:
        abre, cierra = len(re.findall(rf'<{e}[\s>]', cuerpo)), len(re.findall(rf'</{e}>', cuerpo))
        if abre != cierra:
            errores.append(f'<{e}> abiertas {abre} y cerradas {cierra}')
    t = texto(cuerpo)
    for m in TIEMPO_RELATIVO.finditer(t):
        avisos.append(f'tiempo relativo "{m.group(0)}": …{t[max(0, m.start() - 50):m.end() + 30]}…')
    # palabras por sección (<h2>)
    partes = re.split(r'(<h2[^>]*>.*?</h2>)', cuerpo, flags=re.S)
    secciones = [('(antes del primer h2)', partes[0])]
    for i in range(1, len(partes), 2):
        secciones.append((texto(partes[i]), partes[i] + (partes[i + 1] if i + 1 < len(partes) else '')))
    conteo = [(n, len(texto(s).split())) for n, s in secciones]
    total = sum(n for _, n in conteo)
    if total < MIN_PALABRAS:
        avisos.append(f'edición anormalmente corta: {total} palabras (menos de {MIN_PALABRAS}); revisá si faltan secciones o noticias')
    return errores, avisos, conteo


def publicar():
    hoy = dt.datetime.now(ART).date()
    borradas = []
    for iso in ediciones():
        if (hoy - dt.date.fromisoformat(iso)).days > DIAS:
            os.remove(ruta('contenido', iso + '.html'))
            borradas.append(iso)
    fechas = ediciones()
    # ediciones/: una página por contenido; se borran las que no tienen contenido
    os.makedirs(ruta('ediciones'), exist_ok=True)
    for p in glob.glob(ruta('ediciones', '*.html')):
        if os.path.basename(p)[:-5] not in fechas:
            os.remove(p)
    cuerpos = {iso: leer('contenido', iso + '.html') for iso in fechas}
    for iso in fechas:
        escribir(f'ediciones/{iso}.html', pagina(f'Noticias — {ddmmaaaa(iso)}', cuerpos[iso], '../', PIE))
    # index.html
    lista = '\n'.join(f'<li><a href="ediciones/{iso}.html">Noticias — {ddmmaaaa(iso)}</a></li>' for iso in fechas)
    cuerpo_indice = f'<h1>Noticias diarias</h1>\n<p><a href="feed.xml">Feed RSS</a></p>\n<ul>\n{lista}\n</ul>'
    escribir('index.html', pagina('Noticias diarias', cuerpo_indice, '', ''))
    # feed.xml (RSS 2.0)
    items = []
    for iso in fechas[:EN_FEED]:
        d = dt.date.fromisoformat(iso)
        url = f'{BASE}ediciones/{iso}.html'
        fecha_pub = format_datetime(dt.datetime(d.year, d.month, d.day, 7, 0, tzinfo=ART))
        items.append(f'<item><title>Noticias — {ddmmaaaa(iso)}</title><link>{url}</link><guid>{url}</guid>'
                     f'<pubDate>{fecha_pub}</pubDate><description>{html.escape(cuerpos[iso].strip(), quote=False)}</description></item>')
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Noticias diarias</title>'
            f'<link>{BASE}</link><description>Resumen diario de noticias del mundo, Argentina y Mar del Plata</description>'
            '<language>es-AR</language>\n' + '\n'.join(items) + '\n</channel></rss>\n')
    escribir('feed.xml', feed)
    ET.parse(ruta('feed.xml'))  # falla si el feed no es XML válido
    return fechas, borradas


def main():
    iso = sys.argv[1] if len(sys.argv) > 1 else None
    if iso:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', iso):
            sys.exit(f'Fecha inválida: {iso} (formato AAAA-MM-DD)')
        if not os.path.exists(ruta('contenido', iso + '.html')):
            sys.exit(f'No existe contenido/{iso}.html')
        errores, avisos, conteo = revisar(leer('contenido', iso + '.html'))
        total = sum(n for _, n in conteo) or 1
        print(f'== Revisión de contenido/{iso}.html')
        print(f'Palabras: {total}')
        for nombre, n in conteo:
            print(f'  {nombre}: {n} ({n * 100 / total:.0f}%)')
        print('Avisos:' if avisos else 'Avisos: ninguno')
        for a in avisos:
            print('  - ' + a)
        if errores:
            print('ERRORES (corregilos y volvé a ejecutar; no se publicó nada):')
            for e in errores:
                print('  - ' + e)
            sys.exit(1)
        print('Errores: ninguno')
    fechas, borradas = publicar()
    print(f'== Publicado: {len(fechas)} ediciones; feed con {min(len(fechas), EN_FEED)}; la más reciente {fechas[0] if fechas else "-"}')
    if borradas:
        print('Borradas por antigüedad: ' + ', '.join(borradas))
    if iso and (not fechas or fechas[0] != iso):
        print(f'Aviso: la edición más reciente no es {iso}')


if __name__ == '__main__':
    main()
