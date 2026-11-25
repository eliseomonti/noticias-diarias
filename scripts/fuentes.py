#!/usr/bin/env python3
# Lee fuentes.txt, descarga feeds RSS/Atom y APIs JSON, y genera un digest de las ultimas horas.
# Uso: python3 scripts/fuentes.py fuentes.txt [horas] [archivo_links] > /tmp/digest.txt
# Los links van aparte (por defecto /tmp/links.txt) para que el digest sea liviano:
# cada noticia termina en #N y su URL se obtiene con: grep '^N ' /tmp/links.txt
import codecs, json, re, sys, html, time, urllib.request, xml.etree.ElementTree as ET
import concurrent.futures as cf
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

HORAS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
LINKS = sys.argv[3] if len(sys.argv) > 3 else '/tmp/links.txt'
CAP = 20          # maximo de notas por feed ordenado por fecha
RECIENTES = 8     # de esas, cuantas son las mas nuevas; el resto se reparte en toda la ventana
CAP_RANKING = 25  # maximo en feeds ordenados por importancia (portadas de Google News)
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36',
      'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8'}
ART = timezone(timedelta(hours=-3))
AHORA = datetime.now(timezone.utc)
LIMITE = AHORA - timedelta(hours=HORAS)
FUTURO = AHORA + timedelta(hours=2)
ORDEN = ['DATOS', 'AR', 'MDP', 'MUNDO', 'TECH', 'DEP', 'VOCES']
WTTR = 'https://wttr.in/Mar+del+Plata?format=j1&lang=es'


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
    return d if d.tzinfo else d.replace(tzinfo=ART)  # sin zona horaria: se asume hora argentina


def limpio(s, n=200):
    s = html.unescape(s or '')
    s = html.unescape(re.sub('<[^>]+>', ' ', s))
    s = ' '.join(s.split())
    return s[:n] + ('…' if len(s) > n else '')


def bajar(url, intentos=2):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read()
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(3)


# ---------- DATOS: resumen compacto de cada API ----------

def dato_dolar(j):
    out = []
    for d in j:
        nom, com, ven = d.get('nombre'), d.get('compra'), d.get('venta')
        f = fecha(d.get('fechaActualizacion'))
        cuando = f' ({f.astimezone(ART):%d/%m %H:%M} ART)' if f else ''
        out.append(f'{nom}: compra {com} / venta {ven}{cuando}')
    return out


def dato_open_meteo(j):
    d = j['daily']
    v = [d[k][0] for k in ('time', 'temperature_2m_max', 'temperature_2m_min', 'precipitation_probability_max',
                           'wind_speed_10m_max', 'wind_gusts_10m_max')]
    return ['pronostico %s: max %s C, min %s C, prob. lluvia max %s%%, viento max %s km/h, rafagas max %s km/h (open-meteo)' % tuple(v)]


def dato_wttr():
    w = json.loads(bajar(WTTR))['weather'][0]
    hs = w.get('hourly', [])
    mx = lambda k: max((int(h[k]) for h in hs), default='sin dato')
    v = (w['date'], w['maxtempC'], w['mintempC'], mx('chanceofrain'), mx('windspeedKmph'), mx('WindGustKmph'))
    return ['pronostico %s: max %s C, min %s C, prob. lluvia max %s%%, viento max %s km/h, rafagas max %s km/h (wttr.in, respaldo)' % v]


def dato_yahoo(j):
    r = j['chart']['result'][0]
    pares = [(t, c) for t, c in zip(r.get('timestamp') or [], r['indicators']['quote'][0].get('close') or []) if c is not None]
    if not pares:
        raise ValueError('sin cierres')
    t, c = pares[-1]
    linea = f'ultimo cierre {datetime.fromtimestamp(t, ART):%d/%m}: {c:,.0f} puntos'
    if len(pares) > 1:
        t0, c0 = pares[-2]
        linea += f' ({(c / c0 - 1) * 100:+.2f}% vs cierre del {datetime.fromtimestamp(t0, ART):%d/%m})'
    return [linea + ' (Yahoo Finance)']


def procesar_dato(url, data):
    j = json.loads(data)
    if 'dolarapi' in url:
        return dato_dolar(j)
    if 'open-meteo' in url:
        return dato_open_meteo(j)
    if 'finance/chart' in url:
        return dato_yahoo(j)
    return [json.dumps(j, ensure_ascii=False)[:3000]]


# ---------- FEEDS ----------

def es_ranking(url):
    # portadas y secciones de Google News: vienen ordenadas por importancia, no por fecha
    return 'news.google.com/rss?' in url or '/headlines/' in url


def medios_cluster(desc_html):
    # en Google News la descripcion lista los medios que cubren la misma noticia
    return [html.unescape(m).strip() for m in re.findall('<font[^>]*>(.*?)</font>', html.unescape(desc_html or ''))]


