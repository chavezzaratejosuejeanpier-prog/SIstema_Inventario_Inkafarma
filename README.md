# Sistema de Gestión de Inventario — Inkafarma

Proyecto final del curso **Lenguajes de Programación**. Aplica las 3 unidades del sílabo:

| Unidad | Paradigma | Dónde está en el código |
|---|---|---|
| 1 | Programación Funcional | `paradigmas/funcional.py` (map, filter, reduce, lambdas, funciones de orden superior, recursión, inmutabilidad) |
| 2 | Programación Lógica | `paradigmas/reglas.pl` (Prolog: hechos, predicados, unificación, resolución) + `paradigmas/logica.py` (motor) |
| 3 | Multiparadigma / Ciencia de Datos | `paradigmas/multiparadigma.py` (pandas, numpy) + resto del proyecto (OOP con SQLAlchemy, Flask) |

Cumple los 6 criterios de la rúbrica: análisis de requisitos (módulos completos de una cadena de farmacias real, multi-sucursal), diseño justificado (arquitectura por capas y por paradigma, jerarquía de clases propia), implementación correcta y ordenada, aplicación explícita de los 3 paradigmas, datos de prueba para validar (`seed.py`) y pruebas automatizadas (`tests/`), y este documento como documentación.

## Módulos incluidos
Medicamentos · Laboratorios · Compras · Ventas (con promociones y cupones) · Lotes · Fechas de vencimiento · Stock · **Sucursales** (multi-local) · **Usuarios y Roles** (Administrador, Cajero) · **Perfil de usuario** · Recuperación de contraseña por correo · Dashboard con KPIs y gráficos · Alertas automáticas (motor lógico) · **Auditoría** (historial de acciones) · **Reportes** exportables a Excel/PDF.

## Módulos por rol
- **Administrador:** acceso total — usuarios, roles, sucursales, laboratorios, medicamentos, lotes, compras, ventas, promociones, alertas, auditoría y reportes.
- **Cajero:** punto de venta (`/ventas`), historial de sus propias ventas (`/mis-ventas`) y consulta de stock/alertas, todo acotado a su sucursal asignada. No puede editar el catálogo ni ver otras sucursales.

## Tecnologías usadas
- **Frontend:** HTML5, CSS3, JavaScript (vanilla, fetch API), Tailwind CSS, Font Awesome (CDN), Chart.js (CDN).
- **Backend:** Python 3, Flask, Flask-SQLAlchemy.
- **Ciencia de datos:** Pandas, NumPy.
- **Reportes:** openpyxl (Excel) y ReportLab (PDF), con logo institucional embebido.
- **Correo:** envío de códigos de verificación (recuperación de contraseña) vía SMTP.
- **Pruebas:** pytest (`tests/`).
- **Base de datos:** **SQLite por defecto** (`inkafarma.db`, cero configuración). Si existe un `.env` con `DATABASE_URL`, se usa **PostgreSQL (pgAdmin)** en su lugar (ver abajo).
- **Programación lógica:** Prolog (`reglas.pl`). Si no tienes SWI-Prolog instalado, el sistema usa automáticamente un motor equivalente en Python puro, así que **funciona sin instalar nada adicional**.

---

## 🎨 Tailwind CSS (build local, no CDN)

El proyecto usa **Tailwind CSS v4** compilado con la Tailwind CLI oficial, no el script de CDN. El archivo `static/css/tailwind.css` ya viene generado y subido al repo, así que **no necesitas Node.js para simplemente correr el proyecto** (`python app.py` funciona tal cual).

Solo necesitas Node.js si vas a **editar clases de Tailwind** en los templates o en `static/js/` (por ejemplo, agregar una clase nueva que hoy no exista en `static/css/tailwind.css`):

```bash
npm install       # instala tailwindcss y su CLI (una sola vez)
npm run build:css # compila static/src/tailwind.css -> static/css/tailwind.css (una vez)
npm run watch:css # o, mientras editas: recompila automáticamente en cada cambio
```

