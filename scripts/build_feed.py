#!/usr/bin/env python3
import glob, os, re, datetime, html
from email.utils import format_datetime
BASE = "https://eliseomonti.github.io/noticias-diarias/"
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
files = sorted(glob.glob("ediciones/*.html"), reverse=True)
# delete >60 days
today = datetime.date.today()
for f in list(files):
    d = datetime.date.fromisoformat(os.path.basename(f)[:-5])
    if (today - d).days > 60:
        os.remove(f); files.remove(f)
tz = datetime.timezone(datetime.timedelta(hours=-3))
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
items = []
for f in files[:14]:
    iso = os.path.basename(f)[:-5]
    d = datetime.date.fromisoformat(iso)
    src = open(f, encoding="utf-8").read()
    m = re.search(r"<body>(.*)</body>", src, re.S)
    body = m.group(1).strip()
    pub = format_datetime(datetime.datetime(d.year, d.month, d.day, 7, 0, tzinfo=tz))
    url = f"{BASE}ediciones/{iso}.html"
    items.append(f"<item><title>Noticias — {d.strftime('%d/%m/%Y')}</title><link>{url}</link><guid>{url}</guid><pubDate>{pub}</pubDate><description>{esc(body)}</description></item>")
feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Noticias diarias</title>'
        f'<link>{BASE}</link><description>Resumen diario de noticias de Argentina, Mar del Plata y el mundo</description>'
        '<language>es-AR</language>\n' + "\n".join(items) + '\n</channel></rss>\n')
open("feed.xml","w",encoding="utf-8").write(feed)
lis = "\n".join(f'<li><a href="ediciones/{os.path.basename(f)}">Noticias — {datetime.date.fromisoformat(os.path.basename(f)[:-5]).strftime("%d/%m/%Y")}</a></li>' for f in files)
open("index.html","w",encoding="utf-8").write(f'<!DOCTYPE html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark"><style>:root{{color-scheme:dark}}html{{background:#17191c}}body{{font-family:Georgia,serif;font-size:1.05em;line-height:1.65;max-width:42em;margin:0 auto;padding:1em 1.1em;background:#17191c;color:#d6d6d3}}h1,h2,strong{{color:#ededea}}h1,h2{{line-height:1.25}}h2{{margin-top:1.8em;padding-bottom:.25em;border-bottom:1px solid #ffffff1f}}a{{color:#8fb8f0}}a:visited{{color:#b7a3dc}}</style><title>Noticias diarias</title><link rel="alternate" type="application/rss+xml" href="feed.xml"></head><body><h1>Noticias diarias</h1><p><a href="feed.xml">Feed RSS</a></p><ul>\n{lis}\n</ul></body></html>\n')
