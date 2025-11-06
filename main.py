# -*- coding: utf-8 -*-
import requests
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SEARCH_TERM = "Valle de Tobalina"
RECIPIENT_EMAIL = "valledetobalinaboletines@gmail.com"
SENDER_EMAIL = "valledetobalinaboletines@gmail.com"
APP_PASSWORD = "AQUÍ_VA_LA_CONTRASEÑA_DE_APLICACIÓN_DE_GMAIL"

BOLETINES = {
    "BOE": f"https://www.boe.es/buscar/boe.php?campo%5B0%5D=todos&operador%5B0%5D=and&valor%5B0%5D={SEARCH_TERM}",
    "BOCYL": f"https://bocyl.jcyl.es/bocyl/busquedas.do?campo=todos&texto={SEARCH_TERM}",
    "BOP Burgos": f"https://bopbur.diputaciondeburgos.es/search?search_api_fulltext={SEARCH_TERM}",
}

def buscar_boletines():
    resultados = {}
    for nombre, url in BOLETINES.items():
        try:
            r = requests.get(url, timeout=20)
            if SEARCH_TERM.lower() in r.text.lower():
                resultados[nombre] = url
        except Exception as e:
            print(f"Error al buscar en {nombre}: {e}")
            continue
    return resultados

def enviar_correo(resultados):
    fecha = datetime.date.today().strftime("%d-%m-%Y")
    asunto = f"Boletín - {fecha}"

    if resultados:
        cuerpo = "Se han encontrado publicaciones relacionadas con el Valle de Tobalina:\n\n"
        for k, v in resultados.items():
            cuerpo += f"📘 {k}: {v}\n"
    else:
        cuerpo = "No se ha encontrado ninguna publicación relacionada con el Valle de Tobalina hoy."

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    resultados = buscar_boletines()
    enviar_correo(resulta_
