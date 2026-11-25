"""
UNIDAD 2 - PROGRAMACION LOGICA
==============================
Este módulo evalúa el conjunto de reglas lógicas definidas en `reglas.pl`
(hechos, predicados, unificación, resolución, control de ejecución e
indeterminismo, tal como se ve en el sílabo).

Funcionamiento:
1. Se intenta usar el motor REAL de Prolog (SWI-Prolog) a través de la
   librería `pyswip`. Se afirman los hechos (medicamento/2, lote/4) de
   forma dinámica con los datos actuales de la base de datos y se
   consultan las reglas de `reglas.pl`.
2. Si `pyswip` o SWI-Prolog no están instalados en el equipo (lo más
   común al abrir el proyecto por primera vez), se usa automáticamente
   un motor equivalente escrito en Python puro (`_motor_fallback`) que
   reproduce exactamente la misma semántica declarativa de las reglas
   (hechos + reglas + unificación simple), para que el sistema funcione
   sin requerir instalación adicional.

En ambos casos el resultado que retornan las funciones públicas
(`evaluar_alertas`) es idéntico, de modo que el resto de la aplicación
no necesita saber qué motor se usó.
"""
import os

RUTA_REGLAS = os.path.join(os.path.dirname(__file__), "reglas.pl")


def _usar_prolog_real(medicamentos, lotes):
    """Intenta resolver las reglas usando SWI-Prolog real vía pyswip."""
    from pyswip import Prolog

    prolog = Prolog()
    prolog.consult(RUTA_REGLAS)






    list(prolog.query("retractall(medicamento(_, _))"))
    list(prolog.query("retractall(lote(_, _, _, _))"))


    for m in medicamentos:
        prolog.assertz(f"medicamento({m['id']}, {m['stock_minimo']})")


    for l in lotes:
        prolog.assertz(
            f"lote({l['id']}, {l['medicamento_id']}, {l['cantidad_actual']}, {l['dias_para_vencer']})"
        )

    stock_bajo_ids = {r["MedID"] for r in prolog.query("stock_bajo(MedID)")}
    alerta_critica_ids = {r["MedID"] for r in prolog.query("alerta_critica(MedID)")}
    vencidos_ids = {r["LoteID"] for r in prolog.query("vencido(LoteID)")}
    por_vencer_ids = {r["LoteID"] for r in prolog.query("proximo_a_vencer(LoteID)")}
    retiro_ids = {r["LoteID"] for r in prolog.query("requiere_retiro(LoteID)")}

    return _construir_resultado(
        medicamentos, lotes, stock_bajo_ids, alerta_critica_ids, vencidos_ids, por_vencer_ids, retiro_ids
    )


def _motor_fallback(medicamentos, lotes):
    """Reimplementación en Python puro de las mismas reglas declarativas
    de reglas.pl. Se usa automáticamente si SWI-Prolog/pyswip no está
    instalado, para que el sistema funcione sin dependencias externas.
    """
    lotes_por_medicamento = {}
    for l in lotes:
        lotes_por_medicamento.setdefault(l["medicamento_id"], []).append(l)

    stock_bajo_ids = set()
    alerta_critica_ids = set()
    for m in medicamentos:
        lotes_med = lotes_por_medicamento.get(m["id"], [])
        stock_vigente = sum(l["cantidad_actual"] for l in lotes_med if l["dias_para_vencer"] >= 0)
        if stock_vigente <= m["stock_minimo"]:
            stock_bajo_ids.add(m["id"])
            if any(0 <= l["dias_para_vencer"] <= 30 for l in lotes_med):
                alerta_critica_ids.add(m["id"])

    vencidos_ids = {l["id"] for l in lotes if l["dias_para_vencer"] < 0}
    por_vencer_ids = {l["id"] for l in lotes if 0 <= l["dias_para_vencer"] <= 30}
    retiro_ids = {l["id"] for l in lotes if l["dias_para_vencer"] < 0 and l["cantidad_actual"] > 0}

    return _construir_resultado(
        medicamentos, lotes, stock_bajo_ids, alerta_critica_ids, vencidos_ids, por_vencer_ids, retiro_ids
    )


def _construir_resultado(medicamentos, lotes, stock_bajo_ids, alerta_critica_ids, vencidos_ids, por_vencer_ids, retiro_ids):
    meds_por_id = {m["id"]: m for m in medicamentos}
    lotes_por_id = {l["id"]: l for l in lotes}

    return {
        "motor": "prolog" if _MOTOR_ACTIVO == "prolog" else "python (fallback equivalente)",
        "medicamentos_stock_bajo": [meds_por_id[i] for i in stock_bajo_ids if i in meds_por_id],
        "medicamentos_alerta_critica": [meds_por_id[i] for i in alerta_critica_ids if i in meds_por_id],
        "lotes_vencidos": [lotes_por_id[i] for i in vencidos_ids if i in lotes_por_id],
        "lotes_por_vencer": [lotes_por_id[i] for i in por_vencer_ids if i in lotes_por_id],
        "lotes_requieren_retiro": [lotes_por_id[i] for i in retiro_ids if i in lotes_por_id],
    }


_MOTOR_ACTIVO = None


def evaluar_alertas(medicamentos, lotes):
    """Punto de entrada público. Recibe listas de diccionarios
    (medicamentos.to_dict(), lotes.to_dict()) y retorna las alertas
    calculadas por el motor lógico (Prolog real o su equivalente)."""
    global _MOTOR_ACTIVO
    try:
        _MOTOR_ACTIVO = "prolog"
        return _usar_prolog_real(medicamentos, lotes)
    except Exception:
        _MOTOR_ACTIVO = "python"
        return _motor_fallback(medicamentos, lotes)