def elegir(items, url):
    if es_ranking(url):
        return items[:CAP_RANKING]
    con = sorted([i for i in items if i['d']], key=lambda i: i['d'], reverse=True)
    sin = [i for i in items if not i['d']]
    if len(con) > CAP:
        resto = con[RECIENTES:]
        k = CAP - RECIENTES
        paso = (len(resto) - 1) / (k - 1)
        con = con[:RECIENTES] + [resto[round(x * paso)] for x in range(k)]
    return con + sin[:3]  # las notas sin fecha van al final


def procesar(sec, nombre, url):
    try:
        if sec == 'DATOS':
            try:
                return sec, nombre, url, 'OK', procesar_dato(url, bajar(url))
            except Exception:
                if 'open-meteo' in url:
                    return sec, nombre, url, 'RESPALDO', dato_wttr()
                if 'query1.finance.yahoo' in url:
                    return sec, nombre, url, 'RESPALDO', procesar_dato(url, bajar(url.replace('query1', 'query2')))
                raise
        root = ET.fromstring(bajar(url).lstrip().removeprefix(codecs.BOM_UTF8).lstrip())
        items = []
        for it in root.iter():
            if it.tag.split('}')[-1] not in ('item', 'entry'):
                continue
            c, alt = {}, None
            for ch in it:
                t = ch.tag.split('}')[-1]
                if t == 'link' and ch.get('href'):
                    if ch.get('rel') in (None, 'alternate'):
                        alt = alt or ch.get('href')
                    c.setdefault('link', ch.get('href'))
                elif t in ('title', 'link', 'description', 'summary', 'pubDate', 'published', 'updated', 'date'):
                    c.setdefault(t, ch.text or '')
                elif t == 'group':  # YouTube: media:group/media:description
                    for g in ch:
                        if g.tag.split('}')[-1] == 'description':
                            c.setdefault('description', g.text or '')
            d = fecha(c.get('pubDate') or c.get('published') or c.get('date') or c.get('updated'))
            if d and (d < LIMITE or d > FUTURO):
                continue
            raw = c.get('description') or c.get('summary') or ''
            medios = medios_cluster(raw) if 'news.google.com' in url else []
            items.append({'d': d, 't': limpio(c.get('title'), 220), 'l': (alt or c.get('link') or '').strip(),
                          'desc': '' if medios else limpio(raw), 'medios': medios})
        if not items:
            return sec, nombre, url, 'VACIA', []
        return sec, nombre, url, 'OK', elegir(items, url)
    except Exception as e:
        return sec, nombre, url, 'ERROR', 'ERROR: ' + str(e)[:120]


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
    n = 0
    links, fallas, vacias, respaldos = [], [], [], []
    q = chr(39)
    print(f'# Digest generado {AHORA.astimezone(ART):%Y-%m-%d %H:%M} (ART), ultimas {HORAS} h')
    print('# Cada noticia: [fecha hora ART] titulo #N. La URL de la noticia #N se obtiene con: grep ' + q + '^N ' + q + ' ' + LINKS)
    print('# En los feeds de Google News, cubren(N) lista los medios distintos que publicaron esa misma noticia.')
    for sec in ORDEN + sorted({r[0] for r in res} - set(ORDEN)):
        bloque = [r for r in res if r[0] == sec]
        if not bloque:
            continue
        print()
        print(f'======== {sec} ========')
        for _, nombre, url, estado, contenido in bloque:
            if estado == 'ERROR':
                fallas.append(f'{nombre}: {contenido}')
                continue
            if estado == 'VACIA':
                vacias.append(nombre)
                continue
            if estado == 'RESPALDO':
                respaldos.append(nombre)
            print()
            if sec == 'DATOS':
                print(f'## {nombre}')
                for l in contenido:
                    print('- ' + l)
                continue
            orden = 'por importancia' if es_ranking(url) else 'por fecha'
            print(f'## {nombre} ({len(contenido)} items, {orden})')
            for i in contenido:
                n += 1
                links.append(str(n) + ' ' + i['l'])
                h = i['d'].astimezone(ART).strftime('%d/%m %H:%M') if i['d'] else 's/f'
                extra = ''
                if i['medios']:
                    m = list(dict.fromkeys(i['medios']))
                    extra = ' | cubren(' + str(len(m)) + '): ' + ', '.join(m[:6]) + (' …' if len(m) > 6 else '')
                print('- [' + h + '] ' + i['t'] + extra + ' #' + str(n))
                desc, t = i['desc'], i['t']
                if desc and not (len(desc) <= len(t) + 30 and (desc[:40].lower() in t.lower() or t[:40].lower() in desc.lower())):
                    print('    ' + desc)
    with open(LINKS, 'w', encoding='utf-8') as fh:
        fh.write(chr(10).join(links) + chr(10))
    print()
    print('======== ESTADO DE FUENTES ========')
    print('Con error: ' + ('; '.join(fallas) if fallas else 'ninguna'))
    print('Sin notas en la ventana (posible feed muerto): ' + (', '.join(vacias) if vacias else 'ninguna'))
    print('Con respaldo: ' + (', '.join(respaldos) if respaldos else 'ninguna'))


if __name__ == '__main__':
    main()
