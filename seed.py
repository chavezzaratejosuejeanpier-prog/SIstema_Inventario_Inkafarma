"""
Script de inicialización de la base de datos.
Crea las tablas y carga datos de ejemplo para poder probar el sistema
de inmediato: roles, usuarios, sucursales, laboratorios, medicamentos,
lotes, compras, promociones y ventas reales (registradas con la misma
lógica FEFO que el punto de venta).

Uso:
    python seed.py
"""
from datetime import date, datetime, timedelta

from app import app
from extensions import db
from models import (
    Compra, DetalleCompra, Laboratorio, Lote, Medicamento,
    Promocion, RegistroAuditoria, Rol, Sucursal, Usuario, Venta,
)


ROLES_DATA = [
    ("Administrador", "Acceso total al sistema: usuarios, laboratorios, medicamentos, lotes, compras y ventas."),
    ("Cajero", "Registra ventas en el punto de venta y consulta stock/alertas de vencimiento."),
]

SUCURSALES_DATA = [
    ("Sucursal Principal", "Casa Matriz - Av. España 1234, Lima"),
    ("Sucursal Miraflores", "Av. Larco 890, Miraflores, Lima"),
    ("Sucursal San Isidro", "Av. Presidente Kennedy 1990, San Isidro, Lima"),
]

USUARIOS_DATA = [
    ("Administrador General", "admin@inkafarma.pe", "admin123", "Administrador", None),
    ("Luis Cajero", "cajero@inkafarma.pe", "cajero123", "Cajero", "Sucursal Principal"),
    ("María Cajera", "maria.cajera@inkafarma.pe", "cajero123", "Cajero", "Sucursal Miraflores"),
    ("Carlos Cajero", "carlos.cajero@inkafarma.pe", "cajero123", "Cajero", "Sucursal San Isidro"),
]

LABORATORIOS_DATA = [
    ("Laboratorios Bagó", "20100123456", "01-4567890", "contacto@bago.com.pe", "Av. Argentina 2350, Lima"),
    ("Farmindustria S.A.", "20200234567", "01-2345678", "ventas@farmindustria.pe", "Av. Colonial 1450, Lima"),
    ("Genfar Perú", "20300345678", "01-3456789", "pedidos@genfar.pe", "Av. La Molina 890, Lima"),
]

MEDICAMENTOS_DATA = [
    ("MED-0001", "Paracetamol 500mg x100", "Laboratorios Bagó", "Analgésicos", "Tabletas", "Caja", 8.5, 15.9, False, 20),
    ("MED-0002", "Ibuprofeno 400mg x30", "Farmindustria S.A.", "Antiinflamatorios", "Tabletas", "Caja", 6.2, 12.5, False, 15),
    ("MED-0003", "Amoxicilina 500mg x21", "Genfar Perú", "Antibióticos", "Cápsulas", "Caja", 9.0, 18.0, True, 10),
    ("MED-0004", "Loratadina 10mg x20", "Laboratorios Bagó", "Antialérgicos", "Tabletas", "Caja", 5.0, 10.5, False, 15),
    ("MED-0005", "Omeprazol 20mg x28", "Farmindustria S.A.", "Gastrointestinal", "Cápsulas", "Caja", 7.8, 16.0, False, 12),
    ("MED-0006", "Amoxicilina + Ácido Clavulánico 875mg x14", "Genfar Perú", "Antibióticos", "Tabletas", "Caja", 22.0, 39.9, True, 8),
    ("MED-0007", "Salbutamol Inhalador 100mcg", "Farmindustria S.A.", "Respiratorio", "Inhalador", "Unidad", 14.0, 27.9, True, 10),
    ("MED-0008", "Vitamina C 1g x20 efervescente", "Laboratorios Bagó", "Vitaminas", "Tabletas", "Caja", 10.5, 19.9, False, 25),
    ("MED-0009", "Diclofenaco 50mg x20", "Farmindustria S.A.", "Antiinflamatorios", "Tabletas", "Caja", 5.5, 11.9, False, 18),
    ("MED-0010", "Celecoxib 200mg x10", "Genfar Perú", "Antiinflamatorios", "Cápsulas", "Caja", 12.0, 24.9, True, 8),
    ("MED-0011", "Azitromicina 500mg x3", "Laboratorios Bagó", "Antibióticos", "Tabletas", "Caja", 11.5, 22.9, True, 8),
    ("MED-0012", "Ciprofloxacino 500mg x10", "Genfar Perú", "Antibióticos", "Tabletas", "Caja", 8.8, 17.5, True, 10),
    ("MED-0013", "Cetirizina 10mg x10", "Laboratorios Bagó", "Antialérgicos", "Tabletas", "Caja", 4.2, 9.5, False, 20),
    ("MED-0014", "Ranitidina 150mg x20", "Farmindustria S.A.", "Gastrointestinal", "Tabletas", "Caja", 5.5, 11.5, False, 18),
    ("MED-0015", "Metformina 850mg x30", "Genfar Perú", "Diabetes", "Tabletas", "Caja", 6.8, 13.9, True, 15),
    ("MED-0016", "Losartán 50mg x30", "Farmindustria S.A.", "Cardiovascular", "Tabletas", "Caja", 9.5, 19.5, True, 12),
    ("MED-0017", "Enalapril 10mg x30", "Laboratorios Bagó", "Cardiovascular", "Tabletas", "Caja", 7.2, 14.9, True, 12),
    ("MED-0018", "Guayacolato + Ambroxol jarabe 120ml", "Farmindustria S.A.", "Respiratorio", "Jarabe", "Frasco", 7.5, 15.5, False, 15),
    ("MED-0019", "Vitamina D3 2000 UI x30", "Laboratorios Bagó", "Vitaminas", "Cápsulas", "Caja", 13.0, 26.9, False, 15),
    ("MED-0020", "Electrolitos orales x10 sobres", "Genfar Perú", "Hidratación", "Polvo", "Sobre", 3.5, 7.5, False, 30),
]


