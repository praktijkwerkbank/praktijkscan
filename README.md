# De Praktijkscan van Jens Kemna

**In English:** a Dutch-language skill for Claude (Claude Code, Claude Desktop and Cowork) that reviews the website and offer of a small practice: coaches, therapists, physiotherapists, dietitians and psychologists in the Netherlands and Belgium. It checks twelve building blocks with yes-or-no questions, reads the competition, gives a score out of 100, names the three changes that matter most, and can turn the result into a four-page PDF. The skill, its instructions and its output are in Dutch. Text is licensed CC BY 4.0, the scripts MIT.

Een skill voor Claude (Claude Code, Claude Desktop en Cowork) die de website en het aanbod van een praktijk doorlicht: coaches, therapeuten, fysiotherapeuten, diëtisten, psychologen en lichaamsgerichte praktijken. De scan kijkt naar twaalf bouwstenen met elk vijf ja-of-nee-vragen (zakelijk heeft Snelheid er vier), met aparte vragen voor praktijken die aan particulieren verkopen en praktijken die aan organisaties verkopen, leest de concurrentie, geeft een score van 100 en zegt welke drie veranderingen het meest opleveren. De uitslag komt in het gesprek, en op verzoek als pdf van vier pagina's.

Gemaakt door **Jens Kemna**, coach met een eigen praktijk (jenskemna.com) en maker van **Praktijkwerkbank** (praktijkwerkbank.nl), het zesweekse programma waarin mensen met een eigen praktijk Claude leren gebruiken als sparringpartner voor hun website en vindbaarheid.

## Wat de scan doet

Eerst de intake: cijfers, de laatste tien cliënten, letterlijke cliëntzinnen, en de vraag of de agenda vol of leeg zit; dat bepaalt waar de scan begint. Daarna twaalf bouwstenen in drie groepen, elk met vijf ja-of-nee-checks:

| Groep | Bouwsteen | Wat het is |
|---|---|---|
| **A De waarde** | Droomresultaat | Het leven na afloop, in de woorden van je cliënt |
| | Geloof dat het lukt | Gelooft je bezoeker dat het bij hem werkt? Plan, ervaringen, reviews |
| | Snelheid | Hoe snel merkt iemand het eerste verschil, en hoe lang duurt het? |
| | Gemak | Hoe weinig moeite, tijd en ongemak kost het? |
| **B Het aanbod** | Garantie | Wie draagt het risico als het tegenvalt? |
| | Pakket en naam | Een aanbod met naam, begin en einde in plaats van losse uren |
| | Prijs | Zichtbaar, na de waarde, en uitgelegd |
| | Reden om nu | Een eerlijke reden om niet te blijven wachten, zonder druk |
| **C Gevonden en gekozen** | Plek | Voor wie, waarmee, en is die plek nog vrij? |
| | Helderheid | Snapt een vreemde het in vijf seconden? |
| | Vindbaarheid | Gevonden in Google, op de kaart en in AI |
| | Volgende stap | Eén kleine, veilige stap, en een pad dat werkt |

Groep A en B volgen het waardedenken van Alex Hormozi, in eigen woorden: een aanbod voelt meer waard naarmate het droomresultaat groter is en het geloof dat het lukt sterker, en naarmate de wachttijd korter is en de moeite kleiner. De totaalscore is het percentage van de getoetste checks dat klopt.

**Particulier of zakelijk.** Verkoopt een praktijk aan organisaties (workshops voor teams, een vitaliteitsweek, coaching via de werkgever), dan is de koper een ander mens dan de deelnemer. De vragen passen zich daarop aan: een garantie gaat dan over het risico van de organisator, bewijs over cases en klantnamen, de volgende stap over een voorstel en iets om intern door te sturen.

**De uitslag** komt als tekst in het gesprek, en op verzoek als één pdf van vier pagina's: het overzicht met je eerste scherm nu en straks, wat al werkt en de concurrentie; "Wat nu" met de drie dingen die het meest opleveren en hoe je meet; het voorstel voor je plek en je kop; en als bijlage de twaalf bouwstenen met wat er opviel en per vraag ja of nee.

Elke scan zegt hoe je meet of het werkt (tel je aanvragen, vraag hoe mensen je vonden, kijk na 30, 60 en 90 dagen) en geeft voorbeeldzinnen die nadrukkelijk voorbeelden zijn: de praktijkhouder schrijft de zinnen zelf, in eigen woorden.

De scan is geïnspireerd op het denken van Alex Hormozi over aanbod en waarde, op wat Amerikaanse praktijkcoaches voor therapeuten leren over websites, tarieven en verwijzers, en op de principes van StoryBrand, conversiecopywriting en Nielsen Norman Group over helderheid en bruikbaarheid. Alles is in eigen woorden vertaald naar een praktijk in Nederland of België: zonder hype, zonder nepurgentie, met de grenzen van zorg en welzijn en de artikelen uit de Reclame Code en de beroepscodes erbij. Het is geen officieel product van Hormozi of van wie dan ook en bevat geen tekst uit hun boeken of video's.