Los colores de marca (`inka-green`, `inka-green-dark`, `inka-green-light`, `inka-red`, `inka-yellow`) están definidos como tokens reales de Tailwind en `static/src/tailwind.css` (bloque `@theme`), así que soportan todas las variantes automáticamente: `bg-inka-green`, `hover:bg-inka-green-dark`, `focus:ring-inka-green`, etc.

---

## 🐘 Base de datos: SQLite por defecto / PostgreSQL opcional

El proyecto usa **SQLite** (`inkafarma.db`) si no hay un archivo `.env`. Para usar PostgreSQL, copia `.env.example` a `.env` y ajusta la conexión:

```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/inkafarma_db
```

Si eliges PostgreSQL, crea la base de datos en pgAdmin:

1. Abre **pgAdmin** y conéctate a tu servidor local (`localhost`, usuario `postgres`, contraseña `12345`).
2. Click derecho en **Databases → Create → Database…**
3. En "Database", escribe exactamente: `inkafarma_db` → Save.
4. Ya está. **No necesitas crear tablas manualmente**: cuando ejecutes `python seed.py` (paso 5 más abajo), SQLAlchemy crea todas las tablas automáticamente dentro de `inkafarma_db` y las llena con datos de ejemplo. Además, cada vez que arrancas el servidor (`python app.py`), el sistema revisa si hay tablas o columnas nuevas (por ejemplo de sucursales o promociones) y las agrega automáticamente sin borrar tus datos.

> Si tu usuario, host, puerto o contraseña de PostgreSQL son distintos, edita el archivo `.env` con tus datos reales, respetando el formato:
> `postgresql://usuario:password@host:puerto/nombre_basededatos`

Si en algún momento quieres volver a usar SQLite (cero configuración), solo renombra o elimina el archivo `.env` — el sistema detecta que no existe y usa automáticamente un archivo `inkafarma.db` local.

También se incluye `schema_postgresql.sql` con el modelo relacional equivalente, por si tu profesor pide ver el script SQL directamente (es solo de referencia; no hace falta ejecutarlo, `seed.py` ya crea todo).

---

## 📧 Correo saliente (recuperación de contraseña)

El flujo "¿Olvidaste tu contraseña?" envía un código de verificación de 6 dígitos por correo (válido 15 minutos). Para que funcione, completa estas variables en `.env` (ya están de ejemplo en `.env.example`):

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=tu-correo@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion
MAIL_DEFAULT_SENDER=tu-correo@gmail.com
```


---

## 🚀 Paso a paso para ejecutar el proyecto

### 1. Requisitos previos
- **Python 3.10 o superior**. Verifícalo con:
  ```bash
  python3 --version
  ```
- **PostgreSQL instalado y pgAdmin** (ver sección anterior para crear la base de datos `inkafarma_db`).

### 2. Descomprimir el proyecto
Descomprime el archivo `inkafarma_inventario.zip` en la carpeta donde quieras trabajar.

### 3. Crear un entorno virtual (recomendado)
```bash
cd inkafarma_inventario
python3 -m venv venv

# Activar el entorno virtual:
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```
Esto instala Flask, Flask-SQLAlchemy, pandas, numpy, openpyxl y reportlab (para los reportes), pytest (para las pruebas) y **psycopg2-binary** (el driver necesario para conectarse a PostgreSQL).

### 5. Inicializar la base de datos con datos de ejemplo
Este comando crea las tablas y carga un escenario completo y coherente (usando SQLite o PostgreSQL según `.env`):

- **3 sucursales** (Principal, Miraflores y San Isidro) con lotes asignados a cada una.
- **4 usuarios**: 1 administrador y 3 cajeros (uno por local).
- **3 laboratorios**, **20 medicamentos** y **29 lotes** con casos de stock crítico, próximos a vencer y vencidos.
- **4 órdenes de compra** que generan lotes reales (ingreso de stock).
- **3 promociones vigentes** (15% en Paracetamol, cupón `SALUD10` y 3x2 en Vitamina C solo en Miraflores).
- **4 ventas reales** repartidas en varios días y sucursales, registradas con la misma lógica del sistema (descuento FEFO, promociones y cupón aplicados).

```bash
python seed.py
```

> ⚠️ `seed.py` **borra y recrea** todas las tablas (`drop_all()`). Vuelve a ejecutarlo solo cuando quieras restaurar el escenario de demostración; cualquier dato creado desde la interfaz se perderá.

### 6. Ejecutar el servidor
```bash
python app.py
```
Verás algo como `Running on http://127.0.0.1:5000`. Abre esa dirección en tu navegador.