LOTES_DATA = [
    ("MED-0001", "LT-1001", "Sucursal Principal", 365, 200, 200, 8.5),
    ("MED-0001", "LT-1002", "Sucursal Principal", 15, 50, 12, 8.5),
    ("MED-0002", "LT-2001", "Sucursal Principal", 200, 100, 80, 6.2),
    ("MED-0005", "LT-5001", "Sucursal Principal", 300, 150, 150, 7.8),
    ("MED-0007", "LT-7001", "Sucursal Principal", 400, 40, 40, 14.0),
    ("MED-0003", "LT-3002", "Sucursal Miraflores", 180, 60, 60, 9.0),
    ("MED-0004", "LT-4001", "Sucursal Miraflores", 10, 30, 5, 5.0),
    ("MED-0008", "LT-8001", "Sucursal Miraflores", 90, 100, 90, 10.5),
    ("MED-0003", "LT-3001", "Sucursal San Isidro", -5, 40, 10, 9.0),
    ("MED-0006", "LT-6001", "Sucursal San Isidro", 25, 20, 3, 22.0),
    ("MED-0009", "LT-9001", "Sucursal Principal", 240, 60, 45, 5.5),
    ("MED-0010", "LT-10001", "Sucursal Principal", 20, 30, 8, 12.0),
    ("MED-0011", "LT-11001", "Sucursal Miraflores", 300, 40, 40, 11.5),
    ("MED-0012", "LT-12001", "Sucursal Miraflores", 150, 50, 35, 8.8),
    ("MED-0013", "LT-13001", "Sucursal Principal", 400, 80, 70, 4.2),
    ("MED-0014", "LT-14001", "Sucursal San Isidro", 180, 60, 50, 5.5),
    ("MED-0015", "LT-15001", "Sucursal San Isidro", 350, 90, 60, 6.8),
    ("MED-0016", "LT-16001", "Sucursal Principal", 260, 45, 42, 9.5),
    ("MED-0017", "LT-17001", "Sucursal Miraflores", 210, 40, 30, 7.2),
    ("MED-0018", "LT-18001", "Sucursal San Isidro", 120, 70, 55, 7.5),
    ("MED-0019", "LT-19001", "Sucursal Principal", 500, 50, 48, 13.0),
    ("MED-0020", "LT-20001", "Sucursal Miraflores", 90, 100, 85, 3.5),
]


COMPRAS_DATA = [
    (20, "Genfar Perú", "Sucursal Principal", "A", [
        ("MED-0001", "LT-C-1001", 400, 100, 8.5),
        ("MED-0003", "LT-C-1002", 200, 50, 9.0),
    ]),
    (12, "Farmindustria S.A.", "Sucursal Miraflores", "B", [
        ("MED-0002", "LT-C-2001", 250, 80, 6.2),
        ("MED-0005", "LT-C-2002", 320, 60, 7.8),
    ]),
    (9, "Genfar Perú", "Sucursal San Isidro", "C", [
        ("MED-0003", "LT-C-3003", 220, 40, 9.0),
    ]),
    (6, "Laboratorios Bagó", "Sucursal Miraflores", "D", [
        ("MED-0004", "LT-C-4001", 180, 60, 5.0),
        ("MED-0008", "LT-C-4002", 150, 50, 10.5),
    ]),
]

