"""
UNIDAD 1 - PROGRAMACIÓN FUNCIONAL
==================================
Este módulo aplica explícitamente los conceptos de la Unidad 1 del sílabo:

- Programas como funciones / definición declarativa de funciones.
- Valores inmutables: ninguna función modifica las listas/diccionarios que
  recibe; siempre construye y retorna estructuras nuevas.
- Funciones anónimas (lambda).
- Funciones como parámetros y funciones de orden superior (map, filter,
  reduce, sorted con key, función `componer`).
- Funciones genéricas y recursión.

Todas las funciones de este archivo son PURAS: para la misma entrada
siempre retornan la misma salida y no producen efectos secundarios
(no acceden a la base de datos ni al estado global). Los datos de entrada
son listas de diccionarios "planos" obtenidos previamente desde los modelos
(ver models.py -> to_dict()).
"""
from functools import reduce
from datetime import date






def componer(*funciones):
    """Función de orden superior: compone varias funciones en un pipeline.
    componer(f, g, h)(x) == f(g(h(x)))
    """
    return reduce(lambda f, g: lambda x: f(g(x)), funciones)


def mapear(funcion, coleccion):
    """Envoltura declarativa sobre map(), retorna una lista nueva (inmutable)."""
    return list(map(funcion, coleccion))


def filtrar(predicado, coleccion):
    """Envoltura declarativa sobre filter()."""
    return list(filter(predicado, coleccion))






def calcular_valor_total_inventario(lotes):
    """Calcula el valor monetario total del inventario usando reduce().
    lotes: lista de dicts con 'cantidad_actual' y 'precio_compra_unitario'.
    """
    return reduce(
        lambda acumulado, lote: acumulado + (lote["cantidad_actual"] * lote["precio_compra_unitario"]),
        lotes,
        0.0,
    )


def filtrar_lotes_por_vencer(lotes, dias_limite=30):
    """Retorna únicamente los lotes cuyo vencimiento está a <= dias_limite,
    usando una función anónima (lambda) como predicado."""
    return filtrar(lambda lote: 0 <= lote["dias_para_vencer"] <= dias_limite, lotes)


def filtrar_lotes_vencidos(lotes):
    return filtrar(lambda lote: lote["dias_para_vencer"] < 0, lotes)


def agrupar_por_categoria(medicamentos):
    """Agrupa medicamentos por categoría usando reduce() (sin mutar la entrada)."""

    def acumular(diccionario, medicamento):
        categoria = medicamento.get("categoria") or "Sin categoría"
        nuevo = dict(diccionario)
        nuevo[categoria] = nuevo.get(categoria, []) + [medicamento]
        return nuevo

    return reduce(acumular, medicamentos, {})


def calcular_stock_critico(medicamentos):
    """Devuelve los medicamentos cuyo stock_total está por debajo del mínimo,
    ordenados del más crítico al menos crítico (funciones como parámetro de sorted)."""
    criticos = filtrar(lambda m: m["stock_total"] <= m["stock_minimo"], medicamentos)
    return sorted(criticos, key=lambda m: m["stock_total"] - m["stock_minimo"])


def top_n_productos_mas_vendidos(detalles_venta, n=5):
    """A partir del detalle histórico de ventas, calcula los N productos con
    mayor cantidad vendida. Usa reduce para agrupar y sorted (orden superior)
    para el ranking."""

    def acumular(diccionario, detalle):
        nombre = detalle["medicamento"]
        nuevo = dict(diccionario)
        nuevo[nombre] = nuevo.get(nombre, 0) + detalle["cantidad"]
        return nuevo

    totales = reduce(acumular, detalles_venta, {})
    ranking = sorted(totales.items(), key=lambda item: item[1], reverse=True)
    return [{"medicamento": nombre, "cantidad_vendida": cantidad} for nombre, cantidad in ranking[:n]]


def calcular_totales_venta(detalles):
    """Calcula subtotal, IGV (18%) y total de una venta a partir de sus
    detalles, mediante map + reduce (sin mutar la entrada)."""
    subtotales = mapear(lambda d: d["cantidad"] * d["precio_unitario"], detalles)
    subtotal = reduce(lambda a, b: a + b, subtotales, 0.0)
    igv = round(subtotal * 0.18, 2)
    total = round(subtotal + igv, 2)
    return {"subtotal": round(subtotal, 2), "igv": igv, "total": total}


def calcular_descuento_por_volumen(monto, tramos=((500, 0.10), (200, 0.05), (0, 0.0))):
    """Calcula un descuento aplicando el primer tramo que corresponda,
    usando RECURSIÓN sobre la lista de tramos (monto_minimo, porcentaje)."""
    if not tramos:
        return 0.0
    minimo, porcentaje = tramos[0]
    if monto >= minimo:
        return round(monto * porcentaje, 2)
    return calcular_descuento_por_volumen(monto, tramos[1:])


def generar_alerta(medicamento, umbral_dias=30):
    """Función pura que, dado un medicamento (con su lote más próximo a
    vencer ya calculado), retorna un diccionario de alerta declarativo."""
    nivel = "OK"
    if medicamento.get("stock_total", 0) <= medicamento.get("stock_minimo", 0):
        nivel = "STOCK_BAJO"
    dias = medicamento.get("dias_para_vencer")
    if dias is not None and dias < 0:
        nivel = "VENCIDO"
    elif dias is not None and 0 <= dias <= umbral_dias:
        nivel = "POR_VENCER" if nivel == "OK" else nivel
    return {"medicamento": medicamento.get("nombre"), "nivel": nivel}


def _enriquecer_con_vencimiento(lotes):
    """Función de orden superior: dados los lotes, retorna una función que
    le agrega a un medicamento el campo 'dias_para_vencer' de su lote más
    próximo a vencer (o None si no tiene lotes)."""

    def enriquecer(medicamento):
        lotes_del_medicamento = filtrar(lambda l: l["medicamento_id"] == medicamento["id"], lotes)
        dias = [l["dias_para_vencer"] for l in lotes_del_medicamento]
        return {**medicamento, "dias_para_vencer": min(dias) if dias else None}

    return enriquecer


def generar_alertas_funcionales(medicamentos, lotes):
    """Alertas por medicamento (nivel OK/STOCK_BAJO/POR_VENCER/VENCIDO).
    Usa componer() para encadenar el enriquecimiento de cada medicamento
    (con los datos de su lote más próximo a vencer) con generar_alerta(),
    y descarta las alertas en nivel 'OK'."""
    generar = componer(generar_alerta, _enriquecer_con_vencimiento(lotes))
    alertas = mapear(generar, medicamentos)
    return filtrar(lambda a: a["nivel"] != "OK", alertas)


def pipeline_reporte_inventario(medicamentos, lotes):
    """Ejemplo de composición funcional (pipeline): encadena varias
    funciones puras para construir el reporte final de inventario."""
    valor_total = calcular_valor_total_inventario(lotes)
    por_categoria = agrupar_por_categoria(medicamentos)
    criticos = calcular_stock_critico(medicamentos)
    por_vencer = filtrar_lotes_por_vencer(lotes)
    vencidos = filtrar_lotes_vencidos(lotes)
    alertas_funcionales = generar_alertas_funcionales(medicamentos, lotes)
    return {
        "valor_total_inventario": round(valor_total, 2),
        "medicamentos_por_categoria": {k: len(v) for k, v in por_categoria.items()},
        "stock_critico": criticos,
        "lotes_por_vencer": por_vencer,
        "lotes_vencidos": vencidos,
        "alertas_funcionales": alertas_funcionales,
    }
