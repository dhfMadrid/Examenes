"""Servicio ligero para envio de emails SMTP (stdlib smtplib).

Se configura via variables de entorno:
  SMTP_HOST      - host del servidor SMTP (default: smtp.gmail.com)
  SMTP_PORT      - puerto (default: 587, STARTTLS)
  SMTP_USER      - usuario de login SMTP
  SMTP_PASSWORD  - password / app-password SMTP
  EMAIL_FROM     - direccion desde la que se envian los emails

Sin estas variables configuradas, el envio falla silenciosamente
y se registra un warning en logs (nunca bloquea el login).
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


def enviar_otp_a(correo_to: str, otp: str) -> bool:
    """Envia un email con el codigo OTP a la direccion dada.

    Returns True si se envio correctamente, False si fallo.
    """
    # Leer configuración desde el entorno cada vez
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    puerto = int(os.getenv("SMTP_PORT", "587"))
    usuario = os.getenv("SMTP_USER", "")
    clave = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("EMAIL_FROM", "no-reply@example.com")

    logger.info("[email] smtp=%s:%d user=%s from=%s to=%s otp=%s",
                host, puerto, usuario[:6] + "..." if usuario else "(vacio)",
                from_addr, correo_to, otp)

    if not usuario or not clave:
        logger.warning(
            "[email] SMTP_USER o SMTP_PASSWORD no configurados. "
            "SMTP_USER='%s', SMTP_PASSWORD='%s'. Omitiendo envio.",
            usuario[:10] if usuario else '(vacío)',
            clave[:10] if clave else '(vacío)'
        )
        return False

    try:
        # Construir mensaje
        msg = MIMEMultipart()
        msg["From"] = from_addr          # ← usar variable local
        msg["To"] = correo_to
        msg["Subject"] = "[ExamenesULM] Tu codigo de verificacion"

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a73e8;">Codigo de verificacion</h2>
            <p>Tu codigo de seguridad es:</p>
            <h1 style="letter-spacing: 12px; color: #333; font-size: 36px;">{otp}</h1>
            <p style="color: #888; font-size: 14px;">Valido durante 5 minutos. No lo compartas con nadie.</p>
          </body>
        </html>
        """

        msg.attach(MIMEText(body_html, "html", "utf-8"))

        # Enviar usando las variables locales
        with smtplib.SMTP(host, puerto) as server:   # ← usar variables locales
            server.ehlo()
            server.starttls()
            server.login(usuario, clave)             # ← usar variables locales
            server.sendmail(from_addr, correo_to, msg.as_string())  # ← usar variables locales

        logger.info("[email] OTP enviado a %s", correo_to)
        return True

    except Exception:
        logger.exception("[email] Error al enviar email a %s", correo_to)
        return False