PROMOCIONES_DATA = [
    ("Descuento Paracetamol 15%", "porcentaje", "MED-0001", None, 15, None, None, None),
    ("Cupón SALUD10", "cupon", None, None, 10, None, None, "SALUD10"),
    ("3x2 Vitamina C", "nxm", "MED-0008", "Sucursal Miraflores", None, 3, 2, None),
]


def _crear_venta(client, usuario, sucursal, items, dias_atras, cliente, metodo="Efectivo",
                 referencia="", cupon=None):
    """Registra una venta con la API real (FEFO, promociones y descuentos)."""
    with client.session_transaction() as sesion:
        sesion["usuario_id"] = usuario.id
        sesion["usuario_nombre"] = usuario.nombre
        sesion["rol"] = "Administrador" if usuario.rol.nombre == "Administrador" else "Cajero"
        sesion["sucursal_id"] = usuario.sucursal_id
        sesion["sucursal_nombre"] = sucursal.nombre if sucursal else None

    payload = {
        "cliente_nombre": cliente,
        "metodo_pago": metodo,
        "referencia_pago": referencia,
        "items": items,
    }
    if cupon:
        payload["cupon"] = cupon

    respuesta = client.post("/api/ventas", json=payload)
    if respuesta.status_code != 201:
        raise RuntimeError(f"No se pudo crear la venta de prueba: {respuesta.status_code} {respuesta.get_json()}")

    venta = Venta.query.order_by(Venta.id.desc()).first()
    venta.fecha = datetime.utcnow() - timedelta(days=dias_atras)
    db.session.commit()
    return venta


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()
        hoy = date.today()


        roles = {}
        for nombre, descripcion in ROLES_DATA:
            rol = Rol(nombre=nombre, descripcion=descripcion)
            db.session.add(rol)
            roles[nombre] = rol
        db.session.flush()


        sucursales = {}
        for nombre, direccion in SUCURSALES_DATA:
            sucursal = Sucursal(nombre=nombre, direccion=direccion, telefono="01-5550100", activo=True)
            db.session.add(sucursal)
            sucursales[nombre] = sucursal
        db.session.flush()


        usuarios = {}
        for nombre, email, password, rol_nombre, sucursal_nombre in USUARIOS_DATA:
            usuario = Usuario(
                nombre=nombre,
                email=email,
                rol_id=roles[rol_nombre].id,
                sucursal_id=sucursales[sucursal_nombre].id if sucursal_nombre else None,
                activo=True,
            )
            usuario.set_password(password)
            db.session.add(usuario)
            usuarios[email] = usuario
        db.session.flush()


        laboratorios = {}
        for nombre, ruc, telefono, email, direccion in LABORATORIOS_DATA:
            laboratorio = Laboratorio(
                nombre=nombre, ruc=ruc, telefono=telefono, email=email, direccion=direccion, activo=True
            )
            db.session.add(laboratorio)
            laboratorios[nombre] = laboratorio
        db.session.flush()


        medicamentos = {}
        for codigo, nombre, laboratorio, categoria, presentacion, unidad, precio_compra, \
                precio_venta, receta, minimo in MEDICAMENTOS_DATA:
            medicamento = Medicamento(
                codigo=codigo, nombre=nombre, laboratorio_id=laboratorios[laboratorio].id,
                categoria=categoria, presentacion=presentacion, unidad_medida=unidad,
                precio_compra=precio_compra, precio_venta=precio_venta,
                requiere_receta=receta, stock_minimo=minimo, activo=True,
            )
            db.session.add(medicamento)
            medicamentos[codigo] = medicamento
        db.session.flush()


        for codigo, numero, sucursal, dias, inicial, actual, precio in LOTES_DATA:
            db.session.add(Lote(
                medicamento_id=medicamentos[codigo].id,
                sucursal_id=sucursales[sucursal].id,
                numero_lote=numero,
                fecha_fabricacion=hoy - timedelta(days=100),
                fecha_vencimiento=hoy + timedelta(days=dias),
                cantidad_inicial=inicial,
                cantidad_actual=actual,
                precio_compra_unitario=precio,
            ))


        auditoria_compras = []
        for dias_atras, laboratorio, sucursal, prefijo, items in COMPRAS_DATA:
            compra = Compra(
                numero_compra=f"OC-{prefijo}-2026",
                laboratorio_id=laboratorios[laboratorio].id,
                sucursal_id=sucursales[sucursal].id,
                usuario_id=usuarios["admin@inkafarma.pe"].id,
                fecha=datetime.utcnow() - timedelta(days=dias_atras),
                total=0,
                estado="Completada",
            )
            db.session.add(compra)
            db.session.flush()

            total = 0.0
            for codigo, numero, dias, cantidad, precio in items:
                lote = Lote(
                    medicamento_id=medicamentos[codigo].id,
                    sucursal_id=sucursales[sucursal].id,
                    numero_lote=numero,
                    fecha_fabricacion=hoy - timedelta(days=30),
                    fecha_vencimiento=hoy + timedelta(days=dias),
                    cantidad_inicial=cantidad,
                    cantidad_actual=cantidad,
                    precio_compra_unitario=precio,
                )
                db.session.add(lote)
                db.session.flush()
                subtotal = round(cantidad * precio, 2)
                total += subtotal
                db.session.add(DetalleCompra(
                    compra_id=compra.id, medicamento_id=medicamentos[codigo].id, lote_id=lote.id,
                    cantidad=cantidad, precio_unitario=precio, subtotal=subtotal,
                ))
            compra.total = round(total, 2)
            auditoria_compras.append(
                ("crear", "Compra", compra.id, f"{compra.numero_compra} - S/ {compra.total:.2f}")
            )


        inicio, fin = hoy - timedelta(days=10), hoy + timedelta(days=20)
        for nombre, tipo, codigo, sucursal, valor, lleva, paga, cupon in PROMOCIONES_DATA:
            db.session.add(Promocion(
                nombre=nombre, tipo=tipo,
                medicamento_id=medicamentos[codigo].id if codigo else None,
                sucursal_id=sucursales[sucursal].id if sucursal else None,
                valor=valor, lleva=lleva, paga=paga, codigo=cupon,
                fecha_inicio=inicio, fecha_fin=fin, activo=True,
            ))

        db.session.commit()



        usuarios = {u.email: u for u in Usuario.query.all()}
        sucursales = {s.nombre: s for s in Sucursal.query.all()}
        medicamentos = {m.codigo: m for m in Medicamento.query.all()}



        admin = usuarios["admin@inkafarma.pe"]
        for accion, entidad, entidad_id, detalle in auditoria_compras:
            db.session.add(RegistroAuditoria(
                usuario_id=admin.id, accion=accion, entidad=entidad,
                entidad_id=entidad_id, detalle=detalle,
            ))
        db.session.commit()



        app.config["WTF_CSRF_ENABLED"] = False
        cliente = app.test_client()

        _crear_venta(cliente, usuarios["cajero@inkafarma.pe"], sucursales["Sucursal Principal"], [
            {"medicamento_id": medicamentos["MED-0001"].id, "cantidad": 12},
            {"medicamento_id": medicamentos["MED-0002"].id, "cantidad": 4},
        ], dias_atras=6, cliente="Pedro Gómez")

        _crear_venta(cliente, usuarios["maria.cajera@inkafarma.pe"], sucursales["Sucursal Miraflores"], [
            {"medicamento_id": medicamentos["MED-0004"].id, "cantidad": 2},
            {"medicamento_id": medicamentos["MED-0008"].id, "cantidad": 5},
        ], dias_atras=4, cliente="María Torres", metodo="Tarjeta",
            referencia="4321 · María Torres", cupon="SALUD10")

        _crear_venta(cliente, usuarios["carlos.cajero@inkafarma.pe"], sucursales["Sucursal San Isidro"], [
            {"medicamento_id": medicamentos["MED-0003"].id, "cantidad": 3, "numero_receta": "REC-20451"},
            {"medicamento_id": medicamentos["MED-0006"].id, "cantidad": 1, "numero_receta": "REC-20452"},
        ], dias_atras=3, cliente="Carlos Ruiz", metodo="Yape/Plin", referencia="987654321")

        _crear_venta(cliente, usuarios["cajero@inkafarma.pe"], sucursales["Sucursal Principal"], [
            {"medicamento_id": medicamentos["MED-0001"].id, "cantidad": 25},
            {"medicamento_id": medicamentos["MED-0005"].id, "cantidad": 6},
        ], dias_atras=1, cliente="Ana Vargas")

        _crear_venta(cliente, usuarios["cajero@inkafarma.pe"], sucursales["Sucursal Principal"], [
            {"medicamento_id": medicamentos["MED-0001"].id, "cantidad": 5},
            {"medicamento_id": medicamentos["MED-0002"].id, "cantidad": 3},
        ], dias_atras=0, cliente="Cliente Varios")

        print("\n[OK] Base de datos inicializada correctamente.\n")
        print("Datos de ejemplo: 3 sucursales, 20 medicamentos, 3 laboratorios, 29 lotes,")
        print("4 compras, 3 promociones y 5 ventas reales (stock descontado por FEFO).")
        print("\nUsuarios de prueba:")
        print("-" * 74)
        for nombre, email, password, rol_nombre, sucursal_nombre in USUARIOS_DATA:
            destino = sucursal_nombre or "todas"
            print(f"  {rol_nombre:<14} | {email:<32} | {password:<10} | {destino}")
        print("-" * 74)


if __name__ == "__main__":
    run()
