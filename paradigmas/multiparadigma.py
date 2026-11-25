"""
UNIDAD 3 - PROGRAMACION MULTIPARADIGMA
=======================================
Módulo de analítica de datos para el dashboard, construido con
pandas y numpy (tal como pide el temario: "Introducción a la Ciencia
de Datos - numpy / pandas").

Este archivo, junto con el resto del proyecto, evidencia el enfoque
MULTIPARADIGMA de la Unidad 3:
  - Orientado a objetos: los modelos SQLAlchemy (models.py) y las
    clases del framework Flask.
  - Procedural/estructurado: las rutas y controladores (api/*.py).
  - Funcional: paradigmas/funcional.py (map, filter, reduce, lambdas).
  - Lógico: paradigmas/logica.py + reglas.pl (Prolog).
  - Ciencia de datos: este módulo (numpy, pandas, DataFrames, arreglos).
"""
from datetime import date, datetime, timedelta

import pandas as pd
import numpy as np


def stock_por_dia_arreglo(ventas, dias=7):
    """UNIDAD 3 - Semana 13: ARREGLOS.

    Antes de las estructuras dinámicas de pandas/numpy usadas en el resto
    de este módulo, el sílabo pide demostrar el concepto clásico de
    arreglo: tamaño FIJO (declarado de antemano, no crece) y recorrido
    mediante un bucle for indexado (acceso por posición `arreglo[i]`, no
    por clave como en un diccionario).

    Calcula las unidades de stock que salieron (se vendieron) cada uno de
    los últimos `dias` días.
    """
    unidades_por_dia = [0] * dias
    etiquetas_dias = [""] * dias
    hoy = date.today()

    for i in range(dias):
        dia = hoy - timedelta(days=(dias - 1 - i))
        etiquetas_dias[i] = dia.strftime("%d/%m")

    for venta in ventas:
        fecha_venta = datetime.fromisoformat(venta["fecha"]).date()
        antiguedad = (hoy - fecha_venta).days
        indice = dias - 1 - antiguedad
        if 0 <= indice < dias:
            total_unidades_venta = 0
            for detalle in venta.get("detalles", []):
                total_unidades_venta += detalle["cantidad"]
            unidades_por_dia[indice] += total_unidades_venta

    return [
        {"dia": etiquetas_dias[i], "unidades_vendidas": unidades_por_dia[i]}
        for i in range(dias)
    ]


def dataframe_ventas(ventas):
    """Convierte la lista de ventas (dict) en un DataFrame de pandas."""
    if not ventas:
        return pd.DataFrame(columns=["id", "numero_venta", "fecha", "total", "metodo_pago"])
    df = pd.DataFrame(ventas)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def resumen_ventas(ventas):
    """Estadísticas descriptivas de ventas usando numpy (media, desviación
    estándar, máximo, mínimo) y pandas (agrupaciones por método de pago
    y por día)."""
    df = dataframe_ventas(ventas)
    if df.empty:
        return {
            "total_ventas": 0,
            "monto_total": 0,
            "ticket_promedio": 0,
            "desviacion_estandar": 0,
            "venta_maxima": 0,
            "venta_minima": 0,
            "por_metodo_pago": {},
            "ventas_por_dia": [],
        }

    totales = df["total"].to_numpy(dtype=float)

    por_metodo = df.groupby("metodo_pago")["total"].sum().round(2).to_dict()

    ventas_por_dia = (
        df.groupby(df["fecha"].dt.date)["total"]
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={"fecha": "dia", "total": "monto"})
    )
    ventas_por_dia["dia"] = ventas_por_dia["dia"].astype(str)

    return {
        "total_ventas": int(len(df)),
        "monto_total": round(float(np.sum(totales)), 2),
        "ticket_promedio": round(float(np.mean(totales)), 2),
        "desviacion_estandar": round(float(np.std(totales)), 2),
        "venta_maxima": round(float(np.max(totales)), 2),
        "venta_minima": round(float(np.min(totales)), 2),
        "por_metodo_pago": por_metodo,
        "ventas_por_dia": ventas_por_dia.to_dict(orient="records"),
    }


def resumen_inventario(lotes):
    """Estadísticas del inventario (arreglos numpy) a partir de los lotes."""
    if not lotes:
        return {
            "valor_total": 0,
            "cantidad_promedio_por_lote": 0,
            "lotes_totales": 0,
            "percentil_80_cantidad": 0,
        }

    df = pd.DataFrame(lotes)
    valores = (df["cantidad_actual"] * df["precio_compra_unitario"]).to_numpy(dtype=float)
    cantidades = df["cantidad_actual"].to_numpy(dtype=float)

    return {
        "valor_total": round(float(np.sum(valores)), 2),
        "cantidad_promedio_por_lote": round(float(np.mean(cantidades)), 2),
        "lotes_totales": int(len(df)),
        "percentil_80_cantidad": round(float(np.percentile(cantidades, 80)), 2),
    }


def top_medicamentos_por_categoria(medicamentos):
    """Usa pandas groupby para contar medicamentos activos por categoría,
    útil para las gráficas del dashboard."""
    if not medicamentos:
        return []
    df = pd.DataFrame(medicamentos)
    df["categoria"] = df["categoria"].fillna("Sin categoría")
    conteo = df.groupby("categoria").size().reset_index(name="cantidad")
    conteo = conteo.sort_values("cantidad", ascending=False)
    return conteo.to_dict(orient="records")


def proyeccion_reposicion(medicamentos):
    """Estimación simple (numpy) de cuántas unidades conviene reponer por
    medicamento: diferencia entre el doble del stock mínimo y el stock
    actual, acotada en 0."""
    if not medicamentos:
        return []
    df = pd.DataFrame(medicamentos)
    sugerido = np.maximum((df["stock_minimo"] * 2) - df["stock_total"], 0)
    df["sugerido_reponer"] = sugerido.astype(int)
    resultado = df[df["sugerido_reponer"] > 0][["nombre", "stock_total", "stock_minimo", "sugerido_reponer"]]
    return resultado.to_dict(orient="records")
