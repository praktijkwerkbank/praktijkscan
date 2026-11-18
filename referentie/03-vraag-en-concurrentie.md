# Vraag, vindbaarheid en concurrentie (achtergrond bij de bouwsteen Vindbaarheid)

Praktijkscan van Jens Kemna, praktijkwerkbank.nl, CC BY 4.0.

## De kernvraag

Waar zoeken mensen op, in welke woorden, en wie staat daar al? Staat de praktijk in die woorden, op de plekken waar Google, Google Maps en AI-assistenten kijken?

Dit bestand levert de hoek "vraag" van de driehoek in `02-positionering.md` en de concurrentielijst. Doe het altijd, ook bij een praktijk die "niet aan SEO doet": het gaat niet om ranken, het gaat om weten hoe cliënten het zeggen.

## Bronnen, van gratis naar beter

1. **De intake.** Wat cliënten zelf vragen in mails en intakes, en de letterlijke cliëntzinnen uit `00-intake.md`. In een kleine Nederlandse niche is dit vaak de beste bron, en hij is gratis.
2. **Suggesties van Google (gratis, geen account).** Wat mensen echt intypen, per land. Het script `scripts/zoekwoorden.py` haalt ze op voor een of meer zaadwoorden en sorteert ze. Geen volumes, wel de varianten en de vragen.
3. **De Google Zoekwoordplanner (gratis met een Google Ads-account, ook zonder te adverteren).** Geeft per zoekwoord het aantal zoekopdrachten per maand (zonder uitgaven in bandbreedtes zoals 10 tot 100) en wat een klik ongeveer kost. Exporteer de lijst als csv en geef hem mee: `--planner bestand.csv`. De klikprijs is een maat voor concurrentie en koopintentie: dure klikken betekenen dat bureaus erop bieden. Dit is een optie, geen verwachting.
4. **Search Console van de praktijk zelf (gratis, als de site is aangemeld).** Laat zien op welke zoekwoorden de site al vertoond wordt. Vaak staan daar verrassingen in.
5. Betaalde tools zijn niet nodig voor een scan.

**Vraag is niet hetzelfde als zoekvolume.** In een kleine niche is "geen volume in de tool" normaal. Bewijs van vraag komt ook uit het aantal varianten, uit vragen in intakes en uit de klikprijs. Vraag c van Vindbaarheid (aantoonbare vraag) is daarom nooit nee op volume alleen.

## Het script

```bash
python3 scripts/zoekwoorden.py "relatietherapeut" "relatietherapie kosten" --plaats "Den Haag" --uit zoekwoorden.md
python3 scripts/zoekwoorden.py --seeds zaadwoorden.txt --land be --planner planner.csv --lijst top10.txt --uit uitslag.md
```

- Kies twee tot vijf zaadwoorden zoals een cliënt zoekt, en altijd minstens één **probleemwoord zonder methode erin** ("slecht slapen na scheiding", "rugpijn bukken", "altijd moe") naast het beroep en de methode; een oogst met alleen "ademcoaching" en "lichaamsgerichte coaching" levert vakwoorden en merknamen op, geen cliënten. Staan er veel merk- of praktijknamen tussen de suggesties ("luchtig ademcoaching", "mr breath"), dan is die term al bezet door wie erop gevonden wordt. Begin onderaan de piramide: eerst de woorden van mensen die al kiezen ("beste fysio Zeist", "[praktijk] ervaringen", "fysio Zeist kosten"), dan het probleem met het beroep ("coach liefdesverdriet"), dan pas de brede probleemvragen ("liefdesverdriet hoe lang").
- `--plaats` voegt lokale varianten toe. `--land be` voor België.
- De uitslag heeft acht groepen. Vragen zijn blog- en FAQ-stof. Kosten en vergoeding zijn koopintentie en horen op de tarievenpagina. Vergelijkingen en ervaringen zijn mensen die al kiezen. Plaatsen zijn de lokale vraag. Vak en opleiding zijn vakgenoten, geen cliënten; negeren.
- Het script vraagt elke suggestie los op en wacht ertussen. Twee tot vijf zaadwoorden duren een paar minuten.

