import io
import os
from datetime import datetime

import pandas as pd
from flask import Blueprint, send_file
from openpyxl.drawing.image import Image as ExcelImagen
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Image as PdfImagen, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from auth.decorators import requiere_rol
from models import Medicamento, Venta

reportes_bp = Blueprint("reportes_api", __name__, url_prefix="/api/reportes")

LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo.png"))
LOGO_RATIO = 666 / 1272


def _dataframe_ventas():
    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    filas = [{
        "N° Venta": v.numero_venta,
        "Cliente": v.cliente_nombre,
        "Vendedor": v.usuario.nombre if v.usuario else "-",
        "Sucursal": v.sucursal.nombre if v.sucursal else "-",
        "Fecha": v.fecha.strftime("%Y-%m-%d %H:%M"),
        "Método de pago": v.metodo_pago,
        "Cupón": v.cupon_codigo or "-",
        "Descuento (S/)": v.descuento or 0,
        "Total (S/)": v.total,
        "Estado": v.estado,
    } for v in ventas]
    return pd.DataFrame(filas, columns=[
        "N° Venta", "Cliente", "Vendedor", "Sucursal", "Fecha", "Método de pago", "Cupón", "Descuento (S/)", "Total (S/)", "Estado",
    ])


def _dataframe_inventario():
    medicamentos = Medicamento.query.filter_by(activo=True).order_by(Medicamento.nombre).all()
    filas = [{
        "Código": m.codigo,
        "Nombre": m.nombre,
        "Laboratorio": m.laboratorio.nombre if m.laboratorio else "-",
        "Categoría": m.categoria or "-",
        "Precio venta (S/)": m.precio_venta,
        "Stock total": m.stock_total,
        "Stock mínimo": m.stock_minimo,
    } for m in medicamentos]
    return pd.DataFrame(filas, columns=[
        "Código", "Nombre", "Laboratorio", "Categoría", "Precio venta (S/)", "Stock total", "Stock mínimo",
    ])


def _resumen_ventas(df):
    total = len(df)
    monto = df["Total (S/)"].sum() if total else 0
    return f"Total de ventas: {total}   |   Monto total: S/ {monto:,.2f}"


def _resumen_inventario(df):
    total = len(df)
    stock = int(df["Stock total"].sum()) if total else 0
    return f"Total de productos activos: {total}   |   Unidades en stock: {stock}"





