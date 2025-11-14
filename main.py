# -*- coding: utf-8 -*-
import os
import requests
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyPDF2 import PdfReader
from io import BytesIO

# Config desde secrets (GitHub Actions)
SENDER = os.getenv("EMAIL_REMITENTE")
PASSWORD = os.getenv("EMAIL_PASSWORD")
TO = os.getenv("EMAIL_DESTINO")

SEARCH = "valle de tobalina"   # buscamos en minúsculas

# Funciones para construir/obtener URLs

def boe_sumario_url_for_date(d):
    # Usamos la API JSON del BOE para obtener el número del BOE del día y construir la URL PDF
    yyyy = d.year
    mm = f"{d.month:02d}"
    dd = f"{d.day:02d}"
    api = f"https://www.boe.es/boe/dias/{yyyy}/{mm}/{dd}/index.php?format=json"
    try:
        r = requests.get(api, timeout=10)
        r.raise_for_status()
        j = r.json()
        num = j.get("numBOE") or j.get("num")
        if not num:
            return None
        # num puede venir como string "274" o similar
        return f"https://www.boe.es/boe/dias/{yyyy}/{mm}/{dd}/pdfs/BOE-S-{yyyy}-{num}.pdf"
    except Exception:
        return None

def bocyl_sumario_url_for_date(d):
    yyyy = d.year
    mm = f"{d.month:02d}"
    dd = f"{d.day:02d}"
    # Patrón que me diste:
    return f"https://bocyl.jcyl.es/boletines/{yyyy}/{mm}/{dd}/pdf/BOCYL-S-{dd}{mm}{yyyy}.pdf"

def try_bop_sumario_for_date(d):
    """
    BOP Burgos no tiene API pública de número. Intentamos localizar el PDF
    probando números plausibles. Primero probamos un rango cercano al día del año,
    si no, buscamos en 1..400.
    Retorna la URL encontrada o None.
    """
    year = d.year
    # primera aproximación: day of year
    start = d.timetuple().tm_yday
    candidates = list(range(start-5, start+6))  # +/-5
    # añadir fallback 1..400 sin negativos
    candidates += [n for n in range(1, 401) if n not in candidates]
    base_prefix = "http://bopbur.diputaciondeburgos.es/sites/default/files/private/publicado"
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; BoletinesBot/1.0)"})
    for n in candidates:
        if n <= 0:
            continue
        folder = f"bopbur-{year}-{n}"
        url = f"{base_prefix}/{folder}/{folder}-sumario.pdf"
        try:
            # HEAD para comprobar existencia rápido
            h = session.head(url, timeout=8, allow_redirects=True)
            if h.status_code == 200 and 'application/pdf' in h.headers.get('Content-Type',''):
                return url
        except Exception:
            continue
    return None

# Pdf text extraction (intenta PyPDF2)
def pdf_text_from_url(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        f = BytesIO(r.content)
        reader = PdfReader(f)
        txt = []
        for p in reader.pages:
            try:
                page_text = p.extract_text() or ""
            except Exception:
                page_text = ""
            txt.append(page_text)
        return "\n".join(txt).lower()
    except Exception:
        return ""

# Comprueba cada boletín y devuelve (url, found_bool)
def check_boe(d):
    url = boe_sumario_url_for_date(d)
    if not url:
        return None, False
    text = pdf_text_from_url(url)
    found = SEARCH in text
    return url, found

def check_bocyl(d):
    url = bocyl_sumario_url_for_date(d)
    text = pdf_text_from_url(url)
    found = SEARCH in text
    return url, found

def check_bop(d):
    url = try_bop_sumario_for_date(d)
    if not url:
        return None, False
    text = pdf_text_from_url(url)
    found = SEARCH in text
    return url, found

# Construye y envía correo (texto simple)
def send_report(date, results):
    fecha = date.strftime("%d-%m-%Y")
    subject = f"Boletín - {fecha}"
    body = f"Informe de sumarios para {fecha}\n\n"
    for name, tup in results.items():
        url, found = tup
        body += f"{name}:\n"
        if url:
            body += f"- Enlace: {url}\n"
        else:
            body += "- Enlace: NO DISPONIBLE\n"
        body += f"- Menciona 'Valle de Tobalina': {'SÍ' if found else 'NO'}\n\n"

    # Enviar por SMTP (Gmail)
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, PASSWORD)
        server.send_message(msg)

def main():
    today = datetime.date.today()
    results = {}
    # BOE
    boe_url, boe_found = check_boe(today)
    results["BOE"] = (boe_url, boe_found)
    # BOCYL
    bocyl_url, bocyl_found = check_bocyl(today)
    results["BOCYL"] = (bocyl_url, bocyl_found)
    # BOP Burgos
    bop_url, bop_found = check_bop(today)
    results["BOP Burgos"] = (bop_url, bop_found)

    send_report(today, results)

if __name__ == "__main__":
    main()
