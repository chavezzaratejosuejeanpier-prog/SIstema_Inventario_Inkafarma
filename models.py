"""
Modelos de datos del Sistema de Gestión de Inventario - Inkafarma.

Estas clases (paradigma orientado a objetos) conviven en el proyecto con
funciones puras (paradigma funcional, ver paradigmas/funcional.py) y con
reglas lógicas (paradigma lógico, ver paradigmas/logica.py y reglas.pl),
lo que ilustra directamente el enfoque MULTIPARADIGMA visto en la Unidad 3.

Jerarquía de herencia propia (Semana 15 - Clases y objetos, Herencia):

    EntidadBase (abstracta)
        └── EntidadCatalogo (abstracta)
                ├── Usuario
                ├── Laboratorio
                └── Medicamento
        ├── Rol
        ├── CodigoRecuperacion
        ├── Lote
        ├── Compra / DetalleCompra
        └── Venta / DetalleVenta

`EntidadBase` y `EntidadCatalogo` son clases base *nuestras* (no de
SQLAlchemy): definen atributos y métodos comunes que las subclases heredan
y reutilizan sin reescribirlos, además de la herencia de framework
(`db.Model`) que ya traía cada clase.
"""
import random
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class EntidadBase(db.Model):
    """Clase base abstracta de la que heredan todas las entidades del
    sistema. Centraliza la clave primaria y las operaciones de guardado/
    borrado que, sin esta jerarquía, se repetirían en cada modelo."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def guardar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def eliminar(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):



        return f"<{self.__class__.__name__} id={self.id}>"


class EntidadCatalogo(EntidadBase):
    """Clase base abstracta para entidades administrables de catálogo:
    tienen un estado activo/inactivo y se desactivan en vez de borrarse
    físicamente (Usuario, Laboratorio, Medicamento)."""
    __abstract__ = True

    activo = db.Column(db.Boolean, default=True)

    def activar(self):
        self.activo = True
        db.session.commit()

    def desactivar(self):
        self.activo = False
        db.session.commit()


class Sucursal(EntidadCatalogo):
    """Local físico de Inkafarma. El stock (Lote), las compras y las
    ventas quedan atados a una sucursal; el catálogo de medicamentos y
    laboratorios sigue siendo nacional/compartido entre todas."""
    __tablename__ = "sucursales"

    nombre = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(30))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "activo": self.activo,
        }


class Rol(EntidadBase):
    __tablename__ = "roles"

    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))

    usuarios = db.relationship("Usuario", backref="rol", lazy=True)

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "descripcion": self.descripcion}


class Usuario(EntidadCatalogo):
    __tablename__ = "usuarios"

    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)


    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id"), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)


    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)

    sucursal = db.relationship("Sucursal")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def bloqueado(self):
        return bool(self.bloqueado_hasta and datetime.utcnow() < self.bloqueado_hasta)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol.nombre if self.rol else None,
            "rol_id": self.rol_id,
            "sucursal_id": self.sucursal_id,
            "sucursal": self.sucursal.nombre if self.sucursal else None,
            "activo": self.activo,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
        }


class CodigoRecuperacion(EntidadBase):
    """Código de verificación de 6 dígitos para el flujo de 'olvidé mi contraseña'.
    Se envía por correo y expira a los 15 minutos o al primer uso."""
    __tablename__ = "codigos_recuperacion"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    codigo = db.Column(db.String(6), nullable=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    expira = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False)




    intentos = db.Column(db.Integer, default=0)

    usuario = db.relationship("Usuario")

    LIMITE_INTENTOS = 5

    @staticmethod
    def generar_codigo():
        return f"{random.randint(0, 999999):06d}"

    @classmethod
    def crear_para(cls, usuario, minutos_validez=15):

        CodigoRecuperacion.query.filter_by(usuario_id=usuario.id, usado=False).update({"usado": True})
        codigo = cls(
            usuario_id=usuario.id,
            codigo=cls.generar_codigo(),
            expira=datetime.utcnow() + timedelta(minutes=minutos_validez),
        )
        db.session.add(codigo)
        return codigo

    @property
    def expirado(self):
        return datetime.utcnow() > self.expira

    @property
    def valido(self):
        return not self.usado and not self.expirado and (self.intentos or 0) < self.LIMITE_INTENTOS


class Laboratorio(EntidadCatalogo):
    __tablename__ = "laboratorios"

    nombre = db.Column(db.String(150), nullable=False)
    ruc = db.Column(db.String(20))
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(255))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)

    medicamentos = db.relationship("Medicamento", backref="laboratorio", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "ruc": self.ruc,
            "telefono": self.telefono,
            "email": self.email,
            "direccion": self.direccion,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "activo": self.activo,
        }


class Medicamento(EntidadCatalogo):
    __tablename__ = "medicamentos"

    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey("laboratorios.id"), nullable=False)
    categoria = db.Column(db.String(80))
    presentacion = db.Column(db.String(80))
    unidad_medida = db.Column(db.String(30))
    precio_compra = db.Column(db.Float, default=0)
    precio_venta = db.Column(db.Float, default=0)
    requiere_receta = db.Column(db.Boolean, default=False)
    stock_minimo = db.Column(db.Integer, default=10)

    lotes = db.relationship("Lote", backref="medicamento", lazy=True)

    @property
    def stock_total(self):
        return sum(l.cantidad_actual for l in self.lotes)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "laboratorio_id": self.laboratorio_id,
            "laboratorio": self.laboratorio.nombre if self.laboratorio else None,
            "categoria": self.categoria,
            "presentacion": self.presentacion,
            "unidad_medida": self.unidad_medida,
            "precio_compra": self.precio_compra,
            "precio_venta": self.precio_venta,
            "requiere_receta": self.requiere_receta,
            "stock_minimo": self.stock_minimo,
            "stock_total": self.stock_total,
            "activo": self.activo,
        }


class Lote(EntidadBase):
    __tablename__ = "lotes"

    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id"), nullable=True)
    numero_lote = db.Column(db.String(50), nullable=False)
    fecha_fabricacion = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    cantidad_inicial = db.Column(db.Integer, nullable=False)
    cantidad_actual = db.Column(db.Integer, nullable=False)
    precio_compra_unitario = db.Column(db.Float, default=0)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    sucursal = db.relationship("Sucursal")

    @property
    def dias_para_vencer(self):
        return (self.fecha_vencimiento - date.today()).days

    def to_dict(self):
        return {
            "id": self.id,
            "medicamento_id": self.medicamento_id,
            "medicamento": self.medicamento.nombre if self.medicamento else None,
            "sucursal_id": self.sucursal_id,
            "sucursal": self.sucursal.nombre if self.sucursal else None,
            "numero_lote": self.numero_lote,
            "fecha_fabricacion": self.fecha_fabricacion.isoformat() if self.fecha_fabricacion else None,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            "cantidad_inicial": self.cantidad_inicial,
            "cantidad_actual": self.cantidad_actual,
            "precio_compra_unitario": self.precio_compra_unitario,
            "dias_para_vencer": self.dias_para_vencer,
        }


class Compra(EntidadBase):
    __tablename__ = "compras"

    numero_compra = db.Column(db.String(30), unique=True, nullable=False)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey("laboratorios.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id"), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, default=0)
    estado = db.Column(db.String(30), default="Completada")

    detalles = db.relationship("DetalleCompra", backref="compra", lazy=True, cascade="all, delete-orphan")
    laboratorio = db.relationship("Laboratorio")
    usuario = db.relationship("Usuario")
    sucursal = db.relationship("Sucursal")

    def to_dict(self):
        return {
            "id": self.id,
            "numero_compra": self.numero_compra,
            "laboratorio": self.laboratorio.nombre if self.laboratorio else None,
            "usuario": self.usuario.nombre if self.usuario else None,
            "sucursal_id": self.sucursal_id,
            "sucursal": self.sucursal.nombre if self.sucursal else None,
            "fecha": self.fecha.isoformat(),
            "total": self.total,
            "estado": self.estado,
            "detalles": [d.to_dict() for d in self.detalles],
        }


class DetalleCompra(EntidadBase):
    __tablename__ = "detalle_compras"

    compra_id = db.Column(db.Integer, db.ForeignKey("compras.id"), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    medicamento = db.relationship("Medicamento")

    def to_dict(self):
        return {
            "id": self.id,
            "medicamento_id": self.medicamento_id,
            "medicamento": self.medicamento.nombre if self.medicamento else None,
            "lote_id": self.lote_id,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
        }


class Venta(EntidadBase):
    __tablename__ = "ventas"

    numero_venta = db.Column(db.String(30), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id"), nullable=True)
    cliente_nombre = db.Column(db.String(150), default="Cliente Varios")
    cliente_dni = db.Column(db.String(20))
    cliente_email = db.Column(db.String(120))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


    descuento = db.Column(db.Float, default=0)
    cupon_codigo = db.Column(db.String(30))
    total = db.Column(db.Float, default=0)
    metodo_pago = db.Column(db.String(30), default="Efectivo")



    referencia_pago = db.Column(db.String(60))
    estado = db.Column(db.String(30), default="Completada")

    detalles = db.relationship("DetalleVenta", backref="venta", lazy=True, cascade="all, delete-orphan")
    usuario = db.relationship("Usuario")
    sucursal = db.relationship("Sucursal")

    def to_dict(self):
        return {
            "id": self.id,
            "numero_venta": self.numero_venta,
            "usuario": self.usuario.nombre if self.usuario else None,
            "sucursal_id": self.sucursal_id,
            "sucursal": self.sucursal.nombre if self.sucursal else None,
            "cliente_nombre": self.cliente_nombre,
            "cliente_dni": self.cliente_dni,
            "cliente_email": self.cliente_email,
            "fecha": self.fecha.isoformat(),
            "descuento": self.descuento or 0,
            "cupon_codigo": self.cupon_codigo,
            "total": self.total,
            "metodo_pago": self.metodo_pago,
            "referencia_pago": self.referencia_pago,
            "estado": self.estado,
            "detalles": [d.to_dict() for d in self.detalles],
        }


class DetalleVenta(EntidadBase):
    __tablename__ = "detalle_ventas"

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"))
    promocion_id = db.Column(db.Integer, db.ForeignKey("promociones.id"))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0)
    numero_receta = db.Column(db.String(50))

    medicamento = db.relationship("Medicamento")
    promocion = db.relationship("Promocion")

    def to_dict(self):
        return {
            "id": self.id,
            "medicamento_id": self.medicamento_id,
            "medicamento": self.medicamento.nombre if self.medicamento else None,
            "lote_id": self.lote_id,
            "promocion_id": self.promocion_id,
            "promocion": self.promocion.nombre if self.promocion else None,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
            "descuento": self.descuento or 0,
            "numero_receta": self.numero_receta,
        }


class Promocion(EntidadCatalogo):
    """Promoción aplicable en el punto de venta. Cuatro tipos:

    - 'porcentaje':  % de descuento sobre un medicamento específico.
    - 'monto_fijo':  S/ de descuento por unidad sobre un medicamento específico.
    - 'nxm':         lleva N unidades y paga M (ej. "3x2" -> lleva=3, paga=2).
    - 'cupon':       código que el cajero escribe a mano al cobrar; aplica
                      un % de descuento sobre el total de la boleta (no
                      está atado a un medicamento en particular).

    Si `sucursal_id` es None, la promoción aplica en todas las sucursales;
    si tiene valor, solo en esa.
    """
    __tablename__ = "promociones"

    nombre = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"))
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id"))
    valor = db.Column(db.Float)
    lleva = db.Column(db.Integer)
    paga = db.Column(db.Integer)
    codigo = db.Column(db.String(30), unique=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)

    medicamento = db.relationship("Medicamento")
    sucursal = db.relationship("Sucursal")

    @property
    def vigente(self):
        hoy = date.today()
        return bool(self.activo) and self.fecha_inicio <= hoy <= self.fecha_fin

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "medicamento_id": self.medicamento_id,
            "medicamento": self.medicamento.nombre if self.medicamento else None,
            "sucursal_id": self.sucursal_id,
            "sucursal": self.sucursal.nombre if self.sucursal else None,
            "valor": self.valor,
            "lleva": self.lleva,
            "paga": self.paga,
            "codigo": self.codigo,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "activo": self.activo,
            "vigente": self.vigente,
        }


class RegistroAuditoria(EntidadBase):
    """Historial de auditoría: quién hizo qué acción, sobre qué entidad y
    cuándo. Se registra desde registrar_auditoria() (ver api/auditoria.py)
    en los endpoints de creación/edición/eliminación/anulación."""
    __tablename__ = "registro_auditoria"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    accion = db.Column(db.String(30), nullable=False)
    entidad = db.Column(db.String(50), nullable=False)
    entidad_id = db.Column(db.Integer, nullable=True)
    detalle = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario.nombre if self.usuario else "Sistema",
            "accion": self.accion,
            "entidad": self.entidad,
            "entidad_id": self.entidad_id,
            "detalle": self.detalle,
            "fecha": self.fecha.isoformat(),
        }