## Wat je nodig hebt

- Claude met skills: Claude Code, Claude Desktop of Cowork. De scan zelf (de uitslag als tekst in het gesprek) werkt overal waar Claude een website kan lezen.
- Voor de pdf, de schermafbeelding en het zoekwoordenscript: Python 3 (alleen de standaardbibliotheek, er wordt niets geïnstalleerd). Voor de pdf en de schermafbeelding ook Google Chrome, Chromium, Brave of Edge. De schermafbeelding werkt op Mac en Linux, niet op Windows.
- Kan Claude bij jou geen scripts draaien (de Claude-app zonder code-uitvoering), dan krijg je de volledige uitslag als tekst en geen pdf.

## Wat je kunt verwachten, en wat niet

De scan kijkt naar wat een website laat zien, niet naar hoe goed iemand is in zijn vak. Hij belooft geen cliënten, geen omzet en geen plek in Google: hij wijst aan wat een bezoeker nu mist en wat je als eerste kunt veranderen. De voorbeeldzinnen zijn suggesties. Claude kan zich vergissen, dus lees een uitslag na voordat je hem deelt of er iets op baseert. De scan is geen juridisch advies; `referentie/11-grenzen-zorg-en-welzijn.md` is achtergrond bij het scoren, en de verwijzingen daarin naar codes en artikelen kunnen verouderd zijn. Lees bij twijfel de code van je eigen beroepsvereniging.

**Zet geen gegevens van cliënten in een scan.** Zinnen van cliënten gebruik je zonder naam en zonder details waaraan iemand te herkennen is, en dossiers of medische gegevens horen er nooit in.

## Installeren

**Claude Code (Mac, Linux, Windows):** zet de map `praktijkscan` in `~/.claude/skills/` (persoonlijk) of in `.claude/skills/` van je project.

```bash
mkdir -p ~/.claude/skills
cp -r praktijkscan ~/.claude/skills/
```

Start Claude Code opnieuw. Typ `/praktijkscan` of zeg "scan mijn site" met je webadres erbij.

**Claude Desktop of Cowork:** ga naar de instellingen voor skills (of de map `skills` van je project), voeg de map `praktijkscan` toe en herstart. Of plak de inhoud van `SKILL.md` als projectinstructie en upload de bestanden uit `referentie/` als projectkennis.

**Zonder installatie:** open een gesprek met Claude, plak `SKILL.md` en het referentiebestand dat je nodig hebt, en geef je webadres.

## Gebruiken

Volledige scan:

> /praktijkscan https://www.jouwpraktijk.nl

Claude stelt eerst een paar vragen (de zes belangrijkste: wie help je het liefst, je laatste tien cliënten, wat cliënten zeggen dat je anders doet, wat ze bijna tegenhield, letterlijke zinnen van cliënten, en je cijfers; daarnaast de vraag of je agenda vol of leeg zit; de volledige lijst van veertien, plus een zakelijke variant, staat in `referentie/00-intake.md`) en levert daarna de uitslag.

Losse vraag:

> Is deze garantie goed voor een coachpraktijk: "Niet tevreden, geld terug"?
> Wat moet ik vragen voor een traject van zes sessies?
> Hoe onderscheid ik me van de andere diëtisten in Haarlem?

Zoekwoorden en concurrenten los draaien (Python 3, geen installatie, geen account):

```bash
python3 scripts/zoekwoorden.py "relatietherapeut" "relatietherapie kosten" --plaats "Den Haag" --uit zoekwoorden.md
```

Volumes erbij? Exporteer een lijst uit de Google Zoekwoordplanner (gratis met een Google Ads-account) en geef hem mee met `--planner bestand.csv`. De top 10 per zoekwoord plak je in een tekstbestand voor `--lijst top10.txt`; het script telt dan wie bij meerdere zoekwoorden terugkomt.

De uitslag komt als tekst in het gesprek. Wil je hem als document, vraag dan om de pdf: vier pagina's in de stijl van Praktijkwerkbank (drie met `--kort`).

```bash
python3 scripts/maak_pdf.py uitslag.md
```

Werkt met Google Chrome, Chromium, Brave of Edge op je computer. Zonder die browser krijg je een html-bestand dat je zelf afdrukt naar pdf.

## Bestanden

