#!/usr/bin/env python3
"""Collects public RSS headlines into data/articles.json.
Only uses feed-provided titles, descriptions, links and media thumbnails.
Review source terms and image permissions before enabling feeds in production.
"""
import json, re, hashlib, html, os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"data","articles.json")
FEEDS=[
    ("https://www.vogue.com/feed/rss","Fashion"),
    ("https://www.businessoffashion.com/feed/","Fashion"),
    ("https://www.dezeen.com/feed/","Design"),
    ("https://www.designboom.com/design/feed/","Design"),
    ("https://www.itsnicethat.com/rss","Art & Culture"),
    ("https://techcrunch.com/category/design/feed/","Technology"),
]
MAX_PER_FEED=12
def clean(s):
    s=html.unescape(re.sub(r"<[^>]+>"," ",s or ""))
    return re.sub(r"\s+"," ",s).strip()
def text(node, names):
    for name in names:
        found=node.find(name)
        if found is not None and found.text: return clean(found.text)
    return ""
def date_of(node):
    raw=text(node,["pubDate","{http://purl.org/dc/elements/1.1/}date"])
    try: return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except Exception: return datetime.now(timezone.utc).isoformat()
def get_image(node):
    for el in node.iter():
        tag=el.tag.lower()
        if tag.endswith("thumbnail") or tag.endswith("content"):
            url=el.attrib.get("url","")
            if url.startswith("https://") or url.startswith("http://"): return url
    desc=text(node,["description","{http://www.w3.org/2005/Atom}summary"])
    match=re.search(r"<img[^>]+src=[\"']([^\"']+)",desc,re.I)
    return match.group(1) if match else ""
def fetch(url):
    req=Request(url,headers={"User-Agent":"ATELIER-Magazine-RSS/1.0 (editorial feed reader)"})
    with urlopen(req,timeout=18) as response: return response.read()
def parse_feed(url,category):
    try:
        root=ET.fromstring(fetch(url))
        nodes=root.findall(".//item")
        if not nodes: nodes=root.findall("{http://www.w3.org/2005/Atom}entry")
        result=[]
        for n in nodes[:MAX_PER_FEED]:
            title=text(n,["title","{http://www.w3.org/2005/Atom}title"])
            link=text(n,["link"])
            if not link:
                el=n.find("{http://www.w3.org/2005/Atom}link")
                if el is not None: link=el.attrib.get("href","")
            excerpt=text(n,["description","{http://www.w3.org/2005/Atom}summary","{http://www.w3.org/2005/Atom}content"])
            if not title or not link.startswith("http"): continue
            result.append({"title":title,"excerpt":excerpt[:360],"category":category,"source":url.split("/")[2],"date":date_of(n),"url":link,"image":get_image(n)})
        return result
    except Exception as exc:
        print(f"Feed non disponibile {url}: {exc}")
        return []
def main():
    old={}
    if os.path.exists(OUT):
        try:
            with open(OUT,encoding="utf-8") as f:
                old={a.get("url"):a for a in json.load(f).get("articles",[]) if a.get("url")}
        except Exception: pass
    fresh=[]
    for url,cat in FEEDS: fresh.extend(parse_feed(url,cat))
    merged={a["url"]:a for a in fresh}
    for url,a in old.items(): merged.setdefault(url,a)
    articles=list(merged.values())
    articles.sort(key=lambda a:a.get("date",""),reverse=True)
    articles=articles[:100]
    # Stable duplicate protection by canonical URL; no machine translation is applied.
    payload={"updated_at":datetime.now(timezone.utc).isoformat(),"articles":articles}
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(f"Salvati {len(articles)} articoli.")
if __name__=="__main__": main()
