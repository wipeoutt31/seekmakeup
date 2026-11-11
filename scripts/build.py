#!/usr/bin/env python3
"""Build SeekMakeup's directory pages from data/sheet.json (an export of the
"SeekMakeup – Data" Google Sheet) into public/.

Run:  python3 scripts/build.py
"""
import html, json, os, re, shutil, unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
DATA = json.load(open(os.path.join(ROOT, "data", "sheet.json"), encoding="utf-8"))
SITE = "https://seekmakeup.com"
BOROUGHS = ["Manhattan", "Brooklyn", "Queens"]
AREA = ", ".join(BOROUGHS[:-1]) + " and " + BOROUGHS[-1]
CITY = "New York City"
TODAY = "2026-11-10"

# Store chains whose shelves differ a lot from store to store.
VARIES_CHAINS = {"CVS", "Walgreens/Duane Reade", "Target", "Ulta"}
CAT_GROUPS = [
    ("Complexion", ["Primer", "Foundation", "Concealer", "Setting powder or spray"]),
    ("Cheeks", ["Contour or bronzer", "Blush", "Highlighter"]),
    ("Eyes & brows", ["Brows", "Eyeshadow", "Eyeliner", "Mascara"]),
    ("Lips", ["Lip liner", "Lipstick or liquid lip", "Lip gloss"]),
]
CAT_LABEL = {"Setting powder or spray": "Setting powder & spray", "Contour or bronzer": "Contour & bronzer",
             "Lipstick or liquid lip": "Lipstick & liquid lip"}
TIER_ORDER = ["Luxury", "Prestige", "Mid-range", "Drugstore"]
TYPE_FILTER = {"Beauty chain": "beauty", "Brand store": "beauty", "Department store": "dept",
               "Drugstore": "drug", "Big-box store": "drug"}
TYPE_LABEL = {"Beauty chain": "Beauty store", "Brand store": "Brand store", "Department store": "Department store",
              "Drugstore": "Drugstore", "Big-box store": "Big-box store"}

def esc(s): return html.escape(str(s or ""), quote=True)

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def rows(name):
    data = DATA[name]
    head = data[0]
    out = []
    for r in data[1:]:
        r = list(r) + [""] * (len(head) - len(r))
        if r[0].strip():
            out.append(dict(zip(head, r)))
    return out

# ---------- load ----------
brands = rows("Brands")
CATS = [c for _, cs in CAT_GROUPS for c in cs]
for b in brands:
    b["slug"] = slugify(b["Brand"])
    b["cats"] = [c for c in CATS if str(b.get(c, "")).upper() == "TRUE"]
brand_by_name = {b["Brand"]: b for b in brands}

stores = [s for s in rows("Stores") if s.get("Borough") in BOROUGHS]
seen = set()
for s in stores:
    sl = slugify(s["Store"])
    while sl in seen: sl += "-2"
    seen.add(sl); s["slug"] = sl
    note = s.get("Notes", "")
    s["public_note"] = note.split("Show on site:", 1)[1].strip() if "Show on site:" in note else ""
store_by_name = {s["Store"]: s for s in stores}

chain = rows("Chain carries")
chain_cols = [c for c in DATA["Chain carries"][0][1:] if c]
chain_yes = defaultdict(set)      # chain -> brand names
chain_checked = set()
for r in chain:
    for c in chain_cols:
        v = r.get(c, "")
        if v in ("Yes", "No"): chain_checked.add(c)
        if v == "Yes": chain_yes[c].add(r["Brand"])

# carries[(store, brand)] = selection text
carries = {}
for s in stores:
    ch = s.get("Chain", "")
    if ch and ch in chain_checked and "Kohl's" not in s["Store"]:  # Sephora at Kohl's carries a much smaller list
        for bn in chain_yes[ch]:
            carries[(s["Store"], bn)] = "Selection varies" if ch in VARIES_CHAINS else "Carries"