| Bestand | Wat erin staat |
|---|---|
| `SKILL.md` | De werkwijze, het uitslagformat en de harde regels |
| `referentie/00-intake.md` | Wat je verzamelt vóór je oordeelt: pagina's, cijfers, cliëntzinnen, veertien vragen (plus een zakelijke variant) |
| `referentie/01-helderheid.md` t/m `07-volgende-stap.md` | De achtergrond per bouwsteen: kernvraag, wat je vaak ziet, wat werkt |
| `referentie/08-scoringslijst.md` | De twaalf bouwstenen met elk vijf vragen, particulier en zakelijk, en hoe de score werkt |
| `referentie/09-voorbeelden.md` | Voor en na uit een coach- en een fysiopraktijk, en twee uitgewerkte scans |
| `referentie/10-schrijfstijl.md` | De schrijfregels voor alles wat herschreven wordt |
| `referentie/11-grenzen-zorg-en-welzijn.md` | Achtergrond bij het scoren: wat een praktijk kan beloven en wat niet. De uitslag zelf noemt geen codes of artikelen; de scan is geen juridisch advies |
| `referentie/12-na-de-eerste-afspraak.md` | Retentie, verwijzers, het kennismakingsgesprek en de spiegel voor de praktijkhouder |
| `scripts/zoekwoorden.py` | Zoekwoorden ophalen, sorteren, volumes koppelen, concurrenten tellen; stopt met een melding als er geen verbinding is |
| `scripts/schermafbeelding.py` | De homepage zoals een telefoon hem toont (390 bij 844), voor "bovenaan" en voor pagina 1 van de pdf |
| `scripts/maak_pdf.py` | De uitslag als één pdf van vier pagina's in werkbankstijl; controleert de uitslag en meldt wat ontbreekt, te lang is of geen bewijs heeft |
| `referentie/13-zakelijk.md` | Als een organisatie de koper is: twee lezers, garantie, bewijs, prijs en volgende stap voor zakelijk |
| `afzender.json` (zelf maken) | Je eigen naam, foto, mailadres en uitnodiging (of een pitch voor je eigen aanbod) onderaan pagina 3 |
| `assets/` | Lettertypes (Archivo en Instrument Sans, beide SIL Open Font License 1.1, tekst in `assets/OFL.txt`) en het merkteken van Praktijkwerkbank als svg |
| `LICENSE`, `LICENSE-MIT` | De licenties: CC BY 4.0 voor de teksten, MIT voor de scripts |
| `CHANGELOG.md`, `SECURITY.md` | Wat er per versie veranderde, en hoe je een beveiligingsprobleem meldt |

## Licentie en naamsvermelding

| Wat | Licentie |
|---|---|
| De teksten: `SKILL.md`, `README.md`, `referentie/` | **Creative Commons Naamsvermelding 4.0 (CC BY 4.0)**, [volledige tekst](https://creativecommons.org/licenses/by/4.0/legalcode) |
| De scripts in `scripts/` | **MIT**, zie `LICENSE-MIT` |
| De lettertypes in `assets/` (Archivo, Instrument Sans) | **SIL Open Font License 1.1**, van hun eigen makers, zie `assets/OFL.txt` |

Waarom twee licenties: Creative Commons is gemaakt voor tekst en raadt zijn licenties af voor programmacode. De scripts vallen daarom onder MIT, de gangbare vrije licentie voor code. Voor jou verandert er weinig: je mag alles gebruiken, kopiëren, aanpassen en doorgeven, ook in je eigen praktijk of programma en ook commercieel.

**Zo vermeld je de naam.** Gebruik of bewerk je de teksten, zet er dan deze regel bij (in je document, je README of je eigen skill):

> Gebaseerd op de Praktijkscan van Jens Kemna (Praktijkwerkbank, praktijkwerkbank.nl), licentie CC BY 4.0. Aangepast door [jouw naam].

Laat de laatste zin weg als je niets hebt veranderd. De skill doet het zelf ook: elke volledige scan eindigt met één regel naamsvermelding. Bij losse vragen niet. Neem je alleen de scripts over, laat dan de copyrightregel uit `LICENSE-MIT` staan.

**Naam en logo.** De naam Praktijkwerkbank en het merkteken (`assets/merk.svg`, ook bovenaan elke pagina van de pdf) vallen niet onder de vrije licentie. Ze mogen blijven staan in de skill en in de rapporten die je ermee maakt. Je mag ze niet gebruiken als naam of logo van je eigen product of bedrijf. Maak je een eigen versie, geef die dan een eigen naam en een eigen merkteken, en vermeld de bron.

**Bronnen.** De waardeformule (droomresultaat, geloof dat het lukt, wachttijd, moeite) en het idee van een aanbod dat je niet kunt vergelijken komen van Alex Hormozi, uit zijn boek *$100M Offers*. Ze zijn hier in eigen woorden naverteld en vertaald naar een praktijk; er is geen tekst van hem overgenomen.

Verbeter je de skill, dan hoor ik dat graag: open een issue of een pull request op GitHub, of mail jens@praktijkwerkbank.nl. Een beveiligingsprobleem meld je besloten, zie `SECURITY.md`.

Jens Kemna, november 2026.
