
















CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion VARCHAR(200)
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP
);



CREATE TABLE codigos_recuperacion (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    codigo VARCHAR(6) NOT NULL,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expira TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE
);

CREATE TABLE laboratorios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    ruc VARCHAR(20),
    telefono VARCHAR(30),
    email VARCHAR(120),
    direccion VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE medicamentos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    laboratorio_id INTEGER NOT NULL REFERENCES laboratorios(id),
    categoria VARCHAR(80),
    presentacion VARCHAR(80),
    unidad_medida VARCHAR(30),
    precio_compra FLOAT DEFAULT 0,
    precio_venta FLOAT DEFAULT 0,
    requiere_receta BOOLEAN DEFAULT FALSE,
    stock_minimo INTEGER DEFAULT 10,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE lotes (
    id SERIAL PRIMARY KEY,
    medicamento_id INTEGER NOT NULL REFERENCES medicamentos(id),
    numero_lote VARCHAR(50) NOT NULL,
    fecha_fabricacion DATE,
    fecha_vencimiento DATE NOT NULL,
    cantidad_inicial INTEGER NOT NULL,
    cantidad_actual INTEGER NOT NULL,
    precio_compra_unitario FLOAT DEFAULT 0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compras (
    id SERIAL PRIMARY KEY,
    numero_compra VARCHAR(30) UNIQUE NOT NULL,
    laboratorio_id INTEGER NOT NULL REFERENCES laboratorios(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total FLOAT DEFAULT 0,
    
    estado VARCHAR(30) DEFAULT 'Completada'
);

CREATE TABLE detalle_compras (
    id SERIAL PRIMARY KEY,
    compra_id INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    medicamento_id INTEGER NOT NULL REFERENCES medicamentos(id),
    lote_id INTEGER REFERENCES lotes(id),
    cantidad INTEGER NOT NULL,
    precio_unitario FLOAT NOT NULL,
    subtotal FLOAT NOT NULL
);

CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    numero_venta VARCHAR(30) UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    cliente_nombre VARCHAR(150) DEFAULT 'Cliente Varios',
    cliente_dni VARCHAR(20),
    cliente_email VARCHAR(120),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descuento FLOAT DEFAULT 0,
    total FLOAT DEFAULT 0,
    metodo_pago VARCHAR(30) DEFAULT 'Efectivo',
    estado VARCHAR(30) DEFAULT 'Completada'
);

CREATE TABLE detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    medicamento_id INTEGER NOT NULL REFERENCES medicamentos(id),
    lote_id INTEGER REFERENCES lotes(id),
    cantidad INTEGER NOT NULL,
    precio_unitario FLOAT NOT NULL,
    subtotal FLOAT NOT NULL,
    
    numero_receta VARCHAR(50)
);



CREATE TABLE registro_auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    accion VARCHAR(30) NOT NULL,
    entidad VARCHAR(50) NOT NULL,
    entidad_id INTEGER,
    detalle VARCHAR(255),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
