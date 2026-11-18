#!/usr/bin/env python3
"""
Zoekwoorden en concurrenten voor een praktijk, zonder account.

Onderdeel van de Praktijkscan van Jens Kemna (praktijkwerkbank.nl).
Licentie van dit script: MIT, zie LICENSE-MIT in de hoofdmap.

Wat het doet:
  1. Haalt echte zoekopdrachten op via de suggesties van Google (wat mensen
     intypen, in jouw land en taal). Gratis, geen account nodig.
  2. Sorteert ze op soort: vraag, kosten, vergelijking, plaats, online, algemeen, vak, anders.
  3. Optioneel: koppelt zoekvolumes uit een export van de Google
     Zoekwoordplanner (--planner bestand.csv).
  4. Optioneel: leest een geplakte lijst met de top 10 per zoekwoord
     (--lijst bestand.txt) en telt wie bij meerdere zoekwoorden terugkomt.
     De top 10 haal je zelf uit Google, of je laat Claude hem met zijn browser ophalen.

Gebruik:
  python3 zoekwoorden.py "coach liefdesverdriet" "liefdesverdriet verwerken"
  python3 zoekwoorden.py "fysiotherapeut rugklachten" --plaats "Den Haag" --lijst top10.txt   (top 10 geplakt, zie lees_lijst)
  python3 zoekwoorden.py --seeds zaadwoorden.txt --land be --planner planner.csv --uit uitslag.md

Alleen standaardbibliotheek van Python 3, geen installatie nodig.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; Praktijkscan)"
LETTERS = list("abcdefghijklmnoprstuvwz")
VOOR = ["hoe", "wat", "waarom", "wanneer", "welke", "beste", "goede", "kosten", "help"]
ACHTER = ["in", "bij", "voor", "ervaringen", "kosten", "vergoed", "online", "tips", "of"]
SOORTEN = [
    ("vraag", re.compile(r"^(hoe|wat|waarom|wanneer|welke|wie|kan|is|moet|helpt)\b")),
    ("kosten", re.compile(r"\b(kosten|prijs|tarief|tarieven|vergoed|vergoeding|verzekering|gratis|goedkoop)\b")),
    ("vergelijking", re.compile(r"\b(of|vs|versus|verschil|beste|goede|review|reviews|ervaring|ervaringen)\b")),
    ("online", re.compile(r"\b(online|thuis|app|zelf)\b")),
]
# Plaatsnamen, gescheiden door komma's zodat namen van meer woorden heel blijven.
# Bewust weggelaten: plaatsnamen die ook een gewoon woord zijn (huizen, bergen, geel, rijen, putten, best,
# lier, mol, peel, goes, hoorn, halle, epe), anders worden "huizen kopen" of "beste coach" een plaats.
PLAATSEN = [p.strip() for p in """amsterdam, rotterdam, den haag, utrecht, eindhoven, groningen, tilburg, almere, breda, nijmegen,
apeldoorn, haarlem, arnhem, enschede, amersfoort, zaanstad, zaandam, haarlemmermeer, zwolle, leiden, zoetermeer, maastricht,
dordrecht, ede, alphen aan den rijn, leeuwarden, alkmaar, delft, emmen, deventer, venlo, westland, oss, amstelveen, hilversum,
sittard, geleen, heerlen, helmond, hengelo, purmerend, schiedam, roosendaal, lelystad, leidschendam, voorburg, vlaardingen, gouda,
almelo, spijkenisse, assen, bergen op zoom, capelle aan den ijssel, veenendaal, katwijk, zeist, nieuwegein, hardenberg, doetinchem,
roermond, den bosch, 's-hertogenbosch, middelburg, vlissingen, terneuzen, drachten, heerenveen, sneek, kampen, harderwijk,
barneveld, ermelo, soest, baarn, bussum, naarden, weesp, woerden, houten, ijsselstein, vianen, culemborg, tiel, wijchen, oosterhout,
waalwijk, etten-leur, etten leur, uden, veghel, boxtel, veldhoven, geldrop, valkenswaard, weert, cuijk, boxmeer, venray, gennep,
goirle, dongen, drunen, kaatsheuvel, wageningen, rhenen, druten, nijkerk, elburg, heerde, raalte, dalfsen, ommen, steenwijk, meppel,
hoogeveen, coevorden, stadskanaal, veendam, winschoten, delfzijl, appingedam, franeker, harlingen, bolsward, joure, wolvega,
emmeloord, urk, dronten, zeewolde, noordwijk, lisse, hillegom, sassenheim, oegstgeest, voorschoten, wassenaar, rijswijk, pijnacker,
nootdorp, delfgauw, maassluis, hellevoetsluis, brielle, hendrik-ido-ambacht, zwijndrecht, papendrecht, sliedrecht, gorinchem,
leerdam, ridderkerk, barendrecht, krimpen aan den ijssel, bodegraven, nieuwkoop, castricum, heiloo, uitgeest, beverwijk, velsen,
ijmuiden, heemskerk, heerhugowaard, schagen, den helder, enkhuizen, medemblik, edam, volendam, monnickendam, diemen, uithoorn,
aalsmeer, hoofddorp, nieuw-vennep, nieuw vennep, badhoevedorp, zandvoort, heemstede, bloemendaal, leusden, maarssen, bilthoven,
de bilt, driebergen, doorn, elst, oosterbeek, duiven, zevenaar, oldenzaal, borne, rijssen, nijverdal,
antwerpen, gent, brugge, leuven, mechelen, hasselt, kortrijk, aalst, sint-niklaas, sint niklaas, oostende, genk, roeselare,
turnhout, dendermonde, lokeren, beveren, herentals, tienen, diest, aarschot, vilvoorde, zaventem, dilbeek, knokke, blankenberge,
ieper, waregem, deinze, eeklo, maaseik, tongeren, bilzen, beringen, lommel, brussel,
noord-brabant, noord brabant, gelderland, friesland, drenthe, overijssel, zeeland, flevoland, twente, achterhoek, betuwe, veluwe,
het gooi, randstad, bollenstreek, kempen, salland, rivierenland, noord-holland, noord holland, zuid-holland, zuid holland,
west-vlaanderen, west vlaanderen, oost-vlaanderen, oost vlaanderen, vlaams-brabant, vlaams brabant, belgie, belgië, nederland,
omgeving, regio, in de buurt, bij mij in de buurt, dichtbij""".replace("\n", " ").split(",") if p.strip()]
REGIO = {"omgeving", "regio", "in de buurt", "bij mij in de buurt", "dichtbij"}


def plaats_regex(eigen=""):
    namen = set(PLAATSEN)
    if eigen:
        namen.add(eigen.lower().strip())
    return re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n in sorted(namen, key=len, reverse=True)) + r")(?![\w-])")


PLAATSNAMEN = plaats_regex()
EIGEN_PLAATS = ""
VAK = re.compile(r"\b(opleiding|opleidingen|worden|verdient|verdienen|salaris|vacature|vacatures|certificering|erkend|beroep|ausbildung|kursleiter|fortbildung|uddannelse|kurs|certification)\b")
ANDERS_TAAL = re.compile(r"\b(kosten krankenkasse|krankenkasse|machen|kostenlos|online kurs|course|training online|wie oft|the |for |with )\b")


MISLUKT = [0, 0]  # [mislukte opvragingen, alle opvragingen]


def haal(url, pogingen=3):
    MISLUKT[1] += 1
    for p in range(pogingen):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        except Exception:
            # is de allereerste opvraging al mislukt, wacht dan niet lang op de rest
            time.sleep(0.2 if MISLUKT[0] >= 3 else 1.5 * (p + 1))
            if MISLUKT[0] >= 3:
                break
    MISLUKT[0] += 1
    return ""


def suggesties(q, land, taal):
    url = (
        "https://suggestqueries.google.com/complete/search?client=firefox"
        f"&hl={taal}&gl={land}&q=" + urllib.parse.quote(q)
    )
    tekst = haal(url)
    if not tekst:
        return []
    try:
        return [s.lower().strip() for s in json.loads(tekst)[1]]
    except Exception:
        return []


def oogst(zaad, land, taal, plaats, pauze, log):
    vragen = [zaad] + [f"{zaad} {l}" for l in LETTERS]
    vragen += [f"{v} {zaad}" for v in VOOR] + [f"{zaad} {a}" for a in ACHTER]
    if plaats:
        vragen += [f"{zaad} {plaats}", f"{zaad} {plaats} ", f"{plaats} {zaad}"]
    gevonden = {}
    for i, v in enumerate(vragen):
        for s in suggesties(v, land, taal):
            gevonden.setdefault(s, set()).add(zaad)
        time.sleep(pauze)
        if log and i % 10 == 0:
            print(f"  {zaad}: {i + 1}/{len(vragen)} opvragingen, {len(gevonden)} zoekwoorden", file=sys.stderr)
    return gevonden


def soort_van(zoekwoord):
    if ANDERS_TAAL.search(zoekwoord):
        return "anders"
    if VAK.search(zoekwoord):
        return "vak"
    if PLAATSNAMEN.search(zoekwoord):
        return "plaats"
    for naam, patroon in SOORTEN:
        if patroon.search(zoekwoord):
            return naam
    return "algemeen"


def lees_planner(pad):
    """Leest een export van de Google Zoekwoordplanner (csv, komma of tab).
    Zoekt zelf de kolommen 'Keyword' en 'Avg. monthly searches' (of de Nederlandse namen)."""
    volumes = {}
    if not pad:
        return volumes
    with open(pad, "rb") as f:
        ruw = f.read()
    # Google levert de export als UTF-16 met tabs; een bestand uit Excel of Sheets is meestal UTF-8.
    if ruw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        inhoud = ruw.decode("utf-16", "ignore")
    elif ruw[:200].count(b"\x00") > 20:
        inhoud = ruw.decode("utf-16-le", "ignore")
    else:
        inhoud = ruw.decode("utf-8-sig", "ignore")
    scheiding = "\t" if inhoud.count("\t") > inhoud.count(",") else (";" if inhoud.count(";") > inhoud.count(",") else ",")
    regels = list(csv.reader(inhoud.splitlines(), delimiter=scheiding))
    kop_i = None
    for i, r in enumerate(regels[:10]):
        lower = [c.strip().lower() for c in r]
        # de kopregel heeft meer kolommen en een cel die precies "keyword" of "zoekwoord" heet;
        # de titelregel "Keyword Stats ..." bovenaan de export is dat niet
        if len(lower) > 1 and any(c in ("keyword", "keywords", "zoekwoord", "zoekwoorden", "zoekterm") for c in lower):
            kop_i = i
            break
    if kop_i is None:
        print("Planner-bestand: geen kolom 'Keyword' of 'Zoekwoord' gevonden, volumes overgeslagen.", file=sys.stderr)
        return volumes
    kop = [c.strip().lower() for c in regels[kop_i]]
    k_i = next(i for i, c in enumerate(kop) if c in ("keyword", "keywords", "zoekwoord", "zoekwoorden", "zoekterm"))
    v_i = next((i for i, c in enumerate(kop) if "monthly" in c or "maand" in c or "gem." in c), None)
    if v_i is None:
        print("Planner-bestand: geen kolom met zoekopdrachten per maand gevonden, volumes overgeslagen.", file=sys.stderr)
        return volumes
    for r in regels[kop_i + 1:]:
        if len(r) > k_i and r[k_i].strip():
            vol = r[v_i].strip() if v_i is not None and len(r) > v_i else ""
            volumes[r[k_i].strip().lower()] = vol
    return volumes


def lees_lijst(pad):
    """Leest een geplakte lijst met zoekresultaten. Opbouw van het bestand:

        zoekwoord: coach liefdesverdriet
        https://voorbeeld.nl/liefdesverdriet  Titel van de pagina (optioneel)
        https://anderepraktijk.nl/

        zoekwoord: liefdesverdriet verwerken
        ...

    De top 10 haal je zelf uit Google (of laat je Claude ophalen met zijn browser).
    Het script telt dan welke domeinen bij meerdere zoekwoorden terugkomen."""
    conc = {}
    huidig = None
    for regel in open(pad, encoding="utf-8"):
        regel = regel.strip()
        if not regel:
            continue
        if regel.lower().startswith("zoekwoord:"):
            huidig = regel.split(":", 1)[1].strip().lower()
            conc.setdefault(huidig, [])
            continue
        if huidig is None or not regel.startswith("http"):
            continue
        delen = regel.split(None, 1)
        link = delen[0]
        titel = delen[1] if len(delen) > 1 else ""
        domein = re.sub(r"^https?://(www\.)?", "", link).split("/")[0]
        if domein and all(d != domein for d, _, _ in conc[huidig]):
            conc[huidig].append((domein, titel, link))
    return conc


def markdown(zaden, gevonden, volumes, conc, land):
    regels = []
    regels.append(f"# Zoekwoorden en concurrenten ({', '.join(zaden)}; land {land.upper()})\n")
    regels.append("Bron: suggesties van Google (wat mensen echt intypen). Volumes alleen als een export van de Zoekwoordplanner is meegegeven.\n")
    per_soort = {}
    for z, bronnen in gevonden.items():
        per_soort.setdefault(soort_van(z), []).append((z, sorted(bronnen)))
    volgorde = ["vraag", "kosten", "vergelijking", "plaats", "online", "algemeen", "vak", "anders"]
    titels = {
        "vraag": "Vragen die mensen stellen (blog- en FAQ-stof)",
        "kosten": "Over kosten en vergoeding (koopintentie, hoort op je tarievenpagina)",
        "vergelijking": "Vergelijken en ervaringen (mensen die al kiezen)",
        "plaats": "Met een plaats erin (lokale vraag)",
        "online": "Online of zelf (vraag naar een andere vorm)",
        "algemeen": "Overige zoekwoorden",
        "vak": "Vak en opleiding (vakgenoten die het vak willen leren, niet je cliënten; negeren)",
        "anders": "Andere taal of ruis (negeren)",
    }
    regels.append(f"Totaal {len(gevonden)} zoekwoorden.\n")
    for s in volgorde:
        items = sorted(per_soort.get(s, []))
        if not items:
            continue
        overig_plaats = []
        if s == "plaats":
            eigen = EIGEN_PLAATS.lower()
            dichtbij = [it for it in items if (eigen and eigen in it[0]) or any(r in it[0] for r in REGIO)]
            rest = [it for it in items if it not in dichtbij]
            if eigen:
                items, overig_plaats = dichtbij, rest
            elif len(items) > 40:
                items, overig_plaats = dichtbij + rest[:40], rest[40:]
        regels.append(f"## {titels[s]} ({len(items)})\n")
        if not items:
            regels.append("Geen zoekwoorden met je eigen plaats of met 'in de buurt'.\n")
        kop = "| Zoekwoord | Via zaadwoord |" + (" Per maand |" if volumes else "")
        regels.append(kop)
        regels.append("|---|---|" + ("---|" if volumes else ""))
        for z, bronnen in items:
            rij = f"| {z} | {', '.join(bronnen)} |"
            if volumes:
                rij += f" {volumes.get(z, '')} |"
            regels.append(rij)
        regels.append("")
        if overig_plaats:
            plaatsen = {}
            for z, _ in overig_plaats:
                m = PLAATSNAMEN.search(z)
                if m:
                    plaatsen[m.group(1)] = plaatsen.get(m.group(1), 0) + 1
            top = ", ".join(f"{p} ({n})" for p, n in sorted(plaatsen.items(), key=lambda x: -x[1])[:12])
            regels.append(f"Daarnaast {len(overig_plaats)} zoekwoorden met andere plaatsen. Het vaakst: {top}. "
                          "Dat laat zien dat mensen hier met een plaatsnaam zoeken; de lijst zelf is voor jouw praktijk niet nodig.\n")
    if conc:
        regels.append("## Wie staat er al op die plek (top 10 per zoekwoord)\n")
        telling = {}
        for zaad, lijst in conc.items():
            regels.append(f"### {zaad}\n")
            regels.append("| # | Domein | Titel van de pagina |")
            regels.append("|---|---|---|")
            for i, (d, t, _) in enumerate(lijst, 1):
                regels.append(f"| {i} | {d} | {t} |")
                telling[d] = telling.get(d, 0) + 1
            regels.append("")
        vaak = [(d, n) for d, n in telling.items() if n > 1]
        if vaak:
            regels.append("### Komt bij meerdere zoekwoorden terug\n")
            for d, n in sorted(vaak, key=lambda x: -x[1]):
                regels.append(f"- {d} ({n} keer)")
            regels.append("")
        regels.append("Lees per concurrent: voor wie, welk probleem in welke woorden, prijs zichtbaar of niet, bewijs, en wat de volgende stap is. Wat ze allemaal zeggen is de zee van hetzelfde; wat niemand zegt is jouw ruimte.\n")
    return "\n".join(regels)


def main():
    ap = argparse.ArgumentParser(description="Zoekwoorden en concurrenten voor een praktijk (Praktijkscan, Jens Kemna).")
    ap.add_argument("zaden", nargs="*", help="zaadwoorden, bijvoorbeeld \"coach liefdesverdriet\"")
    ap.add_argument("--seeds", help="tekstbestand met een zaadwoord per regel")
    ap.add_argument("--land", default="nl", help="nl of be (standaard nl)")
    ap.add_argument("--taal", default="nl")
    ap.add_argument("--plaats", default="", help="plaatsnaam voor lokale varianten")
    ap.add_argument("--planner", help="csv-export van de Google Zoekwoordplanner, voor volumes")
    ap.add_argument("--lijst", help="tekstbestand met de geplakte top 10 per zoekwoord (zie lees_lijst)")
    ap.add_argument("--uit", help="schrijf het resultaat naar dit bestand (markdown)")
    ap.add_argument("--json", help="schrijf ook de ruwe data naar dit json-bestand")
    ap.add_argument("--pauze", type=float, default=0.15, help="seconden tussen opvragingen")
    ap.add_argument("--stil", action="store_true")
    a = ap.parse_args()

    for vlag, pad in (("--seeds", a.seeds), ("--planner", a.planner), ("--lijst", a.lijst)):
        if pad and not os.path.isfile(pad):
            sys.exit(f"Het bestand bij {vlag} bestaat niet: {pad}")
    zaden = [z.strip().lower() for z in a.zaden if z.strip()]
    if a.seeds:
        zaden += [l.strip().lower() for l in open(a.seeds, encoding="utf-8") if l.strip()]
    if not zaden:
        ap.error("geef minstens een zaadwoord")

    global PLAATSNAMEN, EIGEN_PLAATS
    EIGEN_PLAATS = a.plaats.lower().strip()
    PLAATSNAMEN = plaats_regex(EIGEN_PLAATS)
    gevonden = {}
    for z in zaden:
        for k, v in oogst(z, a.land, a.taal, a.plaats, a.pauze, not a.stil).items():
            gevonden.setdefault(k, set()).update(v)
    if MISLUKT[1] and MISLUKT[0] == MISLUKT[1]:
        sys.exit("Geen verbinding met de suggesties van Google: alle opvragingen mislukten. Dit zegt NIETS over de vraag "
                 "naar deze woorden. Controleer de internetverbinding (of een VPN of filter) en probeer het opnieuw, "
                 "of gebruik de route zonder terminal uit SKILL.md.")
    if MISLUKT[0]:
        print(f"Let op: {MISLUKT[0]} van de {MISLUKT[1]} opvragingen mislukten; de lijst is niet compleet.", file=sys.stderr)
    if not gevonden:
        print("Let op: Google gaf bij deze zaadwoorden geen enkele suggestie. Probeer een korter of gewoner woord "
              "voordat je concludeert dat er geen vraag is.", file=sys.stderr)
    volumes = lees_planner(a.planner)
    conc = lees_lijst(a.lijst) if a.lijst else {}

    md = markdown(zaden, gevonden, volumes, conc, a.land)
    if a.uit:
        with open(a.uit, "w", encoding="utf-8") as f:
            f.write(md)
        if not a.stil:
            print(f"Geschreven: {a.uit}", file=sys.stderr)
    else:
        print(md)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({
                "zaden": zaden,
                "zoekwoorden": {k: {"via": sorted(v), "soort": soort_van(k), "per_maand": volumes.get(k, "")} for k, v in gevonden.items()},
                "concurrenten": {z: [{"domein": d, "titel": t, "url": u} for d, t, u in l] for z, l in conc.items()},
            }, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