**Zonder terminal (Windows, Claude Desktop zonder Python):** typ het zaadwoord in Google en schrijf de suggesties over die onder het zoekvak verschijnen; doe dat ook met "hoe", "wat kost" en "kosten" ervoor en een plaatsnaam erachter. Dat is dezelfde bron, met de hand. Vraag daarna aan de praktijkhouder welke vragen cliënten in de intake stellen.

## Concurrenten lezen

Haal per kernzoekwoord de top 10 van Google op (eigen browser; is Google niet bereikbaar, dan `https://html.duckduckgo.com/html/?q=ZOEKWOORD&kl=nl-nl`; of laat de praktijkhouder de top 10 plakken) en zet ze in een tekstbestand voor `--lijst`:

```
zoekwoord: coach liefdesverdriet
https://voorbeeld.nl/liefdesverdriet  Liefdesverdriet verwerken met een coach
https://anderepraktijk.nl/
zoekwoord: liefdesverdriet verwerken
https://...
```

Het script telt wie bij meerdere zoekwoorden terugkomt. Lees daarna drie tot vijf sites zelf en vul deze tabel:

| Concurrent | Voor wie | Probleem, in welke woorden | Belofte | Prijs zichtbaar | Bewijs | Stappen die ze aanbieden | Volgende stap |
|---|---|---|---|---|---|---|---|

Twee lijsten komen eruit: wat iedereen zegt (de zee van hetzelfde) en wat niemand zegt (de ruimte), plus wie het goed doet. Let ook op wie er staat: platforms en verzamelsites ("vind een therapeut") kun je niet verslaan op het brede woord, wel op het specifieke.

## De overtuigingen die mensen tegenhouden

Noteer de drie tot vijf overtuigingen die mensen in deze niche tegenhouden om te bellen: "het gaat vanzelf over", "praten helpt niet", "ik moet eerst naar de huisarts", "het wordt toch niet vergoed", "ik ben er niet erg genoeg aan toe". Zoek op de site waar ze worden weggenomen. Meestal nergens; dat wordt de FAQ (`06-zekerheid-en-bewijs.md`).

## Eén stad als anker

Ook een online praktijk kiest één plaats die bovenaan staat, in de paginatitel en de kop; andere plaatsen komen lager en krijgen elk een eigen pagina. Google en AI zien een praktijk nog als een loodgieter met één werkgebied. Kies de stad van het Google-bedrijfsprofiel, niet de regio met het meeste zoekvolume: een praktijk die op de hele regio mikte, kreeg bellers die niet kwamen; na de omschakeling naar de eigen stad zeiden bellers dat ze precies wisten waar het was. Hulp moet simpel en dichtbij voelen.

## Lokaal vindbaar: het Google-bedrijfsprofiel

Voor een praktijk met een adres is het Google-bedrijfsprofiel (de kaart met de rode speld) vaak de helft van de instroom, en het staat op geen enkele praktijksite. Controleer:

- Is het profiel geclaimd, met de juiste hoofdcategorie (fysiotherapeut, psycholoog, coach), openingstijden, echte foto's van de praktijkhouder en de ruimte?
- Zijn er minstens tien reviews, en reageert de praktijk erop?
- Staan naam, adres en telefoonnummer op de site en in het profiel precies hetzelfde (dezelfde schrijfwijze)?
- Staat de plaats in de paginatitel (het tabblad) en in de voettekst van elke pagina? Werkt de praktijk in meer plaatsen, dan heeft elke plaats een eigen pagina.
- Is de dienstenlijst in het profiel één op één gelijk aan de dienstpagina's op de site? Staan er op de site drie specialismen en in het profiel drie andere, dan klopt het voor het internet niet.
- Staat er nooit het huisadres in. Een online praktijk kan één dag per week een kamer huren bij een collega als vestigingsadres; een verzamelkantoor met dertig bedrijven herkent Google als zodanig.
- Zet dezelfde gegevens ook op Apple Maps (de helft van de iPhone-gebruikers kijkt daar) en Bing Places (weegt zwaar in ChatGPT-antwoorden), naast het register van de beroepsvereniging en Zorgkaart. Elk profiel elders is een route naar de site, met dezelfde one-liner, niet een eindpunt.