for r in rows("Carries"):
    if r["Store"] in store_by_name and r["Brand"] in brand_by_name:
        carries[(r["Store"], r["Brand"])] = "Selection varies" if r.get("Selection") == "Selection varies" else "Carries"

by_brand = defaultdict(list)
by_store = defaultdict(list)
for (sn, bn), sel in carries.items():
    by_brand[bn].append((store_by_name[sn], sel))
    by_store[sn].append((brand_by_name[bn], sel))

# ---------- page shell ----------
ICON_INFO = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v5M12 8h.01"></path></svg>'
CHEV = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6A6670" stroke-width="2" stroke-linecap="round"><path d="M9 6l6 6-6 6"></path></svg>'

def page(path, title, desc, body, crumbs=None, jsonld=None, scripts=""):
    canon = SITE + path
    cr = ""
    if crumbs:
        parts = []
        for label, href in crumbs:
            parts.append(f'<a href="{href}">{esc(label)}</a>' if href else f'<span aria-current="page">{esc(label)}</span>')
        cr = '<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap">' + ' <span aria-hidden="true">›</span> '.join(parts) + '</div></nav>'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#A3214F">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SeekMakeup">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{ld}
</head>
<body>
<header class="top"><div class="wrap"><a class="logo" href="/">Seek<span>Makeup</span></a>
<nav class="mainnav" aria-label="Main"><a href="/brands/">Brands</a><a href="/stores/">Stores</a><a href="/makeup/">Makeup</a></nav></div></header>
{cr}
<main>
{body}
</main>
<footer class="foot"><div class="wrap">
<p><strong>No real-time inventory.</strong> SeekMakeup lists which stores carry a brand, not what's on the shelf today. Call the store before you go.</p>
<p>© 2026 SeekMakeup · <a href="/brands/">Brands</a> · <a href="/stores/">Stores</a> · <a href="/contact.html">Contact</a> · <a href="/privacy.html">Privacy</a></p>
</div></footer>
{scripts}
</body>
</html>
'''
    out = os.path.join(PUB, path.lstrip("/"))
    if out.endswith("/"): out = os.path.join(out, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)
    if path != "/": SITEMAP.append(path)

SITEMAP = []

NOTICE = f'<div class="notice" role="note">{ICON_INFO}<p><strong>No real-time inventory.</strong> We list stores that carry a brand, not live stock. Selection varies by store, so call ahead for a specific product or shade.</p></div>'

def street(s): return re.sub(r", [A-Za-z .']+, NY \d{5}$", "", s["Address"])
def city(s):  # Queens addresses use their own postal town (Astoria, Flushing...)
    m = re.search(r", ([A-Za-z .']+), NY \d{5}$", s["Address"])
    return m.group(1) if m else ("Brooklyn" if s.get("Borough") == "Brooklyn" else "New York")
def where(s): return f'{s["Neighborhood"]}, {s["Borough"]}'

def maps_url(s): return "https://www.google.com/maps/search/?api=1&query=" + re.sub(r"\s+", "+", (s["Store"] + ", " + s["Address"])).replace("&", "%26").replace("#", "%23")
def tel(p): return "tel:+1" + re.sub(r"\D", "", p)[-10:] if p else ""
def makes(b, n=6):
    labels = [CAT_LABEL.get(c, c) for c in b["cats"]]
    if len(labels) == len(CATS): return "Complexion, cheeks, eyes and lips"
    return " · ".join(labels[:n]) + (" · more" if len(labels) > n else "")
def contact(reason, about): return "/contact.html?reason=" + re.sub(" ", "+", reason) + "&about=" + re.sub(r"\s+", "+", about).replace("&", "%26")

def store_card(s, badges, brand_names=None):
    ph = s.get("Phone", "")
    btns = f'<a class="btn primary" href="{esc(maps_url(s))}" rel="noopener" target="_blank">Directions</a>'
    if ph: btns += f'<a class="btn" href="{tel(ph)}">Call</a>'
    bd = "".join(f'<span class="badge {c}">{esc(t)}</span>' for t, c in badges)
    return f'''<article class="card store" data-type="{TYPE_FILTER.get(s["Store type"], "other")}" data-boro="{esc(s["Borough"])}" data-hood="{esc(s["Neighborhood"])}">
