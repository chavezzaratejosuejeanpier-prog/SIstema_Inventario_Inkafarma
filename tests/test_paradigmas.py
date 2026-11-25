"""Tests de las funciones puras de paradigmas/ (no requieren base de datos
ni contexto de Flask: son funciones que solo reciben y devuelven datos)."""
from paradigmas import funcional, logica, multiparadigma


def test_calcular_totales_venta_aplica_igv_18_por_ciento():
    detalles = [{"cantidad": 2, "precio_unitario": 10.0}, {"cantidad": 1, "precio_unitario": 5.0}]
    totales = funcional.calcular_totales_venta(detalles)
    assert totales["subtotal"] == 25.0
    assert totales["igv"] == 4.5
    assert totales["total"] == 29.5


def test_calcular_totales_venta_no_muta_la_lista_de_entrada():
    detalles = [{"cantidad": 2, "precio_unitario": 10.0}]
    copia = [dict(d) for d in detalles]
    funcional.calcular_totales_venta(detalles)
    assert detalles == copia


def test_top_n_productos_mas_vendidos_ordena_de_mayor_a_menor():
    detalles = [
        {"medicamento": "Paracetamol", "cantidad": 5},
        {"medicamento": "Ibuprofeno", "cantidad": 10},
        {"medicamento": "Paracetamol", "cantidad": 3},
    ]
    top = funcional.top_n_productos_mas_vendidos(detalles, n=2)
    assert top[0] == {"medicamento": "Ibuprofeno", "cantidad_vendida": 10}
    assert top[1] == {"medicamento": "Paracetamol", "cantidad_vendida": 8}


def test_calcular_valor_total_inventario():
    lotes = [
        {"cantidad_actual": 10, "precio_compra_unitario": 2.0},
        {"cantidad_actual": 5, "precio_compra_unitario": 4.0},
    ]
    assert funcional.calcular_valor_total_inventario(lotes) == 40.0


def test_filtrar_lotes_por_vencer_respeta_el_limite_de_dias():
    lotes = [
        {"dias_para_vencer": 10},
        {"dias_para_vencer": 45},
        {"dias_para_vencer": -3},
    ]
    resultado = funcional.filtrar_lotes_por_vencer(lotes, dias_limite=30)
    assert resultado == [{"dias_para_vencer": 10}]


def test_calcular_stock_critico_ordena_del_mas_critico_al_menos():
    medicamentos = [
        {"nombre": "A", "stock_total": 5, "stock_minimo": 10},
        {"nombre": "B", "stock_total": 0, "stock_minimo": 10},
        {"nombre": "C", "stock_total": 20, "stock_minimo": 10},
    ]
    criticos = funcional.calcular_stock_critico(medicamentos)
    assert [m["nombre"] for m in criticos] == ["B", "A"]


def test_calcular_descuento_por_volumen_usa_recursion_sobre_tramos():
    assert funcional.calcular_descuento_por_volumen(600) == 60.0
    assert funcional.calcular_descuento_por_volumen(250) == 12.5
    assert funcional.calcular_descuento_por_volumen(50) == 0.0


def test_evaluar_alertas_detecta_stock_bajo_y_vencidos():
    medicamentos = [{"id": 1, "nombre": "Paracetamol", "stock_total": 2, "stock_minimo": 10}]
    lotes = [{"id": 1, "medicamento_id": 1, "numero_lote": "L1", "dias_para_vencer": -1,
              "cantidad_actual": 2, "medicamento": "Paracetamol"}]
    resultado = logica.evaluar_alertas(medicamentos, lotes)
    assert "medicamentos_stock_bajo" in resultado
    assert "lotes_vencidos" in resultado
    assert "motor" in resultado


def test_resumen_ventas_con_lista_vacia():
    resumen = multiparadigma.resumen_ventas([])
    assert resumen["total_ventas"] == 0
    assert resumen["monto_total"] == 0


def test_resumen_ventas_calcula_totales():
    ventas = [
        {"id": 1, "numero_venta": "BV-1", "fecha": "2026-01-01T10:00:00", "total": 100.0, "metodo_pago": "Efectivo"},
        {"id": 2, "numero_venta": "BV-2", "fecha": "2026-01-02T10:00:00", "total": 50.0, "metodo_pago": "Tarjeta"},
    ]
    resumen = multiparadigma.resumen_ventas(ventas)
    assert resumen["total_ventas"] == 2
    assert resumen["monto_total"] == 150.0