import hashlib, json, difflib, datetime, pathlib, requests
from bs4 import BeautifulSoup

SOURCES = [l.strip() for l in open("sources.txt") if l.strip() and not l.startswith("#")]
STATE = pathlib.Path("state"); STATE.mkdir(exist_ok=True)
changes, status = [], []

for url in SOURCES:
    f = STATE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        if url.lower().endswith(".pdf"):
            text = hashlib.sha1(r.content).hexdigest()
        else:
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script", "style", "nav", "header", "footer", "noscript"]):
                t.decompose()
            main = soup.find("main") or soup
            text = "\n".join(l.strip() for l in main.get_text("\n").splitlines() if l.strip())
    except Exception as e:
        status.append(f"OTILLGÄNGLIG | {url} | {e}")
        continue
    old = f.read_text() if f.exists() else None
    if old is None:
        status.append(f"BASLINJE | {url}")
    elif old != text:
        added = [l[2:] for l in difflib.ndiff(old.splitlines(), text.splitlines()) if l.startswith("+ ")]
        changes.append({"url": url, "tillagt": added[:40]})
        status.append(f"ÄNDRAD | {url}")
    else:
        status.append(f"OFÖRÄNDRAD | {url}")
    f.write_text(text)

json.dump({"datum": str(datetime.date.today()), "ändringar": changes, "status": status},
          open("changes.json", "w"), ensure_ascii=False, indent=1)