<div class="cardhead"><a class="cardtitle" href="/stores/{s["slug"]}/">{esc(s["Store"])}</a></div>
<p class="meta">{esc(TYPE_LABEL.get(s["Store type"], s["Store type"]))} · {esc(where(s))}<br>{esc(s["Address"])}</p>
<div class="badges">{bd}</div>
<p class="checked">Last checked {esc(s.get("Last checked", ""))}</p>
<div class="btns">{btns}</div>
</article>'''

# ---------- brand pages ----------
def brand_page(b):
    lst = sorted(by_brand.get(b["Brand"], []), key=lambda x: (BOROUGHS.index(x[0]["Borough"]), x[0]["Store type"] != "Brand store", x[0]["Neighborhood"], x[0]["Store"]))
    n = len(lst)
    tags = "".join(f'<a class="tag" href="/makeup/{slugify(c)}/">{esc(CAT_LABEL.get(c, c))}</a>' for c in b["cats"])
    if n:
        types = {TYPE_FILTER.get(s["Store type"]) for s, _ in lst}
        chips = [("all", "All stores")] + [(k, l) for k, l in (("beauty", "Beauty stores"), ("dept", "Department stores"), ("drug", "Drugstores & Target")) if k in types]
        chiphtml = '<div class="chips" role="group" aria-label="Filter stores">' + "".join(
            f'<button type="button" class="chip{" on" if k == "all" else ""}" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{esc(l)}</button>' for k, l in chips) + '</div>' if len(chips) > 2 else ""
        boros = [bo for bo in BOROUGHS if any(s["Borough"] == bo for s, _ in lst)]
        if len(boros) > 1:
            chiphtml = '<div class="chips boro" role="group" aria-label="Filter by borough">' + "".join(
                f'<button type="button" class="chip{" on" if k == "all" else ""}" data-b="{k}" aria-pressed="{"true" if k == "all" else "false"}">{esc(l)}</button>'
                for k, l in [("all", "All of " + AREA)] + [(bo, bo + f" ({sum(1 for s, _ in lst if s['Borough'] == bo)})") for bo in boros]) + '</div>' + chiphtml
        cards = "\n".join(store_card(s, [(f'Carries {b["Brand"]}', "ok")] + ([("Selection varies", "warn")] if sel == "Selection varies" else [])) for s, sel in lst)
        count = f'{n} store{"s" if n != 1 else ""} in {AREA} carry this brand'
        listing = f'{chiphtml}<div class="cards" id="list">{cards}</div>'
    else:
        count = f"We haven't found a {AREA} store that carries {b['Brand']} yet"
        online = ""
        if b.get("Website"):
            dom = re.sub(r"^https?://(www\.)?", "", b["Website"])
            online = f' You can buy it online at <a href="{esc(b["Website"])}" rel="noopener">{esc(dom)}</a>.'
        listing = f'<div class="empty"><p>None of the stores we\'ve checked in {AREA} list {esc(b["Brand"])}.{online}</p></div>'
    note = f'<p class="brandnote">{esc(b["Notes"])}</p>' if b.get("Notes") and "checked" not in b.get("Notes", "") else ""
    site = f'<p class="meta">{esc(b["Price tier"])} · <a href="{esc(b["Website"])}" rel="noopener" target="_blank">Brand website</a></p>' if b.get("Website") else f'<p class="meta">{esc(b["Price tier"])}</p>'
    body = f'''<section class="intro"><div class="wrap">
