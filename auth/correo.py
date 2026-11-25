"""Envío de correos de la app (recuperación de contraseña, boleta de venta)
vía Gmail SMTP. El logo se embebe como imagen inline (Content-ID) en vez de
enlazarse por URL, así se ve siempre aunque el servidor no sea público."""
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo.png"))
LOGO_CID = "logo_inkafarma"


def _construir_mensaje(asunto, destinatario, texto_plano, html):
    """Arma un correo multipart/related: alternative (texto+html) + logo
    embebido como imagen inline referenciada por `cid:logo_inkafarma`."""
    remitente = current_app.config["MAIL_DEFAULT_SENDER"]

    mensaje = MIMEMultipart("related")
    mensaje["Subject"] = asunto
    mensaje["From"] = f"Inkafarma <{remitente}>"
    mensaje["To"] = destinatario

    alternativo = MIMEMultipart("alternative")
    alternativo.attach(MIMEText(texto_plano, "plain"))
    alternativo.attach(MIMEText(html, "html"))
    mensaje.attach(alternativo)

    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo = MIMEImage(f.read())
        logo.add_header("Content-ID", f"<{LOGO_CID}>")
        logo.add_header("Content-Disposition", "inline", filename="logo.png")
        mensaje.attach(logo)

    return mensaje, remitente