def _excel(df, nombre_hoja, titulo, resumen):
    buffer = io.BytesIO()
    fila_encabezado = 5

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=nombre_hoja, index=False, startrow=fila_encabezado - 1)
        hoja = writer.sheets[nombre_hoja]
        ultima_columna = get_column_letter(len(df.columns))

        if os.path.exists(LOGO_PATH):
            logo = ExcelImagen(LOGO_PATH)
            logo.width, logo.height = 130, round(130 * LOGO_RATIO)
            hoja.add_image(logo, "A1")

        hoja.merge_cells(f"C1:{ultima_columna}2")
        celda_titulo = hoja["C1"]
        celda_titulo.value = titulo
        celda_titulo.font = Font(size=16, bold=True, color="146B2D")
        celda_titulo.alignment = Alignment(vertical="center")

        hoja.merge_cells(f"C3:{ultima_columna}3")
        celda_resumen = hoja["C3"]
        celda_resumen.value = resumen
        celda_resumen.font = Font(size=10, italic=True, color="6B7280")

        lado = Side(style="thin", color="D1D5DB")
        borde = Border(left=lado, right=lado, top=lado, bottom=lado)
        relleno_encabezado = PatternFill("solid", fgColor="1C8B3C")
        relleno_par = PatternFill("solid", fgColor="F4F7F5")

        for i, columna in enumerate(df.columns, start=1):
            celda = hoja.cell(row=fila_encabezado, column=i)
            celda.fill = relleno_encabezado
            celda.font = Font(bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center")
            celda.border = borde

            max_contenido = df[columna].astype(str).map(len).max() if len(df) else 0
            ancho = min(40, max(12, len(columna), max_contenido) + 4)
            hoja.column_dimensions[get_column_letter(i)].width = ancho

        for fila_idx in range(len(df)):
            for col_idx in range(1, len(df.columns) + 1):
                celda = hoja.cell(row=fila_encabezado + 1 + fila_idx, column=col_idx)
                celda.border = borde
                if fila_idx % 2 == 1:
                    celda.fill = relleno_par

        hoja.freeze_panes = hoja.cell(row=fila_encabezado + 1, column=1)
        hoja.auto_filter.ref = f"A{fila_encabezado}:{ultima_columna}{fila_encabezado + len(df)}"
        hoja.sheet_view.showGridLines = False

    buffer.seek(0)
    return buffer





def _pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#9ca3af"))
    canvas.drawString(36, 20, "Inkafarma · Sistema de Gestión de Inventario")
    canvas.drawRightString(doc.pagesize[0] - 36, 20, f"Página {doc.page}")
    canvas.restoreState()


def _pdf(titulo, df, resumen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=30, bottomMargin=40, leftMargin=36, rightMargin=36)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloReporte", parent=estilos["Title"], fontSize=18,
                                    textColor=colors.HexColor("#146b2d"), spaceAfter=2, alignment=0)
    estilo_fecha = ParagraphStyle("FechaReporte", parent=estilos["Normal"], textColor=colors.HexColor("#6b7280"))
    estilo_resumen = ParagraphStyle("ResumenReporte", parent=estilos["Normal"], fontSize=10,
                                     textColor=colors.HexColor("#374151"))

    encabezado_texto = [Paragraph(titulo, estilo_titulo),
                         Paragraph(datetime.now().strftime("Generado el %d/%m/%Y %H:%M"), estilo_fecha)]

    if os.path.exists(LOGO_PATH):
        logo = PdfImagen(LOGO_PATH, width=90, height=90 * LOGO_RATIO)
        encabezado = Table([[logo, encabezado_texto]], colWidths=[105, None])
    else:
        encabezado = Table([[encabezado_texto]])
    encabezado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))

    elementos = [
        encabezado,
        Spacer(1, 8),
        HRFlowable(width="100%", color=colors.HexColor("#1c8b3c"), thickness=1.5),
        Spacer(1, 12),
        Paragraph(resumen, estilo_resumen),
        Spacer(1, 12),
    ]

    datos = [list(df.columns)] + df.astype(str).values.tolist()
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c8b3c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla)

    doc.build(elementos, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    buffer.seek(0)
    return buffer





@reportes_bp.route("/ventas/excel", methods=["GET"])
@requiere_rol("Administrador")
def ventas_excel():
    df = _dataframe_ventas()
    buffer = _excel(df, "Ventas", "Reporte de Ventas - Inkafarma", _resumen_ventas(df))
    nombre = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buffer, as_attachment=True, download_name=nombre,
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@reportes_bp.route("/ventas/pdf", methods=["GET"])
@requiere_rol("Administrador")
def ventas_pdf():
    df = _dataframe_ventas()
    buffer = _pdf("Reporte de Ventas - Inkafarma", df, _resumen_ventas(df))
    nombre = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre, mimetype="application/pdf")


@reportes_bp.route("/inventario/excel", methods=["GET"])
@requiere_rol("Administrador")
def inventario_excel():
    df = _dataframe_inventario()
    buffer = _excel(df, "Inventario", "Reporte de Inventario - Inkafarma", _resumen_inventario(df))
    nombre = f"reporte_inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buffer, as_attachment=True, download_name=nombre,
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@reportes_bp.route("/inventario/pdf", methods=["GET"])
@requiere_rol("Administrador")
def inventario_pdf():
    df = _dataframe_inventario()
    buffer = _pdf("Reporte de Inventario - Inkafarma", df, _resumen_inventario(df))
    nombre = f"reporte_inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre, mimetype="application/pdf")