<h1>Where to buy {esc(b["Brand"])} in {AREA}</h1>
<p class="count">{count}</p>
{site}{note}
<div class="makes"><span class="label">This brand makes</span><div class="tags">{tags}</div></div>
{NOTICE}
</div></section>
<section class="wrap listing">{listing}</section>
<section class="wrap"><div class="help"><h2>See something wrong?</h2><p>Tell us if a store no longer carries {esc(b["Brand"])}, or if we're missing one.</p><a href="{esc(contact("Report a change to a listing", b["Brand"] + " (brand page)"))}">Report a change →</a></div></section>'''
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Brands", "item": SITE + "/brands/"},
        {"@type": "ListItem", "position": 2, "name": b["Brand"], "item": f'{SITE}/brands/{b["slug"]}/'}]}
    page(f'/brands/{b["slug"]}/', f'Where to buy {b["Brand"]} in {AREA}, NYC | SeekMakeup',
         f'{count.replace("carry this brand", "carry " + b["Brand"])}: addresses, phone numbers and directions. Store listings only, no live inventory.',
         body, crumbs=[("Brands", "/brands/"), (b["Brand"], None)], jsonld=ld, scripts=FILTER_JS)

FILTER_JS = '''<script>
(function(){var chips=document.querySelectorAll('.chip');if(!chips.length)return;var F={f:'all',b:'all'};
chips.forEach(function(c){c.addEventListener('click',function(){var k=c.dataset.b!==undefined?'b':'f';
c.parentNode.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on');x.setAttribute('aria-pressed','false')});
c.classList.add('on');c.setAttribute('aria-pressed','true');F[k]=c.dataset[k];
document.querySelectorAll('#list .store').forEach(function(s){s.hidden=!((F.f==='all'||s.dataset.type===F.f)&&(F.b==='all'||s.dataset.boro===F.b))})})})})();
</script>'''

# ---------- store pages ----------
def store_page(s):
    lst = by_store.get(s["Store"], [])
    ph, web, hrs = s.get("Phone", ""), s.get("Website", ""), s.get("Hours", "")
    lines = [esc(s["Address"])] + ([esc(ph)] if ph else []) + ([esc(hrs)] if hrs else [])
    btns = f'<a class="btn primary" href="{esc(maps_url(s))}" rel="noopener" target="_blank">Directions</a>'
    if ph: btns += f'<a class="btn" href="{tel(ph)}">Call</a>'
    if web: btns += f'<a class="btn" href="{esc(web)}" rel="noopener" target="_blank">Website</a>'
    pnote = f'<div class="notice warnbox" role="note">{ICON_INFO}<p>{esc(s["public_note"])}</p></div>' if s["public_note"] else ""
    if lst:
        varies = any(sel == "Selection varies" for _, sel in lst)
        groups = defaultdict(list)
        for b, sel in lst: groups[b["Price tier"]].append((b, sel))
        gh = ""
        for t in TIER_ORDER:
            if t not in groups: continue
            items = "".join(f'<a class="row" href="/brands/{b["slug"]}/"><span><span class="rowtitle">{esc(b["Brand"])}</span><span class="rowsub">{esc(makes(b, 5))}</span></span>{CHEV}</a>'
                            for b, sel in sorted(groups[t], key=lambda x: x[0]["Brand"].lower()))
            gh += f'<section class="group"><h3>{esc(t)}</h3><div class="rows">{items}</div></section>'
        vtxt = " Shelves at this kind of store vary, so not every brand or shade may be in stock." if varies else (" Individual stores may not stock every brand on the chain's list." if s.get("Chain") else "")
        brandsec = f'<section class="wrap"><h2>Makeup brands carried here ({len(lst)})</h2><p class="sub">Grouped by price range. From the {"store" if s["Store type"] == "Brand store" else "chain"}\'s own brand list, last checked {esc(s.get("Last checked", ""))}.{vtxt}</p>{gh}</section>'
    elif s["public_note"]:
        brandsec = ""
    else:
        brandsec = f'<section class="wrap"><h2>Makeup brands carried here</h2><div class="empty"><p>We haven\'t checked this store\'s brands yet.</p></div></section>'
    body = f'''<section class="intro storeintro"><div class="wrap">
<span class="typepill">{esc(TYPE_LABEL.get(s["Store type"], s["Store type"]))}</span>
<h1>{esc(s["Store"])}</h1>
<p class="meta">{esc(where(s))}</p>
<p class="details">{"<br>".join(lines)}</p>
<div class="btns">{btns}</div>
{pnote}
</div></section>
{brandsec}
<section class="wrap"><div class="help"><h2>Is this your store?</h2><p>Claim this listing to update your brands and hours.</p><a href="{esc(contact("I own a store", s["Store"]))}">Claim this listing →</a></div>
<p class="small"><a href="{esc(contact("Report a change to a listing", s["Store"]))}">Report a brand that's no longer here</a></p></section>'''
    ld = {"@context": "https://schema.org", "@type": "Store", "name": s["Store"], "url": f'{SITE}/stores/{s["slug"]}/',
          "address": {"@type": "PostalAddress", "streetAddress": street(s), "addressLocality": city(s),
                      "addressRegion": "NY", "postalCode": s["Address"][-5:], "addressCountry": "US"}}
    if ph: ld["telephone"] = "+1" + re.sub(r"\D", "", ph)[-10:]
    desc = (f'Makeup brands sold at {s["Store"]}, {s["Address"]}: {len(lst)} brands. ' if lst else f'{s["Store"]}, {s["Address"]}. ') + "Address, phone and directions. No live inventory."
    page(f'/stores/{s["slug"]}/', f'{s["Store"]}, {s["Neighborhood"]}: makeup brands sold here | SeekMakeup', desc, body,
         crumbs=[("Stores", "/stores/"), (s["Store"], None)], jsonld=ld)

