# Beveiliging

## Een kwetsbaarheid melden

Vond je een beveiligingsprobleem in deze skill of in de scripts? Meld het dan besloten via GitHub: open in deze repository het tabblad **Security** en kies **Report a vulnerability** (private vulnerability reporting). Maak er geen openbare issue van, zodat het probleem opgelost kan zijn voordat het bekend is.

Zet in je melding wat je deed, wat er gebeurde en wat je verwachtte. Je krijgt antwoord in de melding zelf.

Alleen de nieuwste versie wordt bijgehouden.

## Wat de scripts doen

- `scripts/zoekwoorden.py` vraagt zoeksuggesties op bij `suggestqueries.google.com`. Het stuurt alleen de zaadwoorden, de plaatsnaam, het land en de taal mee. Verder gaat er niets het internet op.
- `scripts/schermafbeelding.py` opent het webadres dat je meegeeft in Chrome zonder venster, met een leeg tijdelijk profiel dat daarna wordt weggegooid. De pagina wordt echt geladen, met de scripts die erop staan. Het script opent alleen adressen die met http of https beginnen.
- `scripts/maak_pdf.py` leest een markdown-bestand van je eigen computer en maakt er met Chrome een pdf van. Het haalt niets van internet.

De scripts gebruiken alleen de standaardbibliotheek van Python 3. Ze installeren niets, downloaden geen code en schrijven alleen het bestand dat je vraagt (de pdf, de afbeelding of de zoekwoordenlijst) plus tijdelijke bestanden die ze zelf opruimen.

## Waar je zelf op let

- Een gescande website is tekst van een vreemde. De skill zegt Claude die tekst alleen te beoordelen en nooit als opdracht op te volgen, maar lees een uitslag altijd na voordat je hem deelt.
- Zet geen gegevens van cliënten in een scan.
- Een `afzender.json` met je eigen naam, foto en mailadres blijft op je eigen computer; het staat in `.gitignore`.