### 7. Iniciar sesión
Usa cualquiera de estos usuarios de prueba (creados por `seed.py`):

| Rol | Email | Contraseña | Permisos |
|---|---|---|---|
| **Administrador** | admin@inkafarma.pe | admin123 | Acceso total: usuarios, sucursales, laboratorios, medicamentos, lotes, compras, ventas, promociones, auditoría y reportes |
| **Cajero** (Principal) | cajero@inkafarma.pe | cajero123 | Registrar ventas en su sucursal y consultar stock/alertas (sin editar el catálogo) |
| **Cajera** (Miraflores) | maria.cajera@inkafarma.pe | cajero123 | Ídem, acotado a Sucursal Miraflores |
| **Cajero** (San Isidro) | carlos.cajero@inkafarma.pe | cajero123 | Ídem, acotado a Sucursal San Isidro |

> ¿Por qué solo 2 roles? Se simplificó a un esquema realista de punto de venta de farmacia: quien administra el negocio (**Administrador**) y quien atiende en caja (**Cajero**). Si tu proyecto lo requiere, puedes agregar más roles fácilmente desde la pantalla "Usuarios y Roles" o extendiendo `seed.py`.

### 8. Explorar el sistema
- **Dashboard:** KPIs, gráfico de ventas (pandas/numpy), top de vendidos (funcional) y alertas críticas (lógica/Prolog). Vista distinta para Administrador y Cajero.
- **Medicamentos / Laboratorios:** catálogo con CRUD completo (solo Administrador puede crear/editar/eliminar; el Cajero solo consulta).
- **Lotes y Stock:** registra lotes con fecha de vencimiento; el sistema calcula automáticamente si están vigentes, por vencer o vencidos.
- **Compras:** simula una orden de compra a un laboratorio; genera lotes nuevos automáticamente.
- **Ventas:** disponible para Administrador y Cajero; descuenta stock automáticamente usando el criterio FEFO (se consume primero el lote que vence antes), y aplica promociones/cupones vigentes. El Cajero además tiene "Mis ventas" (`/mis-ventas`) con su propio historial.
- **Promociones:** crea descuentos por porcentaje, monto fijo, "Nx M" (ej. 3x2) o cupones, con vigencia por fecha y opcionalmente por sucursal.
- **Sucursales:** administra los locales físicos de la cadena; cada usuario, lote, compra y venta queda asociado a una sucursal.
- **Alertas:** muestra en detalle el resultado del motor de reglas Prolog.
- **Usuarios (solo Administrador):** crea, edita y desactiva usuarios, asigna roles y sucursal.
- **Auditoría (solo Administrador):** historial de quién hizo qué (crear/editar/eliminar/anular/activar/desactivar) sobre cada entidad del sistema.
- **Reportes (solo Administrador):** exporta ventas e inventario a Excel o PDF, con logo y resumen incluidos.
- **Perfil:** cualquier usuario puede ver y actualizar sus propios datos y contraseña.
- **¿Olvidaste tu contraseña?:** en el login, permite recuperar el acceso con un código de 6 dígitos enviado por correo (ver sección de correo saliente más arriba).

---

## 🔁 Reiniciar los datos
Si quieres borrar todo y volver a los datos de ejemplo, vuelve a ejecutar:
```bash
python seed.py
```
(Esto borra y recrea las tablas — úsalo solo mientras pruebas el proyecto).

---

