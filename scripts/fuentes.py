#!/usr/bin/env python3
# Lee fuentes.txt, descarga feeds RSS/Atom y APIs JSON, y genera un digest de las ultimas horas.
# Uso: python3 scripts/fuentes.py fuentes.txt [horas] > /tmp/digest.txt
import json, re, sys, html, urllib.request, xml.etree.ElementTree as ET
import concurrent.futures as cf
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

HORAS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
MAX_ITEMS = 10
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36',
      'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8'}
ART = timezone(timedelta(hours=-3))
AHORA = datetime.now(timezone.utc)
LIMITE = AHORA - timedelta(hours=HORAS)
ORDEN = ['DATOS', 'AR', 'MDP', 'MUNDO', 'TECH', 'DEP', 'VOCES']


def fecha(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def limpio(s, n=160):
    s = html.unescape(re.sub('<[^>]+>', ' ', s or ''))
    s = ' '.join(s.split())
    return s[:n] + ('…' if len(s) > n else '')


def procesar(sec, nombre, url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read()
        if sec == 'DATOS':
            return sec, nombre, None, json.dumps(json.loads(data), ensure_ascii=False)[:1500]
        root = ET.fromstring(data)
        items = []
        for it in root.iter():
            if it.tag.split('}')[-1] not in ('item', 'entry'):
                continue
            c = {}
            for ch in it:
                t = ch.tag.split('}')[-1]
                if t == 'link' and ch.get('href'):
                    c.setdefault('link', ch.get('href'))
                elif t in ('title', 'link', 'description', 'summary', 'pubDate', 'published', 'updated', 'date'):
                    c.setdefault(t, ch.text or '')
                elif t == 'group':  # YouTube: media:group/media:description
                    for g in ch:
                        if g.tag.split('}')[-1] == 'description':
                            c.setdefault('description', g.text or '')
            d = fecha(c.get('pubDate') or c.get('published') or c.get('date') or c.get('updated'))
            if d and d < LIMITE:
                continue
            items.append((d, limpio(c.get('title'), 200), (c.get('link') or '').strip(),
                          limpio(c.get('description') or c.get('summary'))))
        items.sort(key=lambda x: x[0] or AHORA, reverse=True)
        return sec, nombre, items[:MAX_ITEMS], None
    except Exception as e:
        return sec, nombre, None, 'ERROR: ' + str(e)[:120]


def main():
    archivo = sys.argv[1] if len(sys.argv) > 1 else 'fuentes.txt'
    fuentes = []
    for linea in open(archivo, encoding='utf-8'):
        linea = linea.strip()
        if not linea or linea.startswith('#') or linea.count('|') < 2:
            continue
        sec, nombre, url = (p.strip() for p in linea.split('|', 2))
        fuentes.append((sec.upper(), nombre, url))
    with cf.ThreadPoolExecutor(16) as ex:
        res = list(ex.map(lambda f: procesar(*f), fuentes))
    fallas = []
    print(f'# Digest generado {AHORA.astimezone(ART):%Y-%m-%d %H:%M} (ART), ultimas {HORAS} h')
    for sec in ORDEN + sorted({r[0] for r in res} - set(ORDEN)):
        bloque = [r for r in res if r[0] == sec]
        if not bloque:
            continue
        print()
        print(f'======== {sec} ========')
        for _, nombre, items, extra in bloque:
            if extra and extra.startswith('ERROR'):
                fallas.append(f'{nombre}: {extra}')
                continue
            print()
            if extra:
                print(f'## {nombre}')
                print(extra)
                continue
            print(f'## {nombre} ({len(items)} items)')
            for d, t, l, desc in items:
                hora = d.astimezone(ART).strftime('%d/%m %H:%M') if d else 's/f'
                if desc and (desc[:40].lower() in t.lower() or t[:40].lower() in desc.lower()):
                    desc = ''  # Google News repite el titulo en la descripcion
                print(f'- [{hora}] {t} | {l}')
                if desc:
                    print(f'    {desc}')
    print()
    print('======== FUENTES CON ERROR ========')
    for f in fallas or ['ninguna']:
        print(f)


if __name__ == '__main__':
    main()