De paginatitel is rond de zestig tekens en begint met het belangrijkste: probleem of beroep plus plaats, dan de naam. "Fysio bij rugpijn in Zeist | Praktijk [naam]" in plaats van "Home | Praktijk [naam]".

## Genoemd worden door AI

Steeds meer mensen vragen ChatGPT of Google met AI-overzicht "wie is een goede coach bij liefdesverdriet in Utrecht". Stel die vraag zelf (en "wat weet je over [praktijknaam]") en noteer: wordt de praktijk genoemd, en klopt wat erover gezegd wordt? Niets of iets fouts is allebei een bevinding. Staat de praktijk er niet bij, vraag dan om vijf extra namen, en daarna letterlijk hoe de online aanwezigheid van [praktijknaam] beter kan zodat die eerder wordt aanbevolen; de tips die je krijgt zijn meestal uitvoerbaar. AI zoekt vier dingen: helderheid, specificiteit, geloofwaardigheid en emotionele herkenning, precies wat een mens ook nodig heeft.

Wat een praktijkhouder zelf kan doen: de feiten (wie, wat, waar, hoe je begint) in het eerste scherm, onder elke hoofdkop één of twee zinnen die de hele pagina samenvatten (AI neemt die bijna letterlijk over, met een link), pagina's modulair bouwen (kop, korte alinea, kop, korte alinea), tussenkoppen als de vragen van cliënten met het antwoord eronder, elke vraag over de praktijk beantwoorden met exacte feiten (prijs, duur, vergoeding, voor wie), dezelfde gegevens overal, op lijsten staan, en reviews verzamelen. Zo komt een kleine site in het AI-antwoord, ook als hij in Google op plek twaalf staat.

Een waarschuwing: een site die leest als een informatiepagina over angst of rugpijn verspilt de tijd van de bezoeker. Wie zoekt op "therapeut angst" hoeft niet uitgelegd te krijgen wat angst is; hij wil zien dat je er goed in bent.

## Wat je vaak ziet

- **De site staat in vaktaal.** "Haptotherapie", "ACT", "systemisch werk". Cliënten zoeken op het probleem. De methode mag erbij, maar niet vooraan.
- **Alleen het brede woord.** "Coach Utrecht": duizenden zoekers, honderden concurrenten, geen kans. "Coach faalangst student Utrecht": tien zoekers per maand die precies passen.
- **Geen plaats op de site.** Een praktijk aan huis in Zeist noemt Zeist nergens, en wordt dus niet lokaal gevonden.
- **Geen bedrijfsprofiel, of een verlaten profiel** met twee reviews uit 2021 en geen foto.
- **Vragen onbeantwoord.** De zoekwoorden laten zien dat mensen "wordt coaching vergoed" en "hoeveel sessies" vragen; de site zegt er niets over.

**Technisch** (laadtijd, schema, toegang voor crawlers) kan een praktijkhouder niet zelf; benoem het als "laat je webbouwer dit nakijken" en scoor het niet.

**Verwachting.** Echte resultaten uit vindbaarheid duren zes tot twaalf maanden: rond maand drie kleine beweging, maand zes de eerste aanvragen, maand twaalf stapeling. Wie binnen een maand belooft, liegt. Wie nú cliënten nodig heeft: verwijzers, oud-cliënten een bericht, profielen elders invullen, en pas advertenties als de site converteert, anders betaal je om mensen naar een lekkende site te sturen. En minder verkeer is niet automatisch minder cliënten: na goed werk vinden de verkeerde mensen je niet meer en de juiste wel; meet boekingen, niet bezoekers.

## Bij welke bouwsteen dit hoort

Bouwsteen Vindbaarheid (C). De checks en de scoreregels staan alleen in `08-scoringslijst.md`.