## ✅ Pruebas automatizadas
El proyecto incluye pruebas con **pytest** en la carpeta `tests/` (autenticación, medicamentos, usuarios, ventas, sucursales, promociones, correo y los paradigmas funcional/lógico). Para ejecutarlas:
```bash
pytest
```
La configuración (`pytest.ini`) ya apunta a la carpeta `tests/`, así que no necesitas parámetros adicionales.

---

## 🖼️ Logo / foto de Inkafarma
En `static/img/` va la imagen del logo que se muestra en el sidebar, en la pantalla de login y en los reportes Excel/PDF. El sistema busca un archivo llamado **`logo.png`** en esa carpeta:

- Si colocas ahí tu propia foto/logo con el nombre exacto `logo.png`, se usará automáticamente (no hace falta tocar código).
- Si ese archivo no existe, la interfaz usa como respaldo automático `static/img/logo.svg`, un ícono genérico que ya viene incluido para que la pantalla nunca se vea rota.

> Nota: no coloqué directamente el logotipo oficial de Inkafarma porque es una marca registrada de terceros; te dejé el mecanismo listo para que agregues tú mismo el archivo `logo.png` con la imagen que tengas.

---

## 🐍 Uso opcional de Prolog real (SWI-Prolog)
El proyecto funciona igual sin esto (usa un motor equivalente en Python). Si quieres usar el motor Prolog real:
```bash
# Instalar SWI-Prolog en el sistema operativo, por ejemplo en Ubuntu/Debian:
sudo apt-get install swi-prolog
# Instalar el puente Python <-> Prolog:
pip install pyswip
```
El archivo `paradigmas/logica.py` detecta automáticamente si `pyswip` está disponible y lo usa; si no, cae en el motor equivalente sin que el resto de la aplicación se entere.

---

## 📁 Estructura del proyecto
```
inkafarma_inventario/
├── app.py                     # Aplicación Flask (rutas de páginas, migraciones automáticas de columnas/tablas)
├── config.py                  # Configuración (BD, claves, correo, carga el .env)
├── extensions.py              # Instancia de SQLAlchemy
├── models.py                  # Modelos (OOP, con jerarquía propia EntidadBase/EntidadCatalogo): Usuario, Rol,
│                               #   Sucursal, Medicamento, Lote, Compra, Venta, Promocion, RegistroAuditoria...
├── seed.py                    # Carga de datos de ejemplo (roles: Administrador, Cajero)
├── requirements.txt
├── pytest.ini                 # Configuración de pytest (apunta a tests/)
├── schema_postgresql.sql      # Esquema SQL de referencia
├── .env                       # Opcional: PostgreSQL + correo (copiar desde .env.example)
├── .env.example               # Plantilla de referencia
├── auth/
│   ├── __init__.py             # Vacío a propósito (marca la carpeta como paquete Python)
│   ├── routes.py               # Login / logout / recuperación de contraseña
│   ├── correo.py                # Envío de correos (código de recuperación) vía SMTP
│   └── decorators.py           # Control de acceso por rol (login_requerido, requiere_rol)
├── api/
│   ├── __init__.py             # Vacío a propósito (marca la carpeta como paquete Python)
│   ├── medicamentos.py         # API REST: medicamentos y laboratorios
│   ├── lotes.py                # API REST: lotes
│   ├── compras.py              # API REST: compras
│   ├── ventas.py                # API REST: ventas (incluye promociones/cupones y FEFO)
│   ├── usuarios.py             # API REST: usuarios y roles
│   ├── sucursales.py           # API REST: sucursales
│   ├── promociones.py          # API REST: promociones y cupones
│   ├── auditoria.py            # API REST: historial de auditoría
│   ├── reportes.py             # API REST: exportación de reportes a Excel/PDF
│   └── dashboard.py            # API REST: resumen (integra las 3 unidades)
├── paradigmas/
│   ├── __init__.py             # Vacío a propósito (marca la carpeta como paquete Python)
│   ├── funcional.py            # UNIDAD 1 - Programación Funcional
│   ├── reglas.pl               # UNIDAD 2 - Reglas Prolog
│   ├── logica.py               # UNIDAD 2 - Motor lógico (Prolog + fallback)
│   └── multiparadigma.py       # UNIDAD 3 - Analítica con pandas/numpy
├── tests/                      # Pruebas automatizadas (pytest): auth, medicamentos, usuarios, ventas,
│                               #   sucursales, promociones, correo y paradigmas
├── templates/                  # Vistas HTML (Jinja2 + Tailwind)
│   ├── base.html                # Layout base compartido (sidebar, navegación)
│   ├── login.html, olvide_password.html, verificar_codigo.html   # Autenticación
│   ├── medicamentos.html, perfil.html
│   ├── admin/                   # Vistas exclusivas de Administrador (dashboard, ventas, lotes, compras,
│   │                             #   laboratorios, usuarios, sucursales, promociones, auditoría, alertas)
│   └── cajero/                  # Vistas exclusivas de Cajero (dashboard, ventas, historial)
└── static/
    ├── img/
    │   ├── logo.svg             # Logo genérico de respaldo (ya incluido)
    │   ├── logo.png             # <- coloca aquí tu propia foto/logo (opcional)
    │   └── local.png             # Imagen de referencia para sucursales
    ├── audio/
    │   └── notification-sound.mp3   # Sonido de alerta en el punto de venta
    ├── css/                      # Un archivo por página (base.css + uno por módulo)
    └── js/                       # Un archivo por página (base.js + uno por módulo), incluye vistas
                                   #   separadas para Administrador/Cajero en ventas y dashboard
```

