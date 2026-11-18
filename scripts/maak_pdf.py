#!/usr/bin/env python3
"""
Maakt van een Praktijkscan-uitslag (markdown) een opgemaakte pdf in de stijl van Praktijkwerkbank.

Onderdeel van de Praktijkscan van Jens Kemna (praktijkwerkbank.nl). Versie 3.5.
Licentie van dit script: MIT, zie LICENSE-MIT in de hoofdmap. De teksten van de skill vallen onder CC BY 4.0.

De pdf heeft vier pagina's (drie met --kort, of als de uitslag geen plek en geen kop bevat):
  1. Overzicht: de totaalscore, in één zin, het eerste scherm nu en straks (schermafbeelding naast een schets
     met de aanbevolen kop; zonder schermafbeelding de scan in één beeld), wat al werkt en de concurrentie.
  2. Wat nu: de drie dingen die het meest opleveren, hoe je meet en hoe je het aanpakt.
  3. Je plek en je kop: het voorstel voor de plek, de kopvarianten, wat de scan niet weet,
     en (met afzender.json) een uitnodiging of pitch.
  4. Bijlage: de twaalf bouwstenen, per bouwsteen uitleg, uitkomst, wat je zag en welke vragen een ja of een nee kregen.

Het script controleert de uitslag eerst. Wat ontbreekt of te lang is, meldt het als "Let op"; zonder
bouwstenen maakt het geen pdf.

Gebruik:
  python3 maak_pdf.py scan.md
  python3 maak_pdf.py scan.md --uit map/x.pdf
  python3 maak_pdf.py scan.md --html               (alleen de html; zelf afdrukken naar pdf)
  python3 maak_pdf.py scan.md --afzender pad.json  (anders: afzender.json naast SKILL.md, als die er is)
  python3 maak_pdf.py scan.md --kort               (drie pagina's, zonder de pagina met plek en kop)

Het markdown-bestand volgt het format uit SKILL.md (stap 4). Het script rekent de scores zelf uit de checks
en kiest de uitleg en de vragen bij de doelgroep (regel "Doelgroep: particulier" of "Doelgroep: zakelijk").

Nodig: Python 3 (alleen standaardbibliotheek) en Google Chrome, Chromium, Brave of Edge.
"""

import argparse
import base64
import datetime
import html
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
SKILL = HIER.parent
ASSETS = SKILL / "assets"

# ---------- de twaalf bouwstenen (gelijk houden met referentie/08-scoringslijst.md) ----------

GROEPEN = [
    ("A", "De waarde", "Waarom zou iemand ja zeggen?"),
    ("B", "Het aanbod", "Waarom jou en geen ander?"),
    ("C", "Gevonden en gekozen", "Vinden ze je, en zetten ze de stap?"),
]

# groep, naam, {P: (uitleg, labels), Z: (uitleg, labels)}
BOUWSTENEN = [
    ("A", "Droomresultaat", {
        "P": ("Wat er voor je cliënt écht anders is na afloop, in zijn eigen woorden.",
              ["Resultaat in momenten uit het dagelijks leven", "Bovenaan of in het eerste aanbodblok", "In woorden van cliënten",
               "Eén zin met een concreet moment uit de pijn", "Geen genezingsclaim of cijfer zonder bron"]),
        "Z": ("Wat er na afloop anders is voor de organisatie én voor de deelnemers.",
              ["Resultaat in momenten uit het werk", "Bovenaan of in het eerste aanbodblok", "In woorden van opdrachtgevers of deelnemers",
               "Eén zin die de situatie van de koper raakt", "Geen cijfer of \"bewezen\" zonder bron"])}),
    ("A", "Geloof dat het lukt", {
        "P": ("Bewijs en aanpak waardoor je bezoeker gelooft dat het bij hém werkt.",
              ["Plan in twee tot vier stappen", "Ervaringen met naam, situatie en verschil", "Externe reviews of eigen cijfers",
               "Zegt voor wie het niet is", "Eigen ervaring of jaren met dit soort vraag"]),
        "Z": ("Bewijs en aanpak waardoor de koper gelooft dat het bij zijn organisatie werkt.",
              ["Aanpak in twee tot vier stappen", "Cases met naam, functie en organisatie", "Klantnamen, aantallen of reviews",
               "Zegt voor wie het niet is", "Ervaring in de sector van de koper"])}),
    ("A", "Snelheid", {
        "P": ("Hoe snel iemand het eerste verschil merkt, en hoe lang het duurt.",
              ["Wanneer je het eerste verschil merkt", "Na de eerste afspraak iets mee", "Duur en frequentie",
               "Hoe snel je kunt beginnen", "Een moment om samen te kijken of het werkt"]),
        "Z": ("Hoe snel de organisatie en de deelnemers resultaat zien.",
              ["Wanneer je het eerste effect merkt", "Deelnemers gaan met iets naar huis", "Duur van workshop of programma",
               "Een moment om het resultaat te meten"])}),
    ("A", "Gemak", {
        "P": ("Hoe weinig moeite, tijd en spanning het iemand kost.",
              ["Wat je niet hoeft", "Vorm en tijden die passen", "Tussendoor een vraag kunnen stellen", "Eerlijk wat het van je vraagt",
               "Je weet hoe een eerste sessie gaat"]),
        "Z": ("Hoe weinig moeite het de organisator en de deelnemers kost.",
              ["Wat de organisator niet hoeft", "Vorm past bij de organisatie", "Eén contactpersoon, snel antwoord",
               "Wat het van deelnemers vraagt", "Je weet hoe de dag verloopt"])}),
    ("B", "Garantie", {
        "P": ("Hoeveel risico jij overneemt, zodat ja zeggen veilig voelt.",
              ["Kennismaking of losse eerste sessie", "Zekerheid na de eerste stap", "Concreet, zonder kleine letters",
               "Bij de prijs of de knop", "Nergens resultaat gegarandeerd, ook niet in reviews"]),
        "Z": ("Hoeveel risico jij overneemt van de organisatie die boekt.",
              ["Klein beginnen kan, met een vaste prijs", "Zekerheid over de uitvoering", "Milde, concrete voorwaarden",
               "Bij de prijs of de knop", "Nergens resultaat gegarandeerd, ook niet in reviews"])}),
    ("B", "Pakket en naam", {
        "P": ("Een aanbod met een naam, begin en einde, in plaats van losse uren.",
              ["Hoofdaanbod met begin en einde", "Naam die zegt voor wie en wat", "Extra's die een drempel wegnemen",
               "Hoofdaanbod vooraan", "Vervolg, geen grote sprong"]),
        "Z": ("Een programma met een naam, begin en einde, in plaats van losse workshops.",
              ["Programma met begin en einde", "Naam die zegt voor wie en wat", "Extra's die werk en werving wegnemen",
               "Hoofdaanbod vooraan", "Vervolg, geen grote sprong"])}),
    ("B", "Prijs", {
        "P": ("Staat de prijs er, na de waarde, en snap je waarom hij zo is?",
              ["Vast bedrag voor het hoofdaanbod", "Vergoeding en wie betaalt", "Betaalmoment en annulering", "Waarde boven de prijs",
               "Eerlijke reden voor de prijs"]),
        "Z": ("Een zichtbare prijs met wat erbij zit, zodat de koper intern kan rekenen.",
              ["Bedrag met wat erbij zit", "Btw en bijkomende kosten", "Betaalmoment, facturatie, aantallen",
               "Waarde boven de prijs", "Eerlijke reden voor de prijs"])}),
    ("B", "Reden om nu", {
        "P": ("Een eerlijke reden om nu te beginnen, zonder druk.",
              ["Echte capaciteit met een getal", "Een eerlijk moment", "Wat niets doen kost, zacht", "Geen nepurgentie",
               "Interesse- of wachtlijst"]),
        "Z": ("Een eerlijk moment om te boeken: budget, seizoen, beschikbare data.",
              ["Echte beschikbaarheid van data", "Een eerlijk moment (budget, seizoen)", "Wat wachten kost, met bron",
               "Geen nepurgentie", "Alvast iets vastleggen"])}),
    ("C", "Plek", {
        "P": ("Voor wie je er bent en waarmee, op een plek die nog vrij is.",
              ["Eén doelgroep of situatie vooraan", "\u201cDe praktijk die ...\u201d is af te maken", "Ander aanbod erachter",
               "Zegt wat gelezen concurrenten niet zeggen", "Geen instapeis als belofte"]),
        "Z": ("Voor welke organisaties je er bent en waarmee, op een plek die nog vrij is.",
              ["Eén soort organisatie vooraan", "\u201cWij zijn het bedrijf dat ...\u201d", "Ander aanbod erachter",
               "Zegt wat gelezen concurrenten niet zeggen", "Geen instapeis als belofte"])}),
    ("C", "Helderheid", {
        "P": ("Snapt een vreemde op zijn telefoon in vijf seconden wat dit is?",
              ["Voor wie, waarmee, waar bovenaan", "Kop in woorden van cliënten", "Meer jij dan ik of wij",
               "Echte foto en rust bovenaan", "Koppen en knoppen alleen zeggen al genoeg"]),
        "Z": ("Snapt een koper in vijf seconden wat je voor zijn organisatie doet?",
              ["Voor wie, waarmee, waar bovenaan", "Kop in woorden van de koper", "Meer jullie dan ik of wij",
               "Echte foto van de uitvoering, rust", "Koppen en knoppen alleen zeggen al genoeg"])}),
    ("C", "Vindbaarheid", {
        "P": ("Word je gevonden op de woorden die mensen intypen, ook in AI?",
              ["Probleem of beroep plus plaats in de titel", "Zelfde woorden in kop en eerste alinea", "Aantoonbare vraag",
               "Profiel, gegevens en plaatspagina's kloppen", "Wat AI over je zegt, klopt"]),
        "Z": ("Word je gevonden op de woorden die kopers intypen, ook in AI en op LinkedIn?",
              ["Dienst plus doelgroep of regio in de titel", "Zelfde woorden in kop en eerste alinea", "Aantoonbare vraag",
               "Profiel, LinkedIn en regiopagina's", "Wat AI over je zegt, klopt"])}),
    ("C", "Volgende stap", {
        "P": ("Eén duidelijke, kleine stap, en daarna een pad dat werkt.",
              ["Eén hoofdknop, overal dezelfde", "Knop met werkwoord, wat en hoeveel, pad eronder", "Direct een tijd of kort formulier",
               "Pad na de klik werkt", "Kleinere stap voor wie nog niet wil praten"]),
        "Z": ("Eén duidelijke stap naar een voorstel, en iets om intern door te sturen.",
              ["Eén hoofdknop, overal dezelfde", "Knop zegt wat je krijgt en wanneer", "Belafspraak of kort formulier",
               "Pad na de klik werkt", "Iets om intern door te sturen"])}),
]

BANDEN = [
    (75, "Je site doet zijn werk", "Nu verfijnen en meten."),
    (50, "De basis staat", "Een paar bouwstenen kunnen nog meer opleveren."),
    (25, "Hier valt veel te winnen", "Begin met de drie dingen op pagina 2."),
    (0, "Veel ruimte om te groeien", "Begin bij de plek en het aanbod, dan de site."),
]

STANDEN = {"groen": "Staat goed", "oranje": "Kan beter", "rood": "Pak dit aan", "grijs": "Niet gecontroleerd"}

LOGO = ('<svg viewBox="0 0 40 40"><rect width="40" height="40" rx="11" fill="#FFC15C"/>'
        '<path d="M8 14h24v5H8zm3 5h4v13h-4zm14 0h4v13h-4zm-10 5h10v3H15z" fill="#1C1405"/></svg>')

