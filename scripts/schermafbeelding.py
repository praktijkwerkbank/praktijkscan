#!/usr/bin/env python3
"""
Maakt een schermafbeelding van een pagina zoals een telefoon hem toont: 390 bij 844 punten, zonder scrollen.

Onderdeel van de Praktijkscan van Jens Kemna (praktijkwerkbank.nl).
Licentie van dit script: MIT, zie LICENSE-MIT in de hoofdmap.

Waarom een eigen script: Chrome zonder venster rekent met een scherm van minstens 500 punten breed, ook als je
--window-size=390,844 meegeeft. De afbeelding wordt dan rechts afgesneden en je beoordeelt een pagina die geen
telefoon zo laat zien. Dit script zet Chrome echt in telefoonstand (breedte, aanraakscherm, telefoonbrowser).

Gebruik:
  python3 schermafbeelding.py https://www.jouwpraktijk.nl telefoon.png
  python3 schermafbeelding.py https://www.jouwpraktijk.nl laptop.png --breed 1280 --hoog 800 --laptop
  python3 schermafbeelding.py https://www.jouwpraktijk.nl heel.png --heel     (de hele pagina, voor het nalezen)

Nodig: Python 3 op Mac of Linux, en Google Chrome, Chromium, Brave of Edge. Op Windows werkt dit script niet;
gebruik daar de telefoonweergave van de browser zelf (F12, het telefoonicoon) en maak daar een schermafbeelding.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

TELEFOON_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
               "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def vind_chrome():
    kandidaten = [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        shutil.which("google-chrome"), shutil.which("google-chrome-stable"), shutil.which("chromium"),
        shutil.which("chromium-browser"), shutil.which("chrome"), shutil.which("brave"), shutil.which("msedge"),
    ]
    for k in kandidaten:
        if k and os.path.exists(k):
            return k
    return None


class Chrome:
    """Praat met Chrome via twee pijpen (--remote-debugging-pipe): berichten in JSON, gescheiden door een nulbyte."""

    def __init__(self, pad, profiel):
        naar_r, naar_w = os.pipe()   # wij schrijven, Chrome leest op 3
        van_r, van_w = os.pipe()     # Chrome schrijft op 4, wij lezen
        # zet de uiteinden voor Chrome eerst op hoge nummers, zodat 3 en 4 vrij zijn om naartoe te kopiëren
        hoog_r, hoog_w = os.dup2(naar_r, 60), os.dup2(van_w, 61)
        os.close(naar_r); os.close(van_w)

        def koppel():
            os.dup2(60, 3)
            os.dup2(61, 4)

        self.proc = subprocess.Popen(
            [pad, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
             f"--user-data-dir={profiel}", "--remote-debugging-pipe", "about:blank"],
            preexec_fn=koppel, pass_fds=(3, 4, 60, 61), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(hoog_r); os.close(hoog_w)
        self.uit, self.inn = naar_w, van_r
        self.buffer = b""
        self.teller = 0

    def stuur(self, methode, params=None, sessie=None):
        self.teller += 1
        bericht = {"id": self.teller, "method": methode, "params": params or {}}
        if sessie:
            bericht["sessionId"] = sessie
        os.write(self.uit, json.dumps(bericht).encode() + b"\0")
        return self.wacht(lambda m: m.get("id") == self.teller)

    def wacht(self, klopt, tijd=45):
        einde = time.time() + tijd
        while time.time() < einde:
            while b"\0" in self.buffer:
                stuk, self.buffer = self.buffer.split(b"\0", 1)
                m = json.loads(stuk)
                if klopt(m):
                    if "error" in m:
                        raise RuntimeError(m["error"].get("message", "fout van Chrome"))
                    return m
            deel = os.read(self.inn, 1 << 20)
            if not deel:
                break
            self.buffer += deel
        raise TimeoutError("Chrome gaf geen antwoord.")

    def stop(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def main():
    ap = argparse.ArgumentParser(description="Schermafbeelding van een pagina in telefoonstand (Praktijkscan, Jens Kemna).")
    ap.add_argument("adres", help="het webadres, met https://")
    ap.add_argument("uit", help="bestandsnaam van de afbeelding (png)")
    ap.add_argument("--breed", type=int, default=390)
    ap.add_argument("--hoog", type=int, default=844)
    ap.add_argument("--laptop", action="store_true", help="geen telefoonstand: gewone browser op de opgegeven maat")
    ap.add_argument("--heel", action="store_true", help="de hele pagina in plaats van alleen het eerste scherm")
    ap.add_argument("--wacht", type=float, default=4.0, help="seconden wachten na het laden (cookiemelding, lettertypes)")
    a = ap.parse_args()

    if not a.adres.lower().startswith(("http://", "https://")):
        sys.exit("Geef een webadres dat met http:// of https:// begint. Andere adressen (zoals file:) opent dit script niet.")
    if os.name == "nt":
        sys.exit("Dit script werkt niet op Windows. Gebruik de telefoonweergave van je browser (F12, het telefoonicoon).")
    pad = vind_chrome()
    if not pad:
        sys.exit("Geen Chrome, Chromium, Brave of Edge gevonden.")

    with tempfile.TemporaryDirectory() as profiel:
        c = Chrome(pad, profiel)
        try:
            doel = c.stuur("Target.createTarget", {"url": "about:blank"})["result"]["targetId"]
            sessie = c.stuur("Target.attachToTarget", {"targetId": doel, "flatten": True})["result"]["sessionId"]
            c.stuur("Emulation.setDeviceMetricsOverride",
                    {"width": a.breed, "height": a.hoog, "deviceScaleFactor": 1 if a.laptop else 2, "mobile": not a.laptop}, sessie)
            if not a.laptop:
                c.stuur("Emulation.setUserAgentOverride", {"userAgent": TELEFOON_UA}, sessie)
                c.stuur("Emulation.setTouchEmulationEnabled", {"enabled": True}, sessie)
            c.stuur("Page.enable", {}, sessie)
            c.stuur("Page.navigate", {"url": a.adres}, sessie)
            try:
                c.wacht(lambda m: m.get("method") == "Page.loadEventFired", tijd=40)
            except TimeoutError:
                print("Let op: de pagina was na 40 seconden nog niet klaar met laden; de afbeelding kan onvolledig zijn.", file=sys.stderr)
            time.sleep(a.wacht)
            params = {"format": "png"}
            if a.heel:
                params["captureBeyondViewport"] = True
                maat = c.stuur("Page.getLayoutMetrics", {}, sessie)["result"].get("cssContentSize", {})
                if maat:
                    params["clip"] = {"x": 0, "y": 0, "width": maat["width"], "height": min(maat["height"], 12000), "scale": 1}
            beeld = c.stuur("Page.captureScreenshot", params, sessie)["result"]["data"]
            with open(a.uit, "wb") as f:
                f.write(base64.b64decode(beeld))
            breedte = c.stuur("Runtime.evaluate", {"expression": "document.documentElement.scrollWidth", "returnByValue": True},
                              sessie)["result"]["result"].get("value")
            print(f"Geschreven: {a.uit} ({a.breed} bij {a.hoog} punten{'' if a.laptop else ', telefoonstand'})")
            if breedte and breedte > a.breed + 2:
                print(f"Let op: de pagina is {breedte} punten breed op een scherm van {a.breed}; bezoekers moeten opzij scrollen. "
                      "Dat hoort bij 'Stuk of slordig'.", file=sys.stderr)
        finally:
            c.stop()


if __name__ == "__main__":
    main()