### ¿Por qué antes había un solo `style.css`/`app.js` y ahora hay uno por página?
Antes todas las páginas compartían `static/css/style.css` y `static/js/app.js`. Ahora:
- **`base.css`/`base.js`** siguen existiendo y contienen SOLO lo verdaderamente compartido (colores de marca, sidebar, botones, tablas, utilidades de fetch/toast).
- Cada página (`login`, `dashboard`, `medicamentos`, etc.) tiene su **propio archivo CSS y JS**, cargado únicamente en esa página mediante los bloques `{% block estilos %}` y `{% block scripts %}` de Jinja.
- Ventaja: es más ordenado, cada archivo es más corto y fácil de ubicar, y si rompes algo en `ventas.css` no afecta a las demás páginas.

---

## 🎨 Sobre el diseño
La interfaz usa la paleta de colores institucional de Inkafarma (verde, rojo y amarillo) a modo de referencia visual para un caso de estudio académico. Este es un proyecto educativo/ficticio y no representa ni está afiliado al sistema real de Inkafarma.

## 📝 Notas para la sustentación
- El **Dashboard** y la página de **Alertas** son los mejores lugares para mostrar en vivo cómo interactúan las 3 unidades: el pipeline funcional calcula el reporte de inventario, el motor lógico evalúa las reglas Prolog para las alertas, y el módulo de pandas/numpy genera las estadísticas y gráficos.
- Puedes mostrar el archivo `paradigmas/reglas.pl` directamente para explicar hechos, predicados y reglas en Prolog "puro", y luego mostrar `paradigmas/logica.py` para explicar cómo Python dialoga con ese motor.
- `paradigmas/funcional.py` está comentado explícitamente citando cada concepto de la Unidad 1 (funciones anónimas, valores inmutables, funciones de orden superior, recursión).
- `models.py` documenta una jerarquía de herencia propia (`EntidadBase` → `EntidadCatalogo` → `Usuario`/`Laboratorio`/`Medicamento`, entre otras) que ilustra herencia y polimorfismo además del ORM de SQLAlchemy — útil para explicar el paradigma OOP en la Unidad 3.
- Los módulos de **Sucursales**, **Promociones** y **Auditoría** son buenos ejemplos de requisitos de negocio realistas (cadena multi-local, campañas comerciales, trazabilidad) que enriquecen el análisis de requisitos de la rúbrica.
- Los archivos `__init__.py` de `api/`, `auth/` y `paradigmas/` están vacíos **a propósito**: en Python, un archivo `__init__.py` (aunque esté vacío) es lo que le indica al intérprete que esa carpeta es un paquete importable. No es un error ni algo incompleto.