ICOON = {
    "j": '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="#CDF1E2"/><path d="M4.8 8.3l2.1 2.1 4.3-4.6" fill="none" stroke="#0B6E52" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "n": '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="#FFE1DD"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5" fill="none" stroke="#9C2A1E" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "?": '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="rgba(15,29,54,0.08)"/><text x="8" y="11.4" text-anchor="middle" font-size="9.5" font-family="Archivo" font-weight="800" fill="#5E6983">?</text></svg>',
}
PIJL = '<svg viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="#1C1405" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def font_face():
    regels = []
    for naam, gewicht, bestand in [("Archivo", 500, "archivo-500.ttf"), ("Archivo", 700, "archivo-700.ttf"),
                                    ("Archivo", 800, "archivo-800.ttf"), ("Instrument Sans", 400, "instrument-sans-400.ttf"),
                                    ("Instrument Sans", 500, "instrument-sans-500.ttf"), ("Instrument Sans", 600, "instrument-sans-600.ttf"),
                                    ("Instrument Sans", 700, "instrument-sans-700.ttf")]:
        pad = ASSETS / bestand
        if pad.exists():
            regels.append(f'@font-face{{font-family:"{naam}";font-weight:{gewicht};src:url("{pad.as_uri()}") format("truetype")}}')
    return "\n".join(regels)


# ---------- markdown lezen ----------

def inline(t):
    t = re.sub(r'"([^"]*)"', "\u201c\\1\u201d", t)
    t = re.sub(r"(?<=\w)'(?=\w)", "\u2019", t)
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r'<span class="vul">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<!>)\[((?:INVULLEN|VOORBEELD|CHECK)[^\]]*)\]", r'<span class="vul">[\1]</span>', t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s\"'<>]+)\)", r'<a href="\2">\1</a>', t)   # geen aanhalingsteken of spatie in het adres
    return t


def lees(tekst):
    data = {"titel": "", "meta": {}, "secties": {}}
    huidig = None
    for r in tekst.splitlines():
        if r.startswith("# ") and not data["titel"]:
            data["titel"] = re.sub(r"^Praktijkscan:\s*", "", r[2:].strip())
            continue
        if r.startswith("## "):
            huidig = r[3:].strip()
            data["secties"][huidig] = []
            continue
        if huidig is None:
            m = re.match(r"^(Website|Datum|Agenda|Doelgroep|Gescoord|Schermafbeelding)\s*:\s*(.+)$", r.strip())
            if m:
                data["meta"][m.group(1).lower()] = m.group(2).strip()
            continue
        data["secties"][huidig].append(r)
    return data


def sectie(data, *namen):
    for k in data["secties"]:
        if any(k.lower().startswith(n) for n in namen):
            return data["secties"][k]
    return []


def tabel(regels):
    rijen = []
    for r in regels:
        if r.lstrip().startswith("|"):
            cellen = [c.strip() for c in r.strip().strip("|").split("|")]
            if cellen and all(re.fullmatch(r":?-{2,}:?", c) for c in cellen if c):
                continue
            rijen.append(cellen)
    return rijen[1:] if rijen else []


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower().replace("ë", "e").replace("é", "e"))


JA = {"j", "ja", "y", "yes"}
NEE = {"n", "nee", "no"}
OPEN = {"?", "onbekend", "nvt", "ntb", "-"}


def lees_tekens(cel, meldingen, naam):
    """Zet de cel met antwoorden om in j, n en ?. Wat niet te lezen is, wordt ? en komt in de meldingen."""
    cel = cel.strip().lower()
    delen = [d for d in re.split(r"[\s,;/|]+", cel) if d]
    if len(delen) == 1 and len(delen[0]) > 1 and re.fullmatch(r"[jn?]+", delen[0]):
        delen = list(delen[0])
    uit = []
    for d in delen:
        kaal = d.strip(".()") if d != "?" else d
        kaal = kaal.replace(".", "")
        if kaal in JA:
            uit.append("j")
        elif kaal in NEE:
            uit.append("n")
        elif kaal in OPEN:
            uit.append("?")
        else:
            uit.append("?")
            meldingen.append(f"{naam}: het antwoord '{d}' is geen j, n of ? en telt als niet gecontroleerd.")
    return uit


def lees_bouwstenen(regels, meldingen=None):
    meldingen = meldingen if meldingen is not None else []
    uit = {}
    for cellen in tabel(regels):
        if len(cellen) < 2:
            continue
        naam = norm(re.sub(r"^\d+\s*", "", cellen[0]))
        if len(naam) < 3:
            continue
        for b in BOUWSTENEN:
            doel = norm(b[1])
            if naam == doel or (len(naam) >= 4 and (doel.startswith(naam) or naam.startswith(doel) or doel[:6] == naam[:6])):
                uit[b[1]] = {"tekens": lees_tekens(cellen[1], meldingen, b[1]), "zag": cellen[2] if len(cellen) > 2 else ""}
                break
    return uit


def woorden(s):
    return len(re.findall(r"[\w'’%-]+", re.sub(r"`?\[(?:VOORBEELD|INVULLEN|CHECK)[^\]]*\]`?", "", s or "")))


def onder(data, *namen):
    """Regels van een sectie (## Naam) of van een onderdeel van de onderbouwing (### Naam)."""
    r = sectie(data, *namen)
    if r:
        return r
    uit, aan = [], False
    for regel in sectie(data, "onderbouwing"):
        if regel.startswith("### "):
            aan = any(regel[4:].strip().lower().startswith(n) for n in namen)
            continue
        if aan:
            uit.append(regel)
    return uit


RANG = [("eerste", 0), ("tweede", 1), ("derde", 2), ("1", 0), ("2", 1), ("3", 2)]


def welke(aanrader):
    for woord, i in RANG:
        if re.search(r"\b" + woord + r"\b", aanrader.lower()):
            return i
    return None


def lees_plek(regels, vrij=False):
    """Varianten voor de plek: de opsomming na de regel 'Voorstel voor de plek'. Alleen in een eigen sectie
    '## Je plek' (vrij) tellen alle opsommingstekens; in de onderbouwing staan er ook andere lijsten."""
    start = next((i for i, r in enumerate(regels) if re.match(r"^\s*\**voorstel voor de plek", r.strip(), re.I)), None)
    if start is None and not vrij:
        return [], ""
    blok = regels[start + 1:] if start is not None else regels
    varianten, aanrader = [], ""
    for r in blok:
        s = r.strip()
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            tekst, noot, aan = m.group(1).strip(), "", False
            h = re.search(r"\s*\(([^()]*)\)\s*$", tekst)
            if h:
                noot, tekst = h.group(1).strip(), tekst[:h.start()].strip()
                if noot.lower().startswith("aanrader"):
                    aan, noot = True, noot.split(":", 1)[1].strip() if ":" in noot else ""
                noot = noot[:1].upper() + noot[1:]
                if noot and noot[-1] not in ".!?":
                    noot += "."
            varianten.append({"tekst": tekst, "noot": noot, "aan": aan})
        elif re.match(r"^aanrader\s*:", s, re.I):
            aanrader = s.split(":", 1)[1].strip()
        elif varianten and s and start is not None:
            break
    varianten = varianten[:3]
    if aanrader and not any(v["aan"] for v in varianten):
        i = welke(aanrader)
        if i is not None and i < len(varianten):
            varianten[i]["aan"] = True
    return varianten, aanrader


def lees_koppen(regels):
    koppen = [r.strip().lstrip(">").strip() for r in regels if r.strip().startswith(">")][:3]
    koppen = [k for k in koppen if k]
    aanrader = next((r.split(":", 1)[1].strip() for r in regels if re.match(r"^\s*aanrader\s*:", r, re.I)), "")
    aanname = any(re.match(r"^\s*\**aanname", r, re.I) for r in regels)
    i = welke(aanrader) if aanrader else None
    return koppen, aanrader, aanname, (i if i is not None and i < len(koppen) else None)


UITSLUIT = {("Droomresultaat", "e"), ("Garantie", "e"), ("Reden om nu", "d"), ("Plek", "e")}


def lees_bewijs(regels):
    """Bewijs per antwoord uit ### Bewijs: {bouwsteen: {letter: (antwoord, tekst)}}."""
    uit, huidig = {}, None
    for r in regels:
        s = r.strip()
        if not s:
            continue
        m = re.match(r"^[-*]\s*([a-e])\s*[:(]?\s*(ja|nee|j|n|\?)\s*\)?\s*[:,]?\s*(.*)$", s, re.I)
        if m and huidig:
            a = m.group(2).lower()
            uit[huidig][m.group(1).lower()] = ("j" if a in JA else "n" if a in NEE else "?", m.group(3).strip())
            continue
        naam = norm(re.sub(r"^\d+\.?\s*", "", s.strip("*#: ")))
        for b in BOUWSTENEN:
            if len(naam) >= 4 and (naam == norm(b[1]) or norm(b[1])[:6] == naam[:6]):
                huidig = b[1]
                uit.setdefault(huidig, {})
                break
    return uit


def lees_voorbehoud(regels):
    punten = [re.sub(r"^\s*[-*]\s+", "", r).strip() for r in regels if re.match(r"^\s*[-*]\s+", r)]
    if punten:
        return punten[:3]
    proza = " ".join(r.strip() for r in regels if r.strip() and not r.startswith("Methode:"))
    uit, n = [], 0
    for zin in re.split(r"(?<=[.!?])\s+", proza):
        if not zin:
            continue
        if n and n + woorden(zin) > 60:
            break
        uit.append(zin); n += woorden(zin)
    return [" ".join(uit)] if uit else []


def lees_concurrentie(regels):
    c = {}
    for r in regels:
        m = re.match(r"^\s*[-*]?\s*(Gelezen|Iedereen zegt|Niemand zegt|Leer van)\s*:\s*(.+)$", r.strip(), re.I)
        if m:
            c[m.group(1).lower()] = m.group(2).strip()
    return c


def stand(ja, getoetst):
    if getoetst < 3:
        return "grijs"
    f = ja / getoetst
    return "groen" if f >= 0.8 else "oranje" if f >= 0.4 else "rood"


def lees_drie(regels):
    items, huidig = [], None
    for r in regels:
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", r)
        if m:
            huidig = {"tekst": m.group(2).strip(), "voorbeeld": []}
            items.append(huidig)
            continue
        if huidig is None or not r.strip():
            continue
        s = r.strip()
        w = re.match(r"^week\s*:\s*(\d+)", s, re.I)
        if w:
            huidig["week"] = int(w.group(1))
        elif s.startswith(">"):
            huidig["voorbeeld"].append(s.lstrip(">").strip())
        else:
            huidig["tekst"] += " " + s
    for it in items:
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", it["tekst"])
        it["kop"], it["rest"] = (m.group(1).rstrip("."), m.group(2)) if m else ("", it["tekst"])
    return items[:3]