def _enviar(mensaje, remitente, destinatario):
    servidor = current_app.config["MAIL_SERVER"]
    puerto = current_app.config["MAIL_PORT"]
    usuario_smtp = current_app.config["MAIL_USERNAME"]
    password_smtp = current_app.config["MAIL_PASSWORD"]

    with smtplib.SMTP(servidor, puerto, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(usuario_smtp, password_smtp)
        smtp.sendmail(remitente, destinatario, mensaje.as_string())


def _encabezado_html():
    return f"""
        <div style="background: linear-gradient(135deg, #1c8b3c, #146b2d); padding: 22px 32px; text-align:center;">
          <img src="cid:{LOGO_CID}" alt="Inkafarma" style="height:32px; background:#fff; padding:6px 12px; border-radius:8px;">
        </div>
    """


def _pie_html():
    return """
        <p style="margin:0; color:#9ca3af; font-size:11px; text-align:center; padding:16px 32px 24px;">
          Inkafarma · Sistema de Gestión de Inventario
        </p>
    """





def _plantilla_codigo(nombre, codigo):
    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f5; padding: 32px 16px;">
      <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06);">
        {_encabezado_html()}
        <div style="padding: 32px;">
          <p style="margin:0 0 4px; color:#1f2937; font-size:16px;">Hola, {nombre}:</p>
          <p style="margin:0 0 20px; color:#4b5563; font-size:14px; line-height:1.6;">
            Recibimos una solicitud para restablecer la contraseña de tu cuenta.
            Usa el siguiente código de verificación para continuar:
          </p>
          <div style="background:#f0fdf4; border:1.5px dashed #1c8b3c; border-radius:12px; padding:18px; text-align:center; margin-bottom:20px;">
            <p style="margin:0; font-size:32px; font-weight:800; letter-spacing:8px; color:#146b2d;">{codigo}</p>
          </div>
          <p style="margin:0 0 20px; color:#6b7280; font-size:13px; line-height:1.6;">
            Este código vence en <b>15 minutos</b> y solo puede usarse una vez.
          </p>
          <p style="margin:0; color:#9ca3af; font-size:12px; line-height:1.6; border-top:1px solid #eef1ef; padding-top:16px;">
            ¿No solicitaste este cambio? Ignora este correo — tu contraseña seguirá siendo la misma.
          </p>
        </div>
      </div>
    </div>
    """


def enviar_codigo_recuperacion(nombre, destinatario, codigo):
    texto_plano = (
        f"Hola {nombre},\n\n"
        f"Tu código de verificación para restablecer tu contraseña es: {codigo}\n"
        "Vence en 15 minutos.\n\n"
        "Si no solicitaste este cambio, ignora este correo."
    )
    mensaje, remitente = _construir_mensaje(
        "Código de verificación - Inkafarma", destinatario, texto_plano, _plantilla_codigo(nombre, codigo)
    )
    _enviar(mensaje, remitente, destinatario)





def _fila_producto_html(detalle):
    etiqueta_promo = (
        f'<br><span style="font-size:10px; color:#1c8b3c;">🏷️ {detalle["promocion"]}</span>'
        if detalle.get("promocion") else ""
    )
    return f"""
        <tr>
          <td style="padding:6px 0; color:#374151; font-size:13px;">{detalle["medicamento"]}{etiqueta_promo}</td>
          <td style="padding:6px 0; color:#6b7280; font-size:13px; text-align:center;">{detalle["cantidad"]}</td>
          <td style="padding:6px 0; color:#374151; font-size:13px; text-align:right;">S/ {detalle["subtotal"]:.2f}</td>
        </tr>
    """


def _plantilla_boleta(venta_dict):
    subtotal = sum(d["subtotal"] for d in venta_dict["detalles"])
    descuento = venta_dict.get("descuento") or 0
    igv = venta_dict["total"] - (subtotal - descuento)
    filas = "".join(_fila_producto_html(d) for d in venta_dict["detalles"])

    fila_descuento = (
        f'<tr><td style="color:#146b2d;">Descuento</td>'
        f'<td style="text-align:right; color:#146b2d;">- S/ {descuento:.2f}</td></tr>'
        if descuento > 0 else ""
    )
    fila_cupon = (
        f'<tr><td style="padding:2px 0;">Cupón</td>'
        f'<td style="text-align:right; color:#146b2d; font-weight:600;">{venta_dict["cupon_codigo"]}</td></tr>'
        if venta_dict.get("cupon_codigo") else ""
    )

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f5; padding: 32px 16px;">
      <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06);">
        {_encabezado_html()}
        <div style="padding: 28px 32px;">
          <p style="margin:0 0 2px; color:#1f2937; font-size:16px; font-weight:800;">¡Gracias por tu compra!</p>
          <p style="margin:0 0 20px; color:#9ca3af; font-size:12px; font-family:monospace;">Boleta N° {venta_dict["numero_venta"]}</p>

          <table style="width:100%; border-collapse:collapse; margin-bottom:16px; font-size:12px; color:#6b7280;">
            <tr><td style="padding:2px 0;">Cliente</td><td style="text-align:right; color:#374151; font-weight:600;">{venta_dict["cliente_nombre"]}</td></tr>
            <tr><td style="padding:2px 0;">Fecha</td><td style="text-align:right; color:#374151;">{venta_dict["fecha"]}</td></tr>
            <tr><td style="padding:2px 0;">Vendedor</td><td style="text-align:right; color:#374151;">{venta_dict["usuario"]}</td></tr>
            <tr><td style="padding:2px 0;">Método de pago</td><td style="text-align:right; color:#374151;">{venta_dict["metodo_pago"]}</td></tr>
            {fila_cupon}
          </table>

          <table style="width:100%; border-collapse:collapse; border-top:1px dashed #d1d5db; padding-top:8px;">
            <thead>
              <tr>
                <th style="text-align:left; font-size:11px; color:#9ca3af; padding-top:10px;">Producto</th>
                <th style="text-align:center; font-size:11px; color:#9ca3af; padding-top:10px;">Cant.</th>
                <th style="text-align:right; font-size:11px; color:#9ca3af; padding-top:10px;">Subtotal</th>
              </tr>
            </thead>
            <tbody>{filas}</tbody>
          </table>

          <div style="border-top:1px dashed #d1d5db; margin-top:8px; padding-top:10px;">
            <table style="width:100%; font-size:13px; color:#6b7280;">
              <tr><td>Subtotal</td><td style="text-align:right;">S/ {subtotal:.2f}</td></tr>
              {fila_descuento}
              <tr><td>IGV (18%)</td><td style="text-align:right;">S/ {igv:.2f}</td></tr>
              <tr><td style="font-weight:800; color:#1f2937; padding-top:4px;">Total</td>
                  <td style="text-align:right; font-weight:800; color:#146b2d; padding-top:4px;">S/ {venta_dict["total"]:.2f}</td></tr>
            </table>
          </div>
        </div>
        {_pie_html()}
      </div>
    </div>
    """


def enviar_boleta_venta(venta):
    """Envía la boleta de una venta ya registrada al correo del cliente
    (venta.cliente_email). `venta` es la instancia del modelo Venta."""
    venta_dict = venta.to_dict()

    lineas_texto = "\n".join(
        f"  {d['medicamento']} x{d['cantidad']} - S/ {d['subtotal']:.2f}" for d in venta_dict["detalles"]
    )
    texto_plano = (
        f"¡Gracias por tu compra en Inkafarma!\n\n"
        f"Boleta N° {venta_dict['numero_venta']}\n"
        f"Cliente: {venta_dict['cliente_nombre']}\n"
        f"Fecha: {venta_dict['fecha']}\n\n"
        f"Productos:\n{lineas_texto}\n\n"
        f"Total: S/ {venta_dict['total']:.2f}"
    )

    mensaje, remitente = _construir_mensaje(
        f"Boleta de venta {venta_dict['numero_venta']} - Inkafarma",
        venta.cliente_email,
        texto_plano,
        _plantilla_boleta(venta_dict),
    )
    _enviar(mensaje, remitente, venta.cliente_email)