# ---------- category pages ----------
def cat_page(c):
    lst = sorted([b for b in brands if c in b["cats"]], key=lambda b: (-len(by_brand.get(b["Brand"], [])), b["Brand"].lower()))
    items = "".join(f'<a class="row" href="/brands/{b["slug"]}/"><span><span class="rowtitle">{esc(b["Brand"])}</span><span class="rowsub">{esc(b["Price tier"])} · {len(by_brand.get(b["Brand"], []))} {AREA} stores</span></span>{CHEV}</a>' for b in lst)
    label = CAT_LABEL.get(c, c)
    body = f'''<section class="intro"><div class="wrap"><h1>{esc(label)}: brands and where to buy them in {AREA}</h1>
<p class="count">{len(lst)} brands make {esc(label.lower())}. Pick a brand to see the {AREA} stores that carry it.</p>
<p class="sub">Category tags are a guide, so check the brand's site for a specific product.</p>{NOTICE}</div></section>
<section class="wrap"><div class="rows">{items}</div></section>'''
    page(f'/makeup/{slugify(c)}/', f'{label} brands in {AREA}: where to buy | SeekMakeup',
         f'{len(lst)} makeup brands that make {label.lower()}, and the {AREA} stores that carry each one.', body,
         crumbs=[("Makeup", "/makeup/"), (label, None)])

def cat_tags_html():
    out = ""
    for g, cs in CAT_GROUPS:
        out += f'<h3 class="grouphead">{esc(g)}</h3><div class="tags big">' + "".join(f'<a class="tag" href="/makeup/{slugify(c)}/">{esc(CAT_LABEL.get(c, c))}</a>' for c in cs) + '</div>'
    return out

# ---------- build ----------
for d in ("brands", "stores", "makeup", "assets"):
    shutil.rmtree(os.path.join(PUB, d), ignore_errors=True)
os.makedirs(os.path.join(PUB, "assets"))
shutil.copy(os.path.join(ROOT, "scripts", "site.css"), os.path.join(PUB, "assets", "site.css"))

for b in brands: brand_page(b)
for s in stores: store_page(s)
for c in CATS: cat_page(c)