def lees_afzender(pad):
    if not pad or not Path(pad).exists():
        return None
    try:
        a = json.loads(Path(pad).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    foto = a.get("foto")
    if foto:
        fp = Path(foto)
        if not fp.is_absolute():
            fp = Path(pad).parent / fp
        if fp.exists():
            mime = mimetypes.guess_type(str(fp))[0] or "image/jpeg"
            a["foto_src"] = f"data:{mime};base64," + base64.b64encode(fp.read_bytes()).decode()
    return a


# ---------- html-onderdelen ----------


def meter(pct):
    r, dikte = 52, 11
    lengte = math.pi * r
    return f"""<svg class="meter" viewBox="0 0 132 74" aria-hidden="true">
<path d="M14 66 A52 52 0 0 1 118 66" fill="none" stroke="rgba(242,244,249,0.16)" stroke-width="{dikte}" stroke-linecap="round"/>
<path d="M14 66 A52 52 0 0 1 118 66" fill="none" stroke="#FFC15C" stroke-width="{dikte}" stroke-linecap="round"
 stroke-dasharray="{lengte * pct / 100:.1f} {lengte:.1f}"/></svg>"""


def kopbalk(rechts):
    return f"""<div class="top"><div class="merk">{LOGO}<div>praktijk<span>werkbank</span></div></div>
<div class="meta">{rechts}</div></div>"""


def ruimte(tekst):
    delen = [d.strip() for d in re.split(r";", tekst or "") if d.strip()]
    vink = ('<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7.5" fill="#FFC15C"/><path d="M4.8 8.3l2.1 2.1 4.3-4.6" fill="none" '
            'stroke="#1C1405" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return '<ul class="ruimtelijst">' + "".join(f"<li>{vink}<span>{inline(d)}</span></li>" for d in delen) + "</ul>"


ICONEN = {
    "kennen": '<path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20c.8-3.6 3.8-5.5 7.5-5.5s6.7 1.9 7.5 5.5"/>',
    "veilig": '<path d="M12 3l7 3v5.5c0 4.3-2.9 7.6-7 9.5-4.1-1.9-7-5.2-7-9.5V6z"/><path d="M8.8 12.2l2.2 2.2 4.3-4.6"/>',
    "bouwen": '<path d="M3 20h18M5 20V10h14v10M9 10V6h6v4M9 14h6"/>',
    "skills": '<path d="M12 3.5l2.3 5 5.2.6-3.9 3.6 1.1 5.3-4.7-2.7-4.7 2.7 1.1-5.3-3.9-3.6 5.2-.6z"/>',
}


def icoon(naam):
    pad = ICONEN.get(naam, ICONEN["skills"])
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="#1C1405" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{pad}</svg>')


def blokjes(checks, st):
    """Eén blokje per vraag: eerst de ja's (in de kleur van de stand), dan de nee's (lichte tint), dan wat niet gecontroleerd is (grijs)."""
    volg = sorted(checks, key=lambda c: {"j": 0, "n": 1}.get(c, 2))
    soort = {"j": "vol", "n": "leeg", "?": "open"}
    return f'<span class="seg {st}">' + "".join(f'<i class="{soort.get(c, "open")}"></i>' for c in volg) + "</span>"


def foto_src(pad, basis):
    if not pad:
        return ""
    fp = Path(pad)
    if not fp.is_absolute():
        fp = Path(basis) / fp
    if not fp.exists():
        return ""
    mime = mimetypes.guess_type(str(fp))[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(fp.read_bytes()).decode()


CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
@page{size:A4;margin:0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact;font-size:10pt}
body{font-family:"Instrument Sans",system-ui,sans-serif;color:#0F1D36;background:#F2F4F9}
h1,h2,h3,.band,.naam,.ghd h2{text-wrap:balance}
p,.leer,.punt span,.ruimtelijst span{text-wrap:pretty}
.blad{--u:10pt;width:210mm;height:297mm;position:relative;overflow:hidden;padding:3.3rem 3.6rem 2.6rem;
 background:
  radial-gradient(64mm 48mm at 4% 1%,rgba(255,224,166,.95),rgba(255,224,166,0) 70%),
  radial-gradient(74mm 52mm at 99% 3%,rgba(196,222,255,.9),rgba(196,222,255,0) 70%),
  radial-gradient(84mm 64mm at 102% 72%,rgba(205,241,226,.72),rgba(205,241,226,0) 70%),
  radial-gradient(84mm 64mm at -2% 98%,rgba(255,237,168,.8),rgba(255,237,168,0) 70%),
  #F2F4F9;display:flex;flex-direction:column;gap:1.1rem;page-break-after:always}
.blad:last-child{page-break-after:auto}
.blad>*{flex-shrink:0}
.top{display:flex;align-items:center;justify-content:space-between}
.merk{display:flex;align-items:center;gap:.55rem;font-family:Archivo;font-weight:800;font-size:1.05rem;letter-spacing:-.01em}
.merk svg{width:2rem;height:2rem}
.merk span{color:#C46A00}
.top .meta{display:flex;gap:.55rem;align-items:center;color:#5E6983;font-size:.8rem;font-weight:500;white-space:nowrap}
.pil{display:inline-block;border-radius:999px;padding:.26rem .8rem;font-family:Archivo;font-weight:700;font-size:.74rem;letter-spacing:.02em;white-space:nowrap;line-height:1.3}
.pil.amber{background:rgba(255,183,64,.22);color:#7E4400}
.pil.glas{background:#FBFCFE;border:1px solid #DDE3EE;color:#24314D;font-weight:500;font-family:"Instrument Sans";font-size:.8rem}
.pil b{font-weight:800;color:#0F1D36;font-family:Archivo}
.glas{background:#FBFCFE;border:1px solid #DDE3EE;border-radius:1.3rem;
 ;}
.kicker{display:block;font-family:Archivo;font-weight:700;font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;color:#8F4D00}
.vul{background:rgba(255,183,64,.28);border-radius:.25rem;padding:0 .2rem;color:#7E4400;font-size:.92em}
/* blokjes */
.seg{display:flex;gap:.2rem}
.seg i{display:block;height:.55rem;border-radius:99px;box-sizing:border-box}
.seg.groen i.vol{background:#11956F}.seg.oranje i.vol{background:#E39A1E}.seg.rood i.vol{background:#D9483B}
.seg.groen i.leeg{background:#D3EEE5}.seg.oranje i.leeg{background:#F8E6C6}.seg.rood i.leeg{background:#F6CFCB}.seg.grijs i.leeg{background:#E3E7EF}
.seg i.open{background:#F2F4F9;border:1px dashed #A9B2C4}
.stip{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;margin-right:.35rem;vertical-align:.05rem;flex:none}
.stip.open{background:#F2F4F9;border:1px dashed #A9B2C4;box-sizing:border-box}
.stip.groen{background:#11956F}.stip.oranje{background:#E39A1E}.stip.rood{background:#D9483B}.stip.grijs{background:rgba(15,29,54,.2)}
/* pagina 1 */
.held{display:grid;grid-template-columns:minmax(0,1fr) 19rem;gap:1.2rem;align-items:stretch}
.held .links{display:flex;flex-direction:column;justify-content:center}
h1{font-family:Archivo;font-weight:800;font-size:2.9rem;line-height:1.02;letter-spacing:-.028em;margin:.35rem 0 .3rem}
.url{color:#4A5672;font-weight:500;font-size:.95rem}
.pillen{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.8rem}
.score{background:#0F1D36;color:#F2F4F9;border-radius:1.4rem;padding:1rem 1.15rem;position:relative;overflow:hidden;
 ;display:flex;flex-direction:column;gap:.55rem}
.score>*{position:relative}
.score .kicker{color:#FFC15C}
.scorerij{display:grid;grid-template-columns:8.6rem minmax(0,1fr);gap:.9rem;align-items:center}
.metervak{position:relative;width:8.6rem}
.meter{width:100%;display:block}
.getal{position:absolute;left:0;right:0;bottom:-.1rem;text-align:center;font-family:Archivo;font-weight:800;font-size:2.6rem;line-height:1;letter-spacing:-.03em}
.getal small{font-size:.78rem;font-weight:700;color:rgba(242,244,249,.7);letter-spacing:0;margin-left:.1rem}
.band{font-family:Archivo;font-weight:800;font-size:1.3rem;line-height:1.1;letter-spacing:-.01em}
.bandsub{color:rgba(242,244,249,.84);font-size:.78rem;line-height:1.42}
.bandsub b{color:#FFC15C;font-weight:700}
.eenzin{padding:1rem 1.25rem}
.eenzin p{font-size:1.02rem;line-height:1.5;margin-top:.3rem}
.duo{display:grid;grid-template-columns:minmax(0,1.32fr) minmax(0,1fr);gap:1rem;flex:1 1 0;min-height:0}
.grafiek{padding:1rem 1.2rem 1.05rem;display:flex;flex-direction:column}
.ghd{margin-bottom:.5rem}
.ghd h2{font-family:Archivo;font-weight:800;font-size:1.22rem;letter-spacing:-.012em}
.ghd .schaal{display:block;font-size:.74rem;color:#5E6983;margin-top:.15rem}
.ggroepen{display:grid;grid-template-rows:repeat(3,minmax(0,1fr));flex:1;gap:.7rem}
.ggroep{display:flex;flex-direction:column}
.gkop{display:flex;align-items:center;gap:.5rem;padding:.45rem 0 .3rem;border-bottom:1px solid rgba(15,29,54,.1);margin-bottom:.15rem}
.letter{width:1.55rem;height:1.55rem;border-radius:.5rem;background:#FFC15C;color:#1C1405;font-family:Archivo;font-weight:800;
 display:flex;align-items:center;justify-content:center;font-size:.82rem;flex:none}
.gkop b{font-family:Archivo;font-weight:800;font-size:.92rem}
.gkop .gpct{margin-left:auto;font-family:Archivo;font-weight:800;font-size:.82rem;color:#4A5672}
.grij{display:grid;grid-template-columns:9rem minmax(0,1fr) 4.4rem;gap:.7rem;align-items:center;flex:1;min-height:1.6rem}
.gnaam{font-size:.88rem;font-weight:600;color:#0F1D36;white-space:nowrap}
.grij .seg i{flex:1;height:.85rem}
.grij .seg{gap:.22rem}
.gwaarde{font-size:.76rem;color:#4A5672;white-space:nowrap;text-align:right}
.gwaarde b{font-family:Archivo;font-weight:800;color:#0F1D36;font-size:.84rem}
.rechts{display:flex;flex-direction:column;gap:.85rem;min-width:0;min-height:0}
.werkt,.conc{padding:1rem 1.15rem}
.werkt h3,.conc h3{font-family:Archivo;font-weight:800;font-size:1.12rem;letter-spacing:-.01em;margin-bottom:.6rem}
.werkt .punt{display:grid;grid-template-columns:1.05rem minmax(0,1fr);gap:.5rem;font-size:.82rem;line-height:1.42;color:#24314D;align-items:start;margin-bottom:.45rem}
.werkt .punt:last-child{margin-bottom:0}
.werkt .punt svg{width:1.05rem;height:1.05rem;margin-top:.1rem}
.uitlegkaart{padding:1rem 1.15rem 1.05rem;flex:1 1 0;min-height:0;display:flex;flex-direction:column;gap:.6rem}
.uitlegkaart h3{font-family:Archivo;font-weight:800;font-size:1.12rem;letter-spacing:-.01em;line-height:1.15}
.tegels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem;margin:.1rem 0 .15rem}
.tegel{border-radius:.85rem;padding:.6rem .7rem .55rem;display:grid;grid-template-columns:1.6rem minmax(0,1fr);grid-template-rows:auto auto;column-gap:.5rem;align-items:center}
.tegel.op{background:#FFC15C;color:#1C1405}
.tegel.neer{background:#0F1D36;color:#F2F4F9}
.tegel .tp{grid-row:1 / span 2;width:1.6rem;height:1.6rem;border-radius:50%;display:flex;align-items:center;justify-content:center}
.tegel.op .tp{background:rgba(28,20,5,.1)}.tegel.neer .tp{background:rgba(242,244,249,.14)}
.tegel .tp svg{width:1rem;height:1rem}
.tegel b{font-family:Archivo;font-weight:800;font-size:.72rem;line-height:1.15;letter-spacing:-.01em;overflow-wrap:break-word}
.tegel small{font-size:.66rem;opacity:.8;line-height:1.2}
.uitlegkaart p{font-size:.78rem;line-height:1.46;color:#24314D;margin-top:auto}
.uitlegkaart p b{font-family:Archivo;font-weight:800;color:#0F1D36}
.conc .gelezen{font-size:.72rem;color:#5E6983;margin:-.35rem 0 .65rem}
.conc .vak{margin-bottom:.7rem}
.conc .vak:last-child{margin-bottom:0}
.conc .vak .kicker{margin-bottom:.35rem;color:#4A5672;font-size:.64rem}
.conc .vak.ruimte .kicker{color:#8F4D00}
.chip{display:inline-block;border-radius:99px;padding:.2rem .6rem;font-size:.74rem;margin:0 .25rem .3rem 0;line-height:1.3;white-space:nowrap;
 background:rgba(15,29,54,.07);color:#4A5672}
.ruimtelijst{list-style:none;display:grid;gap:.3rem}
.ruimtelijst li{display:grid;grid-template-columns:.9rem minmax(0,1fr);gap:.45rem;font-size:.8rem;line-height:1.38;color:#3B2A0B;font-weight:600;align-items:start}
.ruimtelijst li svg{width:.9rem;height:.9rem;margin-top:.15rem}
.conc .leer{font-size:.8rem;line-height:1.45;color:#24314D}
.voet{display:flex;justify-content:space-between;align-items:flex-end;gap:1.5rem;font-size:.72rem;color:#4A5672;line-height:1.45}
.legenda{display:flex;gap:.9rem;align-items:center;flex-wrap:wrap}
.legenda span{display:inline-flex;align-items:center;font-weight:700;color:#24314D}
.bron{text-align:right;font-weight:600;color:#4A5672;white-space:nowrap}
/* pagina 2 */
.paginakop h2{font-family:Archivo;font-weight:800;font-size:2.15rem;line-height:1.04;letter-spacing:-.025em;margin-top:.3rem}
.paginakop h2 span{color:#C46A00}
.paginakop p{color:#4A5672;font-size:.9rem;margin-top:.35rem;line-height:1.45}
.raster{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-rows:auto repeat(4,minmax(0,1fr));gap:.6rem .8rem;flex:1 1 0;min-height:0}
.kolomkop{padding:.7rem 1.05rem .75rem;background:#0F1D36;color:#F2F4F9;border-radius:1.15rem;display:flex;flex-direction:column}
.kolomkop .rij1{display:flex;align-items:center;gap:.55rem}
.kolomkop h3{font-family:Archivo;font-weight:800;font-size:1.12rem;letter-spacing:-.01em;white-space:nowrap;line-height:1.1}
.kolomkop .gp{white-space:nowrap;margin-left:auto;font-family:Archivo;font-weight:800;font-size:.82rem;color:#FFC15C}
.kolomkop .vraag{color:rgba(242,244,249,.86);font-size:.82rem;font-weight:500;margin-top:.3rem;line-height:1.3}
.steen{padding:.72rem 1rem .78rem;display:flex;flex-direction:column;gap:.34rem;min-width:0}
.naam{font-family:Archivo;font-weight:800;font-size:1.04rem;letter-spacing:-.005em;line-height:1.15;white-space:nowrap}
.uitleg{color:#5E6983;font-size:.74rem;line-height:1.3;min-height:2.6em}
.stand{display:flex;align-items:center;gap:.6rem;height:1rem}
.stand .seg i{width:1.15rem}
.label{font-size:.72rem;color:#4A5672;white-space:nowrap}
.label b{font-family:Archivo;font-weight:800;color:#0F1D36;margin-right:.2rem}
.zag{font-size:.82rem;line-height:1.38;color:#24314D;border-top:1px solid rgba(15,29,54,.08);padding-top:.38rem}
.vragen{list-style:none;display:grid;gap:.2rem;margin-top:auto;border-top:1px solid rgba(15,29,54,.08);padding-top:.42rem}
.vragen li{display:grid;grid-template-columns:.82rem minmax(0,1fr);gap:.4rem;font-size:.72rem;line-height:1.24;color:#5E6983;align-items:start}
.vragen li svg{width:.82rem;height:.82rem;margin-top:.03rem}
.vragen li.n{color:#0F1D36;font-weight:600}
/* pagina 3 */
.dingen{display:flex;flex-direction:column;gap:.85rem}
.ding{display:grid;grid-template-columns:2.6rem minmax(0,1fr) 16.5rem;gap:1.2rem;align-items:center;padding:1.1rem 1.25rem}
.ding.eerste{background:#0F1D36;color:#F2F4F9;border-color:#0F1D36}
.ding .nr{width:2.6rem;height:2.6rem;border-radius:50%;background:#FFC15C;color:#1C1405;font-family:Archivo;font-weight:800;
 display:flex;align-items:center;justify-content:center;font-size:1.35rem}
.ding h3{font-family:Archivo;font-weight:800;font-size:1.12rem;line-height:1.18;letter-spacing:-.012em;margin-bottom:.3rem}
.ding p{font-size:.84rem;line-height:1.48;color:#24314D}
.ding.eerste p{color:rgba(242,244,249,.86)}
.vb{background:rgba(255,183,64,.17);border-radius:.95rem;padding:.8rem 1rem;font-size:.8rem;line-height:1.45;color:#3B2A0B}
.vb b{display:block;font-family:Archivo;font-weight:800;font-size:.6rem;letter-spacing:.13em;text-transform:uppercase;color:#7E4400;margin-bottom:.22rem}
.ding.eerste .vb{background:rgba(255,255,255,.06);border:1px solid rgba(255,193,92,.38);color:#FFF4DE}
.ding.eerste .vb b{color:#FFC15C}
.ding.zondervb{grid-template-columns:2.6rem minmax(0,1fr)}
.ding.eerste .vul{color:#FFE7B8;background:rgba(255,193,92,.2)}
.meten{display:flex;align-items:center;gap:.85rem;padding:.85rem 1.15rem;background:#FBFCFE;border:1px solid #DDE3EE;border-radius:1.1rem;}
.meten .mi{width:2rem;height:2rem;border-radius:.6rem;background:rgba(255,183,64,.3);display:flex;align-items:center;justify-content:center;flex:none}
.meten .mi svg{width:1.1rem;height:1.1rem}
.meten p{font-size:.82rem;line-height:1.45;color:#24314D}
.meten b{font-family:Archivo;font-weight:800;color:#0F1D36}
.aanpak{margin-top:auto;padding:1.15rem 1.25rem;background:#0F1D36;color:#F2F4F9;border-radius:1.3rem}
.aanpak h3{font-family:Archivo;font-weight:800;font-size:1.25rem;letter-spacing:-.012em;margin-bottom:.8rem}
.aanpak .stappen{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.1rem}
.aanpak .stap{display:grid;grid-template-columns:2rem minmax(0,1fr);gap:.6rem;align-items:start}
.aanpak .snr{width:2rem;height:2rem;border-radius:50%;background:#FFC15C;color:#1C1405;font-family:Archivo;font-weight:800;display:flex;align-items:center;justify-content:center}
.aanpak b{display:block;font-family:Archivo;font-weight:800;font-size:.92rem}
.aanpak p{font-size:.8rem;line-height:1.45;color:rgba(242,244,249,.82);margin-top:.15rem}
.letop{display:flex;gap:.85rem;align-items:flex-start;padding:.85rem 1.15rem;background:#FFF7E8;border:1px solid #F3DDB3;border-radius:1.1rem}
.letop .li{width:2rem;height:2rem;border-radius:.6rem;background:#FCE7BF;display:flex;align-items:center;justify-content:center;flex:none}
.letop .li svg{width:1.1rem;height:1.1rem}
.letop b{font-family:Archivo;font-weight:800;color:#0F1D36;font-size:.86rem}
.letop p{font-size:.8rem;line-height:1.45;color:#3B2A0B;margin-top:.2rem}
.pitch{background:#140F28;color:#F6F3FC;border-radius:1.5rem;padding:1.4rem 1.5rem 1.3rem;position:relative;overflow:hidden;
 display:grid;grid-template-columns:11.5rem minmax(0,1fr);gap:1rem 1.4rem;margin-top:auto}
.pitch>*{position:relative;z-index:1}
.pitch .pfoto{width:100%;height:100%;min-height:0;object-fit:cover;object-position:50% 30%;border-radius:1.05rem;}
.pitch .kicker{color:#FFC15C}
.pitch h2{font-family:Archivo;font-weight:800;font-size:1.55rem;line-height:1.12;letter-spacing:-.018em;margin-top:.3rem}
.pitch .pintro{font-size:.86rem;line-height:1.5;color:rgba(246,243,252,.86);margin-top:.45rem}
.punten4{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem 1rem;margin-top:.85rem}
.p4{display:grid;grid-template-columns:1.9rem minmax(0,1fr);gap:.6rem;align-items:start}
.p4 .ic{width:1.9rem;height:1.9rem;border-radius:.6rem;background:#FFC15C;display:flex;align-items:center;justify-content:center}
.p4 .ic svg{width:1.1rem;height:1.1rem}
.p4 b{display:block;font-family:Archivo;font-weight:800;font-size:.86rem;color:#F6F3FC;line-height:1.25}
.p4 span{display:block;font-size:.76rem;line-height:1.42;color:rgba(246,243,252,.78);margin-top:.12rem}
.feiten{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.85rem}
.feiten span{border:1px solid rgba(246,243,252,.22);border-radius:99px;padding:.2rem .65rem;font-size:.72rem;color:rgba(246,243,252,.88);white-space:nowrap}
.pvoet{grid-column:1 / -1;display:flex;align-items:center;justify-content:space-between;gap:1.2rem;border-top:1px solid rgba(246,243,252,.14);padding-top:.9rem}
.pvoet .prijs b{display:block;font-family:Archivo;font-weight:800;font-size:.95rem;color:#FFC15C}
.pvoet .prijs span{display:block;font-size:.76rem;line-height:1.45;color:rgba(246,243,252,.8);margin-top:.2rem;text-wrap:balance}
.knop{display:inline-flex;align-items:center;gap:.6rem;background:#F2F4F9;color:#0F1D36;border-radius:99px;padding:.35rem .4rem .35rem 1.05rem;font-family:Archivo;font-weight:700;font-size:.9rem;white-space:nowrap;text-decoration:none;flex:none}
.knop i{width:1.9rem;height:1.9rem;border-radius:50%;background:#FFC15C;display:flex;align-items:center;justify-content:center}
.knop i svg{width:1rem;height:1rem}
.knopvak{display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;flex:none}
.knopvak small{font-size:.7rem;color:rgba(246,243,252,.75);white-space:nowrap}
.contact{display:flex;align-items:center;gap:.8rem;font-size:.82rem;color:#24314D}
.contact img{width:2.4rem;height:2.4rem;border-radius:50%;object-fit:cover;object-position:50% 22%}
.contact b{font-family:Archivo;font-weight:800;color:#0F1D36}
.afzender{background:#140F28;color:#F6F3FC;border-radius:1.5rem;padding:1.15rem 1.3rem;display:grid;grid-template-columns:7rem minmax(0,1fr) auto;gap:1.3rem;align-items:center;position:relative;overflow:hidden;margin-top:auto}
.afzender>*{position:relative}
.afzender img{width:7rem;height:8rem;object-fit:cover;object-position:50% 20%;border-radius:1rem}
.afzender h3{font-family:Archivo;font-weight:800;font-size:1.35rem;line-height:1.1}
.afzender p{font-size:.86rem;line-height:1.5;color:rgba(246,243,252,.86);margin-top:.35rem}
.afzender p.wie{font-size:.76rem;color:rgba(246,243,252,.7);margin-top:.5rem}
.afzender p.wie b{color:#F6F3FC}
.voetregel{display:flex;justify-content:space-between;font-size:.7rem;color:#5E6983;font-weight:600}
/* pagina 3 met ruimte (als de afzender naar pagina 4 gaat) */
.ruim .dingen{gap:1.05rem}
.ruim .ding{padding:1.5rem 1.5rem;grid-template-columns:2.9rem minmax(0,1fr) 18rem;gap:1.4rem}
.ruim .ding.zondervb{grid-template-columns:2.9rem minmax(0,1fr)}
.ruim .ding .nr{width:2.9rem;height:2.9rem;font-size:1.5rem}
.ruim .ding h3{font-size:1.3rem;margin-bottom:.4rem}
.ruim .ding p{font-size:.94rem;line-height:1.5}
.ruim .vb{font-size:.9rem;line-height:1.48;padding:.95rem 1.1rem}
.ruim .meten p,.ruim .letop p{font-size:.86rem}
/* persoonlijke regel en nu-en-straks */
.pers{display:flex;gap:.85rem;align-items:center;padding:.1rem .2rem}
.pers img{width:3rem;height:3rem;border-radius:50%;object-fit:cover;object-position:50% 20%;flex:none}
.pers p{font-size:1rem;line-height:1.45;color:#0F1D36;font-weight:500;margin-top:.15rem}
.pers small{display:block;font-size:.74rem;color:#5E6983;margin-top:.15rem;font-weight:600}
.voorna{padding:1rem 1.2rem 1.05rem;display:flex;flex-direction:column;min-height:0}
.telefoons{display:grid;grid-template-columns:repeat(2,minmax(0,11.6rem));justify-content:center;align-content:start;gap:2.4rem;margin:auto 0;padding:1rem 0}
.telefoons figure{display:flex;flex-direction:column;align-items:center;gap:.7rem}
.telefoons figcaption{font-size:.8rem;color:#24314D}
.telefoons figcaption b{font-family:Archivo;font-weight:800}
.tel{width:100%;aspect-ratio:390/844;flex:none;border:.32rem solid #0F1D36;border-radius:1.5rem;overflow:hidden;background:#fff;position:relative}
.tel>img{width:100%;height:100%;object-fit:cover;object-position:50% 0;display:block}
.tel.schets{border-color:#FFC15C;display:flex;flex-direction:column}
.sch-top{height:11%;overflow:hidden;flex:none;border-bottom:1px solid #E3E7EF}
.sch-top img{width:100%;display:block}
.sch-in{flex:1;display:flex;flex-direction:column;padding:.8rem .75rem .7rem;gap:.45rem;min-height:0}
.sch-in h4{font-family:Archivo;font-weight:800;font-size:.86rem;line-height:1.18;letter-spacing:-.01em;color:#0F1D36;text-wrap:balance}
.sch-in p{font-size:.64rem;line-height:1.4;color:#4A5672}
.sch-knop{display:block;width:62%;height:1.25rem;border-radius:99px;background:#FFC15C;flex:none;margin-top:.1rem}
.sch-foto{flex:1;min-height:1.5rem;border-radius:.7rem;background:#F3F5F9;border:1px dashed #C9D0DD;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.15rem;margin-top:.2rem}
.sch-foto svg{width:1.6rem;height:1.6rem}
.sch-foto small{font-size:.56rem;color:#8A94A8}
.waarom{padding-top:.8rem;border-top:1px solid rgba(15,29,54,.09);font-size:.8rem;line-height:1.45;color:#24314D}
.waarom b{font-family:Archivo;font-weight:800;color:#0F1D36}
/* pitch: weken, bewijs, tweede knop */
.pkop{font-family:Archivo;font-weight:800;font-size:.6rem;letter-spacing:.13em;text-transform:uppercase;color:#FFC15C;margin-top:.85rem}
.pkop + .punten4{margin-top:.45rem}
.p4 .ic.num{font-family:Archivo;font-weight:800;font-size:.95rem;color:#1C1405}
.pbewijs{margin-top:.55rem;font-size:.8rem;line-height:1.45;color:#FFE7B8;border-left:.18rem solid #FFC15C;padding-left:.6rem}
.preactie{margin-top:.6rem;font-size:.74rem;line-height:1.4;color:rgba(246,243,252,.82);font-style:italic}
.preactie span{display:block;font-style:normal;color:rgba(246,243,252,.6);margin-top:.1rem}
.knoppen{display:flex;flex-direction:column;gap:.45rem;align-items:stretch}
.knoppen .knop{justify-content:space-between}
.knoppen .knop.tweede{justify-content:center}
.knop.tweede{background:transparent;color:#F6F3FC;border:1px solid rgba(246,243,252,.45);padding:.62rem 1rem;font-weight:600;font-size:.82rem}
/* pagina 4 */
.tweekol{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);gap:1rem;align-items:stretch}
.blok{padding:1.15rem 1.3rem 1.2rem;display:flex;flex-direction:column}
.blok h3{font-family:Archivo;font-weight:800;font-size:1.25rem;line-height:1.15;letter-spacing:-.012em;margin:.3rem 0 .3rem}
.blok .intro{font-size:.8rem;line-height:1.45;color:#4A5672;margin-bottom:.35rem}
.variant{display:grid;grid-template-columns:1.7rem minmax(0,1fr);gap:.7rem;padding:.75rem 0;border-top:1px solid rgba(15,29,54,.09)}
.variant .vn{width:1.7rem;height:1.7rem;border-radius:50%;background:rgba(15,29,54,.07);color:#24314D;font-family:Archivo;font-weight:800;font-size:.85rem;display:flex;align-items:center;justify-content:center}
.variant.aan .vn{background:#FFC15C;color:#1C1405}
.variant p{font-size:.9rem;line-height:1.45;color:#0F1D36;font-weight:500}
.variant small{display:block;font-size:.74rem;line-height:1.4;color:#5E6983;margin-top:.3rem}
.tag{display:inline-block;font-family:Archivo;font-weight:800;font-size:.58rem;letter-spacing:.12em;text-transform:uppercase;color:#7E4400;background:rgba(255,183,64,.3);border-radius:99px;padding:.12rem .5rem;margin-bottom:.3rem}
.blok.donker{background:#0F1D36;border-color:#0F1D36;color:#F2F4F9}
.blok.donker .kicker{color:#FFC15C}
.blok.donker .intro{color:rgba(242,244,249,.78)}
.blok.donker .variant{border-top-color:rgba(242,244,249,.16)}
.blok.donker .variant .vn{background:rgba(242,244,249,.14);color:#F2F4F9}
.blok.donker .variant.aan .vn{background:#FFC15C;color:#1C1405}
.blok.donker .variant p{color:#F2F4F9;font-family:Archivo;font-weight:700;font-size:.98rem;line-height:1.36;letter-spacing:-.005em}
.blok.donker .variant small{color:rgba(242,244,249,.72)}
.blok.donker .tag{color:#1C1405;background:#FFC15C}
.blok .slotregel{margin-top:auto;padding-top:.7rem;border-top:1px solid rgba(15,29,54,.09);font-size:.76rem;line-height:1.42;color:#4A5672}
.blok.donker .slotregel{border-top-color:rgba(242,244,249,.16);color:rgba(242,244,249,.78)}
.weetniet{display:flex;gap:.85rem;align-items:flex-start;padding:.9rem 1.15rem;background:#FBFCFE;border:1px solid #DDE3EE;border-radius:1.1rem}
.weetniet .wi{width:2rem;height:2rem;border-radius:.6rem;background:rgba(15,29,54,.07);display:flex;align-items:center;justify-content:center;flex:none}
.weetniet .wi svg{width:1.1rem;height:1.1rem}
.weetniet b{font-family:Archivo;font-weight:800;color:#0F1D36;font-size:.86rem}
.weetniet p{font-size:.78rem;line-height:1.45;color:#24314D;margin-top:.2rem}
"""

# Elke maat in rem hangt aan --u van de pagina zelf, zodat een volle pagina kan krimpen zonder de andere mee te nemen.
CSS = re.sub(r"(?<![\w.])(-?\d*\.?\d+)rem", r"calc(\1*var(--u))", CSS)

PASKLAAR = """
<script>
(function(){
  var KLEINST=7.6;
  [].slice.call(document.querySelectorAll('.blad.vast')).forEach(function(b){
    function past(){
      if(b.scrollHeight>b.clientHeight+1) return false;
      var r=b.getBoundingClientRect(), pb=parseFloat(getComputedStyle(b).paddingBottom)||0, grens=r.bottom-pb+1;
      var els=b.querySelectorAll('.duo > *, .duo > * > *, .telefoons, .telefoons figure, .sch-in, .raster > *, .steen > *, .dingen > *, .tweekol > *, .weetniet, .pitch, .aanpak, .afzender, .voet, .voetregel');
      for(var i=0;i<els.length;i++){var q=els[i].getBoundingClientRect(); if(q.height&&q.bottom>grens) return false;
        if(getComputedStyle(els[i]).overflowY==='visible'&&els[i].scrollHeight>els[i].clientHeight+1) return false;
        var par=els[i].parentElement.getBoundingClientRect(); if(q.height&&q.bottom>par.bottom+1) return false;}
      return true;}
    var u=10;
    while(!past()&&u>KLEINST){u=Math.round((u-0.1)*10)/10;b.style.setProperty('--u',u+'pt')}
    b.setAttribute('data-u',u);b.setAttribute('data-past',past()?'ja':'nee');
  });
})();
</script>
"""


def bouw_html(tekst, afzender=None, afzender_basis=".", kort=False, meldingen=None, bron_map="."):
    meldingen = meldingen if meldingen is not None else []
    d = lees(tekst)
    titel = re.sub(r"(?<=\w)'(?=\w)", "\u2019", d["titel"] or "Praktijkscan")
    titel_kort = titel if len(titel) <= 44 else titel[:42].rstrip() + "\u2026"
    meta = d["meta"]
    zakelijk = meta.get("doelgroep", "").lower().startswith(("zak", "b2b", "organ"))
    dg = "Z" if zakelijk else "P"
    if "gescoord" not in meta:
        meldingen.append("De regel 'Gescoord:' ontbreekt; zeg welk aanbod je scoorde.")
    if woorden(d["titel"] or "") > 4:
        meldingen.append(f"De naam in de titel is {woorden(d['titel'])} woorden; houd het bij de naam van de praktijk (hoogstens vier woorden), anders loopt de kop over vier regels.")
    if "doelgroep" not in meta:
        meldingen.append("De regel 'Doelgroep: particulier' of 'Doelgroep: zakelijk' ontbreekt; ik reken met particulier.")
    stenen = lees_bouwstenen(sectie(d, "bouwstenen"), meldingen)
    eenzin = " ".join(x.strip() for x in sectie(d, "in één zin", "in een zin") if x.strip())
    drie = lees_drie(sectie(d, "de drie dingen", "drie dingen"))
    conc = lees_concurrentie(sectie(d, "concurrentie"))
    werkt = [re.sub(r"^\s*[-*]\s+", "", r).strip() for r in sectie(d, "wat al werkt") if re.match(r"^\s*[-*]\s+", r)][:3]
    letop = [re.sub(r"^\s*[-*]\s+", "", r).strip() for r in sectie(d, "let op") if re.match(r"^\s*[-*]\s+", r)][:3]
    datum, website, agenda = meta.get("datum", ""), meta.get("website", ""), meta.get("agenda", "")

    # scores
    tot_ja = tot_get = 0
    per_groep = {g[0]: [0, 0] for g in GROEPEN}
    data = {g[0]: [] for g in GROEPEN}
    for g, naam, teksten in BOUWSTENEN:
        uitleg, labels = teksten[dg]
        info = stenen.get(naam, {"tekens": [], "zag": "Niet gescoord."})
        if naam not in stenen:
            meldingen.append(f"{naam}: staat niet in de tabel Bouwstenen en telt als niet gecontroleerd.")
        elif len(info["tekens"]) != len(labels):
            meldingen.append(f"{naam}: {len(info['tekens'])} antwoorden gevonden, verwacht {len(labels)} "
                             f"({'zakelijk' if zakelijk else 'particulier'}). Te veel vervalt, te weinig telt als niet gecontroleerd.")
        if naam in stenen and woorden(info["zag"]) > 19:
            meldingen.append(f"{naam}: 'Wat ik zag' is {woorden(info['zag'])} woorden; de grens is 15.")
        checks = (info["tekens"] + ["?"] * len(labels))[:len(labels)]
        ja = checks.count("j")
        get = sum(1 for c in checks if c in "jn")
        st = stand(ja, get)
        tot_ja += ja; tot_get += get
        per_groep[g][0] += ja; per_groep[g][1] += get
        data[g].append((naam, uitleg, info["zag"], ja, get, st, checks, labels))
    pct = round(100 * tot_ja / tot_get) if tot_get else 0
    band = next(b for b in BANDEN if pct >= b[0])

    def gpct(g):
        ja, get = per_groep[g]
        return round(100 * ja / get) if get else 0

    def label(ja, get, st):
        if st == "grijs":
            return '<span class="label"><span class="stip grijs"></span>Niet gecontroleerd</span>'
        return f'<span class="label"><i class="stip {st}"></i><b>{ja} van {get}</b>{STANDEN[st].lower()}</span>'

    legenda = ('<div class="legenda"><span><i class="stip groen"></i>Staat goed</span><span><i class="stip oranje"></i>Kan beter</span>'
               '<span><i class="stip rood"></i>Pak dit aan</span><span><i class="stip open"></i>Niet gecontroleerd</span></div>')
    bron = '<div class="bron">Methode: de Praktijkscan van Jens Kemna<br>Praktijkwerkbank, praktijkwerkbank.nl</div>'
    # de vierde pagina: plek, kop en wat de scan niet weet
    eigen = sectie(d, "je plek")
    varianten, plek_aanrader = lees_plek(eigen, vrij=True) if eigen else lees_plek(onder(d, "de plek"))
    kopvar, kop_aanrader, kop_aanname, kop_i = lees_koppen(onder(d, "suggesties voor de kop"))
    voorbehoud = lees_voorbehoud(onder(d, "wat je niet van mij moet aannemen"))
    vier = not kort and bool(varianten or kopvar)
    n_pag = 4 if vier else 3
    nr_plek, nr_stenen = 3, n_pag
    persoonlijk = " ".join(x.strip() for x in sectie(d, "persoonlijk") if x.strip())
    scherm = foto_src(meta.get("schermafbeelding"), bron_map)
    if meta.get("schermafbeelding") and not scherm:
        meldingen.append(f"De schermafbeelding '{meta['schermafbeelding']}' is niet gevonden naast het markdown-bestand.")
    beste_kop = kopvar[kop_i if kop_i is not None else 0] if kopvar else ""
    voorna = bool(scherm and beste_kop)
    if not scherm:
        meldingen.append("Geen regel 'Schermafbeelding:' met de homepage op telefoonformaat; pagina 1 toont dan de grafiek in plaats van nu en straks.")
    if afzender and not persoonlijk:
        meldingen.append("Geen persoonlijke regel (## Persoonlijk): één of twee zinnen van de afzender over wat opviel.")
    if "[VOORSTEL" in persoonlijk.upper():
        meldingen.append("De persoonlijke regel is nog een voorstel; laat de afzender hem in eigen woorden zetten en haal [VOORSTEL] weg.")

    # controle van het bewijs per antwoord
    bewijs = lees_bewijs(onder(d, "bewijs"))
    if not bewijs:
        meldingen.append("Geen bewijs per antwoord gevonden (### Bewijs in de onderbouwing): de antwoorden zijn niet na te lopen.")
    else:
        zonder, anders = [], []
        for g in data:
            for naam, _, _, _, _, _, ch, labels in data[g]:
                for letter, c in zip("abcde", ch):
                    b = bewijs.get(naam, {}).get(letter)
                    if c in "jn" and (b is None or not b[1]):
                        zonder.append(f"{naam} {letter}")
                    elif b is not None and b[0] != c:
                        anders.append(f"{naam} {letter} (tabel {c}, bewijs {b[0]})")
                    elif c == "n" and (naam, letter) in UITSLUIT and not re.search(r"[\"\u201c\u201d\u2018\u2019']", b[1]):
                        meldingen.append(f"{naam} {letter} is een uitsluitvraag en staat op nee zonder citaat van de overtreding; zonder citaat is het ja.")
        if anders:
            meldingen.append("Bewijs en tabel spreken elkaar tegen bij: " + "; ".join(anders) + ".")
        if zonder:
            meldingen.append(f"Bewijs ontbreekt bij {len(zonder)} antwoorden: " + ", ".join(zonder[:8]) + (" en meer." if len(zonder) > 8 else "."))

    # controle van de uitslag
    if not eenzin:
        meldingen.append("De sectie 'In één zin' ontbreekt.")
    elif woorden(eenzin) > 52:
        meldingen.append(f"'In één zin' is {woorden(eenzin)} woorden; de grens is 45.")
    if len(drie) != 3:
        meldingen.append(f"'De drie dingen die het meest opleveren' heeft {len(drie)} genummerde punten in plaats van 3.")
    for n, it in enumerate(drie, 1):
        if not it["kop"]:
            meldingen.append(f"Ding {n} heeft geen vetgedrukte titel (**Titel.** en dan de uitleg).")
        if woorden(it["rest"]) > 60:
            meldingen.append(f"Ding {n}: de uitleg is {woorden(it['rest'])} woorden; de grens is 50.")
        if woorden(" ".join(it["voorbeeld"])) > 36:
            meldingen.append(f"Ding {n}: het voorbeeld is {woorden(' '.join(it['voorbeeld']))} woorden; de grens is 30.")
    if not werkt:
        meldingen.append("De sectie 'Wat al werkt' ontbreekt of heeft geen opsommingstekens.")
    for veld in ("gelezen", "iedereen zegt", "niemand zegt", "leer van"):
        if veld not in conc:
            meldingen.append(f"Concurrentie: de regel '{veld.capitalize()}:' ontbreekt.")
    if not kort and not varianten:
        meldingen.append("Geen voorstel voor de plek gevonden (opsomming onder 'Voorstel voor de plek:' in ### De plek).")
    if not kort and not kopvar:
        meldingen.append("Geen kopvarianten gevonden (regels met > onder ### Suggesties voor de kop).")

    # ---------- pagina 1: overzicht ----------
    doelgroep_pil = ('<span class="pil glas">Doelgroep: <b>zakelijk</b>, de koper is een organisatie</span>' if zakelijk
                     else '<span class="pil glas">Doelgroep: <b>particulier</b>, de cliënt betaalt zelf</span>')
    agenda_kort = re.split(r"[,.;]", agenda)[0].strip() if agenda else ""
    agenda_pil = f'<span class="pil glas">Agenda: <b>{inline(agenda_kort)}</b></span>' if agenda_kort else ""

    grafiek = ""
    for g, gnaam, _ in GROEPEN:
        rijen = "".join(
            f'<div class="grij"><span class="gnaam">{html.escape(n)}</span>{blokjes(ch, st)}'
            f'<span class="gwaarde"><i class="stip {st}"></i>{"<b>%d</b> van %d" % (ja, get) if st != "grijs" else "onbekend"}</span></div>'
            for n, _, _, ja, get, st, ch, _ in data[g])
        grafiek += (f'<div class="ggroep"><div class="gkop"><span class="letter">{g}</span><b>{gnaam}</b>'
                    f'<span class="gpct">{gpct(g)}% ja</span></div>{rijen}</div>')

    werkt_html = ""
    if werkt:
        werkt_html = ('<section class="werkt glas"><h3>Wat al werkt</h3>'
                      + "".join(f'<div class="punt">{ICOON["j"]}<span>{inline(w)}</span></div>' for w in werkt)
                      + "</section>")
    conc_html = ""
    if conc:
        gl = conc.get("gelezen", "")
        gelezen = [x.strip() for x in gl.split(";" if ";" in gl else ",") if x.strip()]
        conc_html = f"""<section class="conc glas"><h3>Jij tussen de concurrenten</h3>
<div class="gelezen">{len(gelezen)} zelf gelezen: {inline(', '.join(gelezen))}</div>
<div class="vak"><span class="kicker">Wat iedereen zegt</span>{"".join(f'<span class="chip">{inline(x.strip())}</span>' for x in conc.get('iedereen zegt', '').split(';') if x.strip())}</div>
<div class="vak ruimte"><span class="kicker">Wat niemand zegt: jouw ruimte</span>{ruimte(conc.get('niemand zegt', ''))}</div>
<div class="vak"><span class="kicker">Leer van</span><div class="leer">{inline(conc.get('leer van', ''))}</div></div></section>"""

    def tegel(naam, richting):
        pijl = ('<svg viewBox="0 0 24 24"><path d="M12 19V6M6 12l6-6 6 6" fill="none" stroke="#1C1405" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                if richting == "op" else
                '<svg viewBox="0 0 24 24"><path d="M12 5v13M6 12l6 6 6-6" fill="none" stroke="#F2F4F9" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
        return f'<div class="tegel {richting}"><span class="tp">{pijl}</span><b>{naam}</b><small>{"groter is beter" if richting == "op" else "kleiner is beter"}</small></div>'

    uitlegkaart = ('<section class="uitlegkaart glas"><span class="kicker">Waar de score op let</span>'
                   '<h3>Hoe waardevol voelt je aanbod?</h3>'
                   '<div class="tegels">' + tegel("Droomresultaat", "op") + tegel("Geloof dat het lukt", "op")
                   + tegel("Wachttijd", "neer") + tegel("Moeite", "neer") + '</div>'
                   '<p>Dat is de waardeformule van Alex Hormozi, in gewone woorden. Groep <b>A</b> meet die vier. '
                   'Groep <b>B</b> kijkt of je aanbod onvergelijkbaar is: een garantie, een pakket met een naam, een prijs die klopt en een reden om nu te beginnen. '
                   'Groep <b>C</b> kijkt of de juiste mensen je vinden en de stap zetten.</p></section>')

    pers_html = ""
    if persoonlijk:
        pt = re.sub(r"`?\[VOORSTEL[^\]]*\]`?\s*", "", persoonlijk).strip()
        foto = f'<img src="{afzender["foto_src"]}" alt="">' if afzender and afzender.get("foto_src") else ""
        wie = html.escape(afzender.get("naam", "")) if afzender else ""
        pers_html = (f'<section class="pers">{foto}<div><span class="kicker">Wat mij opviel</span><p>{inline(pt)}</p>'
                     + (f'<small>{wie}</small>' if wie else "") + "</div></section>")
    if voorna:
        delen = re.split(r"(?<=[.?!])\s+", beste_kop, maxsplit=1)
        k1, k2 = delen[0], (delen[1] if len(delen) > 1 else "")
        reden = re.sub(r"^(de\s+)?(eerste|tweede|derde|[123])\s*[,:]?\s*", "", kop_aanrader, flags=re.I).strip()
        reden = re.sub(r"^want\s+(die|deze|hij)\s+", "Hij ", reden, flags=re.I)   # na 'want' staat al een hoofdzin
        reden = re.sub(r"^want\s+", "", reden, flags=re.I)
        if reden:
            reden = reden[:1].upper() + reden[1:] + ("" if reden[-1] in ".!?" else ".")
        waarom_html = ('<div class="waarom"><b>Waarom deze kop?</b> ' + (inline(reden) + " " if reden else "")
                       + f'Op pagina {nr_plek if vier else 2} staan nog {"twee" if len(kopvar) == 3 else "meer"} varianten.</div>') if len(kopvar) > 1 or reden else ""
        links_html = f"""<div class="voorna glas"><div class="ghd"><h2>Je eerste scherm, nu en straks</h2>
<span class="schaal">Links je homepage op een telefoon, zonder scrollen. Rechts een schets met de kop die ik zou aanraden; je eigen foto en kleuren blijven.</span></div>
<div class="telefoons">
<figure><div class="tel"><img src="{scherm}" alt=""></div><figcaption><b>Nu</b></figcaption></figure>
<figure><div class="tel schets"><div class="sch-top"><img src="{scherm}" alt=""></div><div class="sch-in"><h4>{inline(k1)}</h4>{f'<p>{inline(k2)}</p>' if k2 else ''}<span class="sch-knop"></span><div class="sch-foto"><svg viewBox="0 0 24 24" fill="none" stroke="#A9B2C4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20c.8-3.6 3.8-5.5 7.5-5.5s6.7 1.9 7.5 5.5"/></svg><small>jouw foto</small></div></div></div><figcaption><b>Zo zou het kunnen</b></figcaption></figure>
</div>{waarom_html}</div>"""
        rechts_html = f'{werkt_html}{conc_html}'
        voet1 = (f'De score gaat over wat je site laat zien, niet over hoe goed je bent in je vak. Pagina 2: de drie dingen die het meest opleveren.'
                 f'{" Pagina 3: je plek en je kop." if vier else ""} Pagina {nr_stenen}: de twaalf bouwstenen, vraag voor vraag.')
    else:
        links_html = f"""<div class="grafiek glas"><div class="ghd"><h2>Je scan in één beeld</h2><span class="schaal">Per bouwsteen: hoeveel vragen een ja kregen. De score gaat over wat je site laat zien, niet over hoe goed je bent in je vak.</span></div>
      <div class="ggroepen">{grafiek}</div></div>"""
        rechts_html = f'{werkt_html}{conc_html}{uitlegkaart}'
        voet1 = (f'{legenda}Pagina 2: de drie dingen die het meest opleveren.{" Pagina 3: je plek en je kop." if vier else ""} '
                 f'Pagina {nr_stenen}: de twaalf bouwstenen, vraag voor vraag.')

    blad1 = f"""
<div class="blad vast">
  {kopbalk(f'<span class="pil amber">Praktijkscan</span><span>{html.escape(datum)}</span><span>Pagina 1 van {n_pag}</span>')}
  <section class="held">
    <div class="links"><span class="kicker">Het overzicht</span><h1>{html.escape(titel)}</h1>
      <div class="url">{html.escape(website)}</div><div class="pillen">{doelgroep_pil}{agenda_pil}</div></div>
    <div class="score"><span class="kicker">Totaalscore</span>
      <div class="scorerij"><div class="metervak">{meter(pct)}<div class="getal">{pct}<small>/100</small></div></div>
      <div class="band">{band[1]}</div></div>
      <div class="bandsub">Van de <b>{tot_get}</b> vragen die ik kon controleren, kregen er al <b>{tot_ja}</b> een ja. {band[2]}</div>
    </div>
  </section>
  {pers_html}
  {f'<section class="eenzin glas"><span class="kicker">In één zin</span><p>{inline(eenzin)}</p></section>' if eenzin else ''}
  <section class="duo">
    {links_html}
    <div class="rechts">{rechts_html}</div>
  </section>
  <div class="voet"><div>{voet1}</div>{bron}</div>
</div>"""

    # ---------- pagina 2: de twaalf bouwstenen ----------
    koppen = ""
    for g, gnaam, vraag in GROEPEN:
        koppen += (f'<div class="kolomkop"><div class="rij1"><span class="letter">{g}</span><h3>{gnaam}</h3>'
                   f'<span class="gp">{gpct(g)}%</span></div><div class="vraag">{vraag}</div></div>')
    kaarten = ""
    for i in range(4):
        for g, _, _ in GROEPEN:
            naam, uitleg, zag, ja, get, st, ch, labels = data[g][i]
            vragen = "".join(f'<li class="{"open" if c == "?" else c}">{ICOON[c]}<span>{inline(l)}</span></li>' for c, l in zip(ch, labels))
            kaarten += f"""<div class="steen glas"><div class="naam">{html.escape(naam)}</div>
<div class="uitleg">{html.escape(uitleg)}</div><div class="stand">{blokjes(ch, st)}{label(ja, get, st)}</div>
<div class="zag">{inline(zag)}</div><ul class="vragen">{vragen}</ul></div>"""

    blad2 = f"""
<div class="blad vast">
  {kopbalk(f'<span class="pil amber">Bijlage</span><span>{html.escape(titel_kort)}</span><span>Pagina {nr_stenen} van {n_pag}</span>')}
  <section class="paginakop"><span class="kicker">Bijlage: de twaalf bouwstenen</span><h2>Waar het staat, en waar je kunt <span>winnen</span></h2>
  <p>Per bouwsteen: wat ik zag, en welke van de vijf vragen een ja of een nee kregen{' (zakelijk heeft snelheid er vier)' if zakelijk else ''}.{(' Gescoord: ' + inline(meta['gescoord'].rstrip('.')) + '.') if meta.get('gescoord') else ''}</p></section>
  <section class="raster">{koppen}{kaarten}</section>
  <div class="voet"><div>{legenda}</div>{bron}</div>
</div>"""

    # ---------- pagina 3: wat nu ----------
    dingen = ""
    for n, it in enumerate(drie, 1):
        vb = ""
        if it["voorbeeld"]:
            v = " ".join(it["voorbeeld"])
            verzonnen = "VOORBEELD" in v
            v = re.sub(r"`?\[VOORBEELD[^\]]*\]`?\s*", "", v).strip()
            vb = f'<div class="vb"><b>{"Voorbeeld" if verzonnen else "Uit je eigen tekst"}</b>{inline(v)}</div>'
        cls = "ding glas" + (" eerste" if n == 1 else "") + ("" if vb else " zondervb")
        dingen += f'<div class="{cls}"><span class="nr">{n}</span><div><h3>{inline(it["kop"])}</h3><p>{inline(it["rest"])}</p></div>{vb}</div>'

    meten = ('<section class="meten"><span class="mi"><svg viewBox="0 0 24 24"><path d="M4 19V9m6 10V5m6 14v-7m4 7H3" fill="none" '
             'stroke="#1C1405" stroke-width="2.2" stroke-linecap="round"/></svg></span><p><b>Zo weet je of het werkt.</b> '
             'Tel per maand je aanvragen en vraag iedereen hoe hij je vond. Verander één ding tegelijk, en kijk na 30, 60 en 90 dagen terug.</p></section>')

    letop_html = ""
    if letop:
        letop_html = ('<section class="letop"><span class="li"><svg viewBox="0 0 24 24" fill="none" stroke="#7E4400" stroke-width="2.2" '
                      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9.5 17h-19z"/><path d="M12 10v4.5M12 17.6v.1"/></svg></span>'
                      '<div><b>Let op.</b>' + "".join(f"<p>{inline(x)}</p>" for x in letop) + "</div></section>")

    slot = ""
    if afzender and afzender.get("pitch"):
        p = dict(afzender["pitch"])
        # perioden: velden die tot en met een datum gelden (bijvoorbeeld een early-birdprijs); na de laatste datum geldt "daarna"
        vandaag = datetime.date.today().isoformat()
        perioden = sorted(p.get("perioden", []), key=lambda x: x.get("tot", ""))
        geldig = next((x for x in perioden if vandaag <= x.get("tot", "")), None)
        if geldig:
            p.update({k: v for k, v in geldig.items() if k != "tot"})
        elif perioden and p.get("daarna"):
            p.update(p["daarna"])
        pf = foto_src(p.get("foto"), afzender_basis) or afzender.get("foto_src", "")
        punten = "".join(f'<div class="p4"><span class="ic">{icoon(x.get("icoon", ""))}</span><div><b>{html.escape(x.get("titel", ""))}</b>'
                         f'<span>{html.escape(x.get("tekst", ""))}</span></div></div>' for x in p.get("punten", [])[:4])
        weken = {int(w.get("nr", 0)): w for w in p.get("weken", [])}
        gekoppeld = [(n, it, weken[it["week"]]) for n, it in enumerate(drie, 1) if it.get("week") in weken]
        puntenkop = ""
        if gekoppeld:
            puntenkop = f'<div class="pkop">{html.escape(p.get("wekenkop", "Jouw drie dingen in het programma"))}</div>'
            punten = "".join(f'<div class="p4"><span class="ic num">{n}</span><div><b>{inline(it["kop"])}</b>'
                             f'<span>Week {w.get("nr")}{", " + html.escape(w["datum"]) if w.get("datum") else ""}: {html.escape(w.get("titel", ""))}</span></div></div>'
                             for n, it, w in gekoppeld)
            if p.get("wekenslot"):
                x = p["wekenslot"]
                punten += (f'<div class="p4"><span class="ic">{icoon(x.get("icoon", "skills"))}</span><div><b>{html.escape(x.get("titel", ""))}</b>'
                           f'<span>{html.escape(x.get("tekst", ""))}</span></div></div>')
        bewijs_html = f'<p class="pbewijs">{inline(p["bewijs"])}</p>' if p.get("bewijs") else ""
        reactie_html = ""
        if p.get("reactie"):
            r = p["reactie"]
            reactie_html = f'<p class="preactie">\u201c{html.escape(r.get("tekst", ""))}\u201d <span>{html.escape(r.get("wie", ""))}</span></p>'
        knop2 = ""
        if p.get("knop2") and p.get("link2"):
            knop2 = f'<a class="knop tweede" href="{html.escape(p["link2"], quote=True)}">{html.escape(p["knop2"])}</a>'
        feiten = "".join(f"<span>{html.escape(f)}</span>" for f in p.get("feiten", []))
        link = html.escape(p.get("link", ""), quote=True)
        slot = f"""<section class="pitch">
  {f'<img class="pfoto" src="{pf}" alt="">' if pf else '<div></div>'}
  <div><span class="kicker">{html.escape(p.get('kicker', ''))}</span><h2>{html.escape(p.get('kop', ''))}</h2>
    <p class="pintro">{html.escape(p.get('tekst', ''))}</p>{bewijs_html}{puntenkop}<div class="punten4">{punten}</div><div class="feiten">{feiten}</div>{reactie_html}</div>
  <div class="pvoet"><div class="prijs"><b>{html.escape(p.get('prijs', ''))}</b><span>{html.escape(p.get('garantie', ''))}</span></div>
    <div class="knopvak"><div class="knoppen"><a class="knop" href="{link}">{html.escape(p.get('knop', 'Bekijk het programma'))}<i>{PIJL}</i></a>{knop2}</div>
    <small>{html.escape(p['klein']) if p.get('klein') else html.escape(p.get('linktekst', '')) + ((' of mail ' + html.escape(afzender['mail'])) if afzender.get('mail') else '')}</small></div></div>
</section>"""
    elif afzender:
        foto = f'<img src="{afzender["foto_src"]}" alt="">' if afzender.get("foto_src") else ""
        mail = html.escape(afzender.get("mail", ""))
        slot = f"""<section class="afzender"{'' if foto else ' style="grid-template-columns:1fr auto"'}>{foto}
  <div><h3>{html.escape(afzender.get('kop', 'Heb je hier iets aan?'))}</h3><p>{html.escape(afzender.get('tekst', ''))}</p>
  <p class="wie"><b>{html.escape(afzender.get('naam', ''))}</b>{(', ' + html.escape(afzender['rol'])) if afzender.get('rol') else ''}</p></div>
  {f'<a class="knop" href="mailto:{mail}">{mail}<i>{PIJL}</i></a>' if mail else ''}</section>"""

    aanpak = ""
    if not slot or vier:
        stappen = [("1", "Kies de eerste", "Begin bij nummer 1 en plan er een vaste middag voor. Eén ding tegelijk, de rest later."),
                   ("2", "Maak het van jou", "Schrijf de voorbeelden in je eigen woorden. Lees ze hardop en vervang wat niet van jou is."),
                   ("3", "Kijk terug", "Meet een maand na de wijziging, en scan je site na drie maanden opnieuw.")]
        aanpak = ('<section class="aanpak"><h3>Zo pak je het aan</h3><div class="stappen">'
                  + "".join(f'<div class="stap"><span class="snr">{n}</span><div><b>{t}</b><p>{x}</p></div></div>' for n, t, x in stappen)
                  + '</div></section>')
    slot3 = aanpak if (vier or not slot) else slot

    blad4 = ""
    if vier:
        def varlijst(items, aan_i=None):
            uit = ""
            for n, v in enumerate(items, 1):
                aan = v["aan"] or (aan_i is not None and aan_i == n - 1)
                uit += (f'<div class="variant{" aan" if aan else ""}"><span class="vn">{n}</span><div>'
                        + ('<span class="tag">Aanrader</span>' if aan else "")
                        + f'<p>{inline(v["tekst"])}</p>' + (f'<small>{inline(v["noot"])}</small>' if v["noot"] else "") + "</div></div>")
            return uit

        plek_blok = ""
        if varianten:
            slotr = (f'<div class="slotregel"><b>Aanrader:</b> {inline(plek_aanrader)}</div>' if plek_aanrader
                     else '<div class="slotregel">De keuze is aan jou. De plek is wat je vooraan zet, niet wat je weigert.</div>')
            plek_blok = ('<section class="blok glas"><span class="kicker">Je plek</span><h3>Voor wie je er bent, in één zin</h3>'
                         '<div class="intro">Zo zou je in één zin kunnen zeggen voor wie je er bent en waarmee.</div>'
                         + varlijst(varianten) + slotr + "</section>")
        kop_blok = ""
        if kopvar:
            herkomst = ("Dit zijn aannames, gebouwd op wat er nu op je site staat. Leg ze naast wat cliënten je letterlijk schreven."
                        if kop_aanname else "Lees ze hardop en vervang elk woord dat niet van jou is.")
            slotr = f'<div class="slotregel">{("<b>Aanrader:</b> " + inline(kop_aanrader) + " ") if kop_aanrader else ""}{herkomst}</div>'
            kop_blok = ('<section class="blok glas donker"><span class="kicker">Je kop</span><h3>Zo zou je kop kunnen luiden</h3>'
                        '<div class="intro">Voorbeelden voor de eerste regels van je homepage, elk met een andere ingang.</div>'
                        + varlijst([{"tekst": k, "noot": "", "aan": False} for k in kopvar], kop_i) + slotr + "</section>")
        weet = ""
        if voorbehoud:
            weet = ('<section class="weetniet"><span class="wi"><svg viewBox="0 0 24 24" fill="none" stroke="#24314D" stroke-width="2.1" '
                    'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.1"/></svg></span>'
                    '<div><b>Wat deze scan niet weet.</b>' + "".join(f"<p>{inline(x)}</p>" for x in voorbehoud) + "</div></section>")
        enkel = ' style="grid-template-columns:minmax(0,1fr)"' if not (plek_blok and kop_blok) else ""
        blad4 = f"""
<div class="blad vast">
  {kopbalk(f'<span class="pil amber">Plek en kop</span><span>{html.escape(titel_kort)}</span><span>Pagina {nr_plek} van {n_pag}</span>')}
  <section class="paginakop"><span class="kicker">Plek en kop</span><h2>Waar je staat, en hoe je het <span>zegt</span></h2>
  <p>Dit zijn voorstellen, geen eindtekst. Jij kent je cliënten; kies wat klopt en schrijf het in je eigen woorden.</p></section>
  <section class="tweekol"{enkel}>{plek_blok}{kop_blok}</section>
  {weet}
  {slot}
  <div class="voetregel"{'' if slot else ' style="margin-top:auto"'}><span>Methode: de Praktijkscan van Jens Kemna, Praktijkwerkbank (praktijkwerkbank.nl)</span><span>{html.escape(website)}, {html.escape(datum)}</span></div>
</div>"""

    blad3 = f"""
<div class="blad vast{' ruim' if vier else ''}">
  {kopbalk(f'<span class="pil amber">Wat nu</span><span>{html.escape(titel_kort)}</span><span>Pagina 2 van {n_pag}</span>')}
  <section class="paginakop"><span class="kicker">Wat nu</span><h2>De drie dingen die het <span>meest opleveren</span></h2>
  <p>Begin bij de eerste en doe er één tegelijk. De voorbeelden zijn suggesties: maak ze in je eigen woorden.</p></section>
  <section class="dingen">{dingen}</section>
  {meten}
  {letop_html}
  {slot3}
  <div class="voetregel"><span>Methode: de Praktijkscan van Jens Kemna, Praktijkwerkbank (praktijkwerkbank.nl)</span><span>{html.escape(website)}, {html.escape(datum)}</span></div>
</div>"""

    return f"""<!doctype html><html lang="nl"><head><meta charset="utf-8">
<title>Praktijkscan {html.escape(titel)}</title>
<style>{font_face()}{CSS}</style></head><body>
{blad1}{blad3}{blad4}{blad2}
{PASKLAAR}
</body></html>"""


# ---------- pdf maken ----------

def vind_chrome():
    kandidaten = [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        shutil.which("google-chrome"), shutil.which("google-chrome-stable"), shutil.which("chromium"),
        shutil.which("chromium-browser"), shutil.which("chrome"), shutil.which("brave"), shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for k in kandidaten:
        if k and os.path.exists(k):
            return k
    return None


def maak_pdf(html_pad, pdf_pad):
    """Geeft (gelukt, foutmelding, paginamaten). Paginamaten: per pagina (lettergrootte in punten, past ja of nee)."""
    chrome = vind_chrome()
    if not chrome:
        return False, "Geen Chrome, Chromium, Brave of Edge gevonden.", []
    uri = Path(html_pad).resolve().as_uri()
    maten = []
    with tempfile.TemporaryDirectory() as profiel:
        basis = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                 f"--user-data-dir={profiel}", "--virtual-time-budget=5000"]
        try:
            dom = subprocess.run(basis + ["--dump-dom", uri], capture_output=True, timeout=60).stdout.decode("utf-8", "ignore")
            maten = [(float(u), p == "ja") for u, p in re.findall(r'data-u="([\d.]+)" data-past="(ja|nee)"', dom)]
        except (subprocess.SubprocessError, OSError, ValueError):
            maten = []
        cmd = basis + ["--no-pdf-header-footer", f"--print-to-pdf={pdf_pad}", "--run-all-compositor-stages-before-draw", uri]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except subprocess.CalledProcessError as e:
            return False, (e.stderr or b"").decode("utf-8", "ignore")[-500:], maten
        except subprocess.TimeoutExpired:
            return False, "Chrome reageerde niet binnen twee minuten.", maten
    return Path(pdf_pad).exists(), "", maten


def main():
    ap = argparse.ArgumentParser(description="Praktijkscan-uitslag naar pdf in werkbankstijl.")
    ap.add_argument("scan", help="markdown-bestand met de uitslag")
    ap.add_argument("--uit", help="pad van de pdf (standaard naast het markdown-bestand)")
    ap.add_argument("--html", action="store_true", help="alleen de html maken")
    ap.add_argument("--afzender", help="json met naam, rol, mail, foto, kop en tekst (standaard afzender.json naast SKILL.md)")
    ap.add_argument("--zonder-afzender", action="store_true", help="geen afzenderkaart, ook als afzender.json bestaat")
    ap.add_argument("--kort", action="store_true", help="drie pagina's: zonder de pagina met plek, kop en voorbehoud")
    a = ap.parse_args()

    afz_pad = Path(a.afzender) if a.afzender else SKILL / "afzender.json"
    afz = None if a.zonder_afzender else lees_afzender(afz_pad)

    bron = Path(a.scan)
    if not bron.is_file():
        sys.exit(f"Geen pdf gemaakt: het bestand '{bron}' bestaat niet. Geef het markdown-bestand met de uitslag mee.")
    try:
        tekst = bron.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as fout:
        sys.exit(f"Geen pdf gemaakt: ik kan '{bron}' niet lezen als tekst ({fout}).")
    if not lees_bouwstenen(sectie(lees(tekst), "bouwstenen")):
        sys.exit("Geen pdf gemaakt: ik vind geen tabel onder '## Bouwstenen' met de twaalf bouwstenen en hun antwoorden "
                 "(j, n of ?). Het bestand volgt het format uit SKILL.md, stap 4, niet (een scan van voor versie 3 kan niet).")
    meldingen = []
    h = bouw_html(tekst, afzender=afz, afzender_basis=afz_pad.parent, kort=a.kort, meldingen=meldingen, bron_map=bron.resolve().parent)
    for m in meldingen:
        print("Let op: " + m, file=sys.stderr)
    pdf_pad = Path(a.uit) if a.uit else bron.with_suffix(".pdf")
    html_pad = pdf_pad.with_suffix(".html")
    if a.html:
        html_pad.write_text(h, encoding="utf-8")
        print(f"Html geschreven: {html_pad}")
        return
    with tempfile.TemporaryDirectory() as werk:
        tijdelijk = Path(werk) / "praktijkscan.html"
        tijdelijk.write_text(h, encoding="utf-8")
        ok, fout, maten = maak_pdf(tijdelijk, pdf_pad)
    if not ok:
        html_pad.write_text(h, encoding="utf-8")
        print(f"Pdf maken lukte niet ({fout}). De html staat hier: {html_pad}. "
              "Open hem in een browser en kies Afdrukken > Opslaan als pdf.", file=sys.stderr)
        sys.exit(1)
    for n, (u, past) in enumerate(maten, 1):
        if not past:
            print(f"Let op: pagina {n} past niet, ook niet met de kleinste letter; er valt tekst weg. Maak de zinnen korter.", file=sys.stderr)
        elif u < (8.6 if n == len(maten) and len(maten) > 1 else 9):
            print(f"Let op: pagina {n} is verkleind naar {str(u).replace('.', ',')} punt (normaal 10). Kortere zinnen lezen beter.", file=sys.stderr)
    print(f"Pdf geschreven: {pdf_pad} ({len(maten) or '?'} pagina's)")


if __name__ == "__main__":
    main()