# Brands index
letters = defaultdict(list)
for b in sorted(brands, key=lambda b: b["Brand"].lower()):
    L = unicodedata.normalize("NFKD", b["Brand"])[0].upper()
    letters[L if L.isalpha() else "#"].append(b)
bi = ""
for L in sorted(letters):
    bi += f'<section class="group"><h3>{L}</h3><div class="rows">' + "".join(
        f'<a class="row" href="/brands/{b["slug"]}/"><span><span class="rowtitle">{esc(b["Brand"])}</span><span class="rowsub">{esc(b["Price tier"])} · {len(by_brand.get(b["Brand"], []))} stores</span></span>{CHEV}</a>' for b in letters[L]) + '</div></section>'
page("/brands/", f"Makeup brands and where to buy them in {AREA} | SeekMakeup",
     f"{len(brands)} makeup brands, from drugstore to luxury, and the {AREA} stores that carry each one.",
     f'<section class="intro"><div class="wrap"><h1>Makeup brands</h1><p class="count">{len(brands)} brands. Pick one to see the {AREA} stores that carry it.</p>{NOTICE}</div></section><section class="wrap">{bi}</section>',
     crumbs=[("Brands", None)])

# Stores index, by neighborhood
si = '<p class="small">Jump to: ' + " · ".join(f'<a href="#{slugify(bo)}">{bo}</a>' for bo in BOROUGHS) + '</p>'
for bo in BOROUGHS:
    hoods = defaultdict(list)
    for s in stores:
        if s["Borough"] == bo: hoods[s["Neighborhood"]].append(s)
    si += f'<h2 id="{slugify(bo)}" class="borohead">{bo} <span class="sub">({sum(len(v) for v in hoods.values())} stores)</span></h2>'
    for h in sorted(hoods):
        si += f'<section class="group"><h3>{esc(h)}</h3><div class="rows">' + "".join(
            f'<a class="row" href="/stores/{s["slug"]}/"><span><span class="rowtitle">{esc(s["Store"])}</span><span class="rowsub">{esc(street(s))} · {len(by_store.get(s["Store"], []))} brands</span></span>{CHEV}</a>'
            for s in sorted(hoods[h], key=lambda s: s["Store"])) + '</div></section>'
page("/stores/", f"Makeup stores in {AREA} by neighborhood | SeekMakeup",
     f"{len(stores)} {AREA} stores that sell makeup, from Sephora and Ulta to department stores, drugstores and brand boutiques.",
     f'<section class="intro"><div class="wrap"><h1>Stores in {AREA}</h1><p class="count">{len(stores)} stores, by borough and neighborhood.</p>{NOTICE}</div></section><section class="wrap">{si}</section>',
     crumbs=[("Stores", None)])

# Makeup (categories) index
page("/makeup/", f"Shop makeup by category in {AREA} | SeekMakeup",
     f"Find brands by what you need, from foundation to lip gloss, and the {AREA} stores that carry them.",
     f'<section class="intro"><div class="wrap"><h1>Shop by what you need</h1><p class="count">Pick a category to see the brands that make it.</p></div></section><section class="wrap">{cat_tags_html()}</section>',
     crumbs=[("Makeup", None)])

# Search index for the home page
idx = {"b": [[b["Brand"], b["slug"]] for b in sorted(brands, key=lambda b: b["Brand"].lower())]}
bpos = {name: i for i, (name, _) in enumerate(idx["b"])}
idx["s"] = []
for s in stores:
    lst = by_store.get(s["Store"], [])
    idx["s"].append([s["Store"], s["slug"], TYPE_LABEL.get(s["Store type"], s["Store type"]), where(s), s["Address"],
                     [bpos[b["Brand"]] for b, _ in lst], [bpos[b["Brand"]] for b, sel in lst if sel == "Selection varies"], s["Borough"]])
json.dump(idx, open(os.path.join(PUB, "assets", "search.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# Home page
popular = ["Fenty Beauty", "Rare Beauty", "Charlotte Tilbury", "MAC Cosmetics", "NARS", "Maybelline New York", "e.l.f. Cosmetics", "Dior Beauty"]
pop = "".join(f'<a class="tag" href="/brands/{brand_by_name[p]["slug"]}/">{esc(p)}</a>' for p in popular if p in brand_by_name)
home = f'''<section class="hero"><div class="wrap">
<span class="pill">Now in {AREA} · more of NYC coming</span>
<h1>Find the stores that carry your makeup brands.</h1>
<p class="lede">Search one brand or several to see which {AREA} stores carry them, so you know where to look before you go.</p>
<div class="notice" role="note">{ICON_INFO}<p><strong>No real-time inventory tracking.</strong> SeekMakeup is a directory of makeup brands and the stores that sell them. We can't tell you whether a product or shade is in stock today, so call the store before you go.</p></div>
<form id="finder" class="finder" autocomplete="off" onsubmit="return false">
<label for="q">Brand or brands</label>
<div class="picker"><div id="picked" class="picked"></div><input id="q" type="text" placeholder="Start typing a brand, e.g. Fenty Beauty" aria-describedby="qhint" aria-autocomplete="list" aria-controls="sugg"></div>
<ul id="sugg" class="sugg" role="listbox" hidden></ul>
<p id="qhint" class="hint">Add as many brands as you like.</p>
<label class="check"><input id="all" type="checkbox"> Only show stores that carry all of these brands</label>
<label for="area" class="arealabel">Area</label>
<select id="area" class="area"><option value="">All of {AREA}</option>{"".join(f'<option value="{bo}">{bo}</option>' for bo in BOROUGHS)}</select>
</form>
</div></section>
<section class="wrap" id="results" aria-live="polite"></section>
<section class="wrap"><h2>Popular brands</h2><div class="tags big">{pop}</div><p class="small"><a href="/brands/">See all {len(brands)} brands →</a> · <a href="/stores/">Browse {len(stores)} stores →</a></p></section>
<section class="wrap"><h2>Shop by what you need</h2>{cat_tags_html()}</section>
<section class="wrap"><div class="help"><h2>Own a store?</h2><p>Claim your free listing and tell us which brands you carry.</p><a href="/contact.html?reason=I+own+a+store">Claim your store →</a></div></section>
<section class="wrap signup"><h2>Get updates</h2><p class="sub">We'll email you when we add the Bronx and Staten Island. No spam.</p>
<form name="launch-list" method="POST" action="/api/subscribe" class="inline">
<p class="hidden"><label>Leave this empty <input name="company"></label></p>
<label class="sr" for="email">Email address</label><input id="email" type="email" name="email" placeholder="you@example.com" required autocomplete="email"><button type="submit">Notify me</button></form>
<p class="small">See our <a href="/privacy.html">privacy policy</a>.</p></section>'''
home_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "SeekMakeup", "url": SITE + "/"}
page("/", f"SeekMakeup — Find the stores in {AREA} that carry your makeup brands",
     f"Search {len(brands)} makeup brands across {len(stores)} {AREA} stores. A directory of brands and the stores that sell them; no live inventory.",
     home, jsonld=home_ld, scripts='<script src="/assets/finder.js" defer></script>')
shutil.copy(os.path.join(ROOT, "scripts", "finder.js"), os.path.join(PUB, "assets", "finder.js"))

# Sitemap
urls = ["/", "/contact.html", "/privacy.html"] + SITEMAP
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
    f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n"
open(os.path.join(PUB, "sitemap.xml"), "w").write(sm)

print(f"brands {len(brands)} | stores {len(stores)} | links {len(carries)} | pages {len(urls)}")
print("brands with no store:", [b["Brand"] for b in brands if not by_brand.get(b["Brand"])])
print("stores with no brands:", [s["Store"] for s in stores if not by_store.get(s["Store"])])
