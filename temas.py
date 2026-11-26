# -*- coding: utf-8 -*-
"""Temáticas de la aplicación del caso (la app que corre en web-NN).

Cada temática tiene un PATRÓN de negocio que define sus funciones (no es solo un formulario o bitácora):
  inventario  → stock por ítem, movimientos de entrada/salida con validación de stock, stock crítico, valorización
  reservas    → agenda por recurso sin dobles reservas (bloque horario o rango de fechas), disponibilidad, cancelar/completar
  prestamos   → préstamo solo de ítems disponibles, devolución, atrasos, mantención y ranking
  ordenes     → flujo de estados (avanzar), prioridad/severidad, tiempos de cierre, montos o RTO opcionales
  membresias  → planes con valor y duración, vigencia calculada, renovar/suspender, por vencer

Tipos de campo: text, tel, email, date, number, select:Op1|Op2, textarea
Todas las apps agregan además las tablas usuarios_app (login con roles) y auditoria_app (registro inmutable).
"""

TEMAS = [
    {
        "clave": "veterinaria", "nombre_app": "VetCuidado", "patron": "reservas",
        "titulo": "Agenda de atenciones de clínica veterinaria",
        "contexto": "Una clínica veterinaria de La Serena agenda atenciones por teléfono en un cuaderno; se topan horas del mismo veterinario, no se sabe qué atenciones se realizaron y los datos de los tutores quedan expuestos en el mesón.",
        "actores": ["Recepcionista", "Médico veterinario", "Tutor de la mascota", "Administrador TI"],
        "procesos": ["Registro de veterinarios", "Agendamiento de atenciones", "Consulta de disponibilidad", "Registro de asistencia", "Respaldo de la agenda"],
        "padre": {"tabla": "veterinarios", "titulo": "Veterinarios", "singular": "veterinario", "campos": [
            ("nombre", "text", "Nombre"), ("especialidad", "select:Medicina general|Cirugía|Dermatología|Exóticos", "Especialidad")]},
        "hijo": {"tabla": "atenciones", "titulo": "Atenciones", "singular": "atención", "fk": "veterinario_id", "campos": [
            ("mascota", "text", "Mascota"), ("especie", "select:Perro|Gato|Ave|Exótico", "Especie"),
            ("tutor", "text", "Tutor"), ("telefono", "tel", "Teléfono del tutor"), ("motivo", "textarea", "Motivo")]},
        "vocab": {"modo": "bloque", "bloques": ["09:00", "10:00", "11:00", "12:00", "15:00", "16:00", "17:00"], "completar": "Atendida"},
    },
    {
        "clave": "biblioteca", "nombre_app": "BiblioRed", "patron": "prestamos",
        "titulo": "Préstamo de libros de biblioteca comunal",
        "contexto": "La biblioteca comunal presta libros anotando en fichas de papel; no sabe qué libros están prestados, los atrasos no se detectan y el catálogo se pierde si falla el computador.",
        "actores": ["Bibliotecario", "Lector", "Coordinador de sede", "Administrador TI"],
        "procesos": ["Catalogación de libros", "Préstamo", "Devolución", "Control de atrasos", "Respaldo del catálogo"],
        "padre": {"tabla": "libros", "titulo": "Libros", "singular": "libro", "campos": [
            ("titulo", "text", "Título"), ("autor", "text", "Autor"), ("isbn", "text", "ISBN"),
            ("categoria", "select:Novela|Infantil|Ciencia|Historia|Referencia", "Categoría")]},
        "hijo": {"tabla": "prestamos", "titulo": "Préstamos", "singular": "préstamo", "fk": "libro_id", "campos": [
            ("lector", "text", "Lector"), ("email", "email", "Correo del lector")]},
        "vocab": {"dias": 14},
    },
    {
        "clave": "taller", "nombre_app": "TallerPro", "patron": "ordenes",
        "titulo": "Órdenes de trabajo de taller mecánico",
        "contexto": "Un taller mecánico anota las órdenes en papel; se extravían, el cliente no sabe en qué estado está su vehículo, no se controla lo cobrado y no hay trazabilidad de quién modificó una orden.",
        "actores": ["Jefe de taller", "Mecánico", "Cliente", "Administrador TI"],
        "procesos": ["Registro de clientes", "Apertura de órdenes", "Seguimiento por estado", "Cobro y entrega", "Respaldo de órdenes"],
        "padre": {"tabla": "clientes", "titulo": "Clientes", "singular": "cliente", "campos": [
            ("nombre", "text", "Nombre"), ("rut", "text", "RUT"), ("telefono", "tel", "Teléfono")]},
        "hijo": {"tabla": "ordenes", "titulo": "Órdenes de trabajo", "singular": "orden", "fk": "cliente_id", "campos": [
            ("patente", "text", "Patente"), ("vehiculo", "text", "Marca y modelo"),
            ("servicio", "select:Mantención|Frenos|Motor|Diagnóstico|Eléctrico", "Servicio"), ("detalle", "textarea", "Detalle")]},
        "vocab": {"estados": ["Recibido", "Diagnóstico", "En reparación", "Listo", "Entregado"], "nivel": "Prioridad",
                  "niveles": ["Baja", "Media", "Alta", "Urgente"], "monto": "Valor del trabajo (CLP)", "rto": ""},
    },
    {
        "clave": "canchas", "nombre_app": "ReservaYa", "patron": "reservas",
        "titulo": "Reserva de canchas deportivas municipales",
        "contexto": "El municipio administra las reservas de canchas por WhatsApp; se producen dobles reservas, no hay registro histórico y la información de los vecinos circula sin control.",
        "actores": ["Encargado deportivo", "Vecino", "Coordinador municipal", "Administrador TI"],
        "procesos": ["Registro de canchas", "Reserva de horarios", "Consulta de disponibilidad", "Control de asistencia", "Respaldo de reservas"],
        "padre": {"tabla": "canchas", "titulo": "Canchas", "singular": "cancha", "campos": [
            ("nombre", "text", "Nombre"), ("tipo", "select:Fútbol|Básquetbol|Tenis|Multiuso", "Tipo"), ("sector", "text", "Sector")]},
        "hijo": {"tabla": "reservas", "titulo": "Reservas", "singular": "reserva", "fk": "cancha_id", "campos": [
            ("vecino", "text", "Nombre del vecino"), ("telefono", "tel", "Teléfono")]},
        "vocab": {"modo": "bloque", "bloques": ["08-10", "10-12", "15-17", "17-19", "19-21"], "completar": "Asistió"},
    },
    {
        "clave": "ferreteria", "nombre_app": "StockFerre", "patron": "inventario",
        "titulo": "Inventario y ventas de ferretería de barrio",
        "contexto": "Una ferretería lleva su inventario en una planilla en el computador de caja; hay quiebres de stock, diferencias de inventario, ventas sin registro y riesgo de pérdida total ante falla del equipo.",
        "actores": ["Dueño", "Vendedor", "Bodeguero", "Administrador TI"],
        "procesos": ["Catálogo de productos", "Compras a proveedores", "Ventas", "Control de stock crítico", "Respaldo del inventario"],
        "padre": {"tabla": "productos", "titulo": "Productos", "singular": "producto", "campos": [
            ("nombre", "text", "Nombre"), ("sku", "text", "SKU"), ("categoria", "select:Herramientas|Fijaciones|Electricidad|Gasfitería|Pinturas", "Categoría")]},
        "hijo": {"tabla": "movimientos", "titulo": "Movimientos", "singular": "movimiento", "fk": "producto_id", "campos": [
            ("detalle", "text", "Proveedor / cliente / motivo")]},
        "vocab": {"tipos": [["Compra", 1], ["Venta", -1], ["Merma", -1]], "venta": "Venta", "precio": True, "unidad": "unidades"},
    },
    {
        "clave": "gimnasio", "nombre_app": "FitControl", "patron": "membresias",
        "titulo": "Planes y membresías de gimnasio",
        "contexto": "Un gimnasio registra planes y socios en un cuaderno; no puede verificar vigencias, cobra planes vencidos tarde, los datos personales quedan sin protección y no existe respaldo.",
        "actores": ["Recepción", "Entrenador", "Socio", "Administrador TI"],
        "procesos": ["Definición de planes", "Inscripción de socios", "Renovación", "Control de vigencias", "Respaldo de socios"],
        "padre": {"tabla": "planes", "titulo": "Planes", "singular": "plan", "campos": [
            ("nombre", "text", "Nombre del plan"), ("modalidad", "select:Libre|Clases grupales|Personalizado", "Modalidad")]},
        "hijo": {"tabla": "socios", "titulo": "Socios", "singular": "socio", "fk": "plan_id", "campos": [
            ("nombre", "text", "Nombre"), ("email", "email", "Correo"), ("telefono", "tel", "Teléfono")]},
        "vocab": {},
    },
    {
        "clave": "helpdesk", "nombre_app": "MesaTI", "patron": "ordenes",
        "titulo": "Mesa de ayuda TI para una PYME",
        "contexto": "Una PYME recibe solicitudes de soporte por correo y teléfono; los casos se pierden, no se mide el tiempo de respuesta, no se priorizan los críticos y no hay trazabilidad por área.",
        "actores": ["Técnico de soporte", "Usuario interno", "Jefe de área", "Administrador TI"],
        "procesos": ["Registro de áreas", "Apertura de tickets", "Atención por estado", "Medición de tiempos", "Respaldo de tickets"],
        "padre": {"tabla": "areas", "titulo": "Áreas", "singular": "área", "campos": [
            ("nombre", "text", "Nombre del área"), ("responsable", "text", "Responsable")]},
        "hijo": {"tabla": "tickets", "titulo": "Tickets", "singular": "ticket", "fk": "area_id", "campos": [
            ("asunto", "text", "Asunto"), ("categoria", "select:Hardware|Software|Red|Accesos|Correo", "Categoría"), ("detalle", "textarea", "Detalle")]},
        "vocab": {"estados": ["Abierto", "En curso", "En espera", "Resuelto", "Cerrado"], "nivel": "Prioridad",
                  "niveles": ["Baja", "Media", "Alta", "Crítica"], "monto": "", "rto": ""},
    },
    {
        "clave": "donaciones", "nombre_app": "RedSolidaria", "patron": "inventario",
        "titulo": "Banco de alimentos de una ONG",
        "contexto": "Una ONG registra donaciones y entregas en papel; no sabe cuánto stock tiene, entrega productos vencidos, no puede rendir cuentas y los datos de beneficiarios quedan expuestos.",
        "actores": ["Coordinador de la ONG", "Voluntario", "Donante", "Administrador TI"],
        "procesos": ["Catálogo de insumos", "Recepción de donaciones", "Entrega a familias", "Rendición de cuentas", "Respaldo de registros"],
        "padre": {"tabla": "insumos", "titulo": "Insumos", "singular": "insumo", "campos": [
            ("nombre", "text", "Nombre"), ("categoria", "select:Abarrotes|Lácteos|Higiene|Infantil|Otros", "Categoría"),
            ("unidad", "select:unidades|kg|litros|cajas", "Unidad")]},
        "hijo": {"tabla": "movimientos", "titulo": "Movimientos", "singular": "movimiento", "fk": "insumo_id", "campos": [
            ("contraparte", "text", "Donante o familia beneficiaria")]},
        "vocab": {"tipos": [["Donación recibida", 1], ["Entrega a familia", -1], ["Vencido / merma", -1]], "venta": "", "precio": False, "unidad": "unidades"},
    },
    {
        "clave": "dental", "nombre_app": "SonrisaAgenda", "patron": "reservas",
        "titulo": "Agenda de clínica dental",
        "contexto": "Una clínica dental agenda pacientes en una planilla compartida; se topan horas de un mismo profesional, no se registra la asistencia, hay acceso indebido a datos sensibles de salud y no existe respaldo cifrado.",
        "actores": ["Secretaria", "Odontólogo", "Paciente", "Administrador TI"],
        "procesos": ["Registro de profesionales", "Agendamiento de citas", "Consulta de disponibilidad", "Registro de asistencia", "Respaldo de la agenda"],
        "padre": {"tabla": "profesionales", "titulo": "Profesionales", "singular": "profesional", "campos": [
            ("nombre", "text", "Nombre"), ("especialidad", "select:General|Ortodoncia|Endodoncia|Odontopediatría", "Especialidad")]},
        "hijo": {"tabla": "citas", "titulo": "Citas", "singular": "cita", "fk": "profesional_id", "campos": [
            ("paciente", "text", "Paciente"), ("rut", "text", "RUT"), ("telefono", "tel", "Teléfono"), ("tratamiento", "text", "Tratamiento")]},
        "vocab": {"modo": "bloque", "bloques": ["09:00", "10:00", "11:00", "12:00", "15:00", "16:00", "17:00"], "completar": "Asistió"},
    },
    {
        "clave": "bodega", "nombre_app": "BodegaControl", "patron": "inventario",
        "titulo": "Gestor de bodega de una distribuidora",
        "contexto": "Una distribuidora controla su bodega con guías en papel; no sabe el stock real por producto, despacha sin existencias, no detecta quiebres a tiempo y no puede valorizar el inventario.",
        "actores": ["Jefe de bodega", "Operario", "Vendedor", "Administrador TI"],
        "procesos": ["Maestro de productos", "Recepción de mercadería", "Despachos", "Ajustes de inventario", "Respaldo del inventario"],
        "padre": {"tabla": "productos", "titulo": "Productos", "singular": "producto", "campos": [
            ("nombre", "text", "Nombre"), ("codigo", "text", "Código"), ("ubicacion", "text", "Ubicación (pasillo/rack)")]},
        "hijo": {"tabla": "movimientos", "titulo": "Movimientos", "singular": "movimiento", "fk": "producto_id", "campos": [
            ("documento", "text", "Guía / factura"), ("detalle", "text", "Proveedor / cliente")]},
        "vocab": {"tipos": [["Recepción", 1], ["Despacho", -1], ["Ajuste negativo", -1]], "venta": "Despacho", "precio": True, "unidad": "unidades"},
    },
    {
        "clave": "hostal", "nombre_app": "HostalCoquimbo", "patron": "reservas",
        "titulo": "Reservas de hostal turístico",
        "contexto": "Un hostal de Coquimbo gestiona habitaciones y reservas en un cuaderno y redes sociales; se producen sobreventas de la misma habitación, no se controla el check-out y los datos de huéspedes no tienen protección.",
        "actores": ["Recepcionista", "Dueña del hostal", "Huésped", "Administrador TI"],
        "procesos": ["Registro de habitaciones", "Reserva de estadías", "Consulta de disponibilidad", "Check-out", "Respaldo de reservas"],
        "padre": {"tabla": "habitaciones", "titulo": "Habitaciones", "singular": "habitación", "campos": [
            ("numero", "text", "Número"), ("tipo", "select:Single|Doble|Familiar", "Tipo"), ("tarifa", "number", "Tarifa por noche (CLP)")]},
        "hijo": {"tabla": "reservas", "titulo": "Reservas", "singular": "reserva", "fk": "habitacion_id", "campos": [
            ("huesped", "text", "Huésped"), ("documento", "text", "Documento"), ("telefono", "tel", "Teléfono")]},
        "vocab": {"modo": "rango", "completar": "Check-out"},
    },
    {
        "clave": "laboratorio", "nombre_app": "LabPresta", "patron": "prestamos",
        "titulo": "Préstamo de equipos de laboratorio",
        "contexto": "El laboratorio de redes de una sede presta equipos (routers, switches, osciloscopios) con una hoja de firma; hay equipos extraviados, no se detectan atrasos y no se sabe quién tiene cada uno.",
        "actores": ["Pañolero", "Docente", "Estudiante", "Administrador TI"],
        "procesos": ["Inventario de equipos", "Préstamo", "Devolución", "Control de atrasos y mantención", "Respaldo del inventario"],
        "padre": {"tabla": "equipos", "titulo": "Equipos", "singular": "equipo", "campos": [
            ("nombre", "text", "Nombre"), ("codigo", "text", "Código de inventario"), ("tipo", "select:Router|Switch|Osciloscopio|Multímetro|Otro", "Tipo")]},
        "hijo": {"tabla": "prestamos", "titulo": "Préstamos", "singular": "préstamo", "fk": "equipo_id", "campos": [
            ("solicitante", "text", "Solicitante"), ("asignatura", "text", "Asignatura / curso")]},
        "vocab": {"dias": 3},
    },
    {
        "clave": "heladeria", "nombre_app": "HeladoFresco", "patron": "inventario",
        "titulo": "Producción y ventas de heladería artesanal",
        "contexto": "Una heladería artesanal anota producción y ventas en una libreta; se queda sin sabores en horario peak, no sabe qué sabores se venden más, las mermas no se registran y no tiene respaldo.",
        "actores": ["Dueña", "Heladero", "Cajero", "Administrador TI"],
        "procesos": ["Carta de sabores", "Producción diaria", "Ventas", "Control de mermas", "Respaldo de registros"],
        "padre": {"tabla": "sabores", "titulo": "Sabores", "singular": "sabor", "campos": [
            ("nombre", "text", "Sabor"), ("tipo", "select:Crema|Agua|Sin azúcar|Vegano", "Tipo")]},
        "hijo": {"tabla": "movimientos", "titulo": "Producción y ventas", "singular": "movimiento", "fk": "sabor_id", "campos": [
            ("detalle", "text", "Observación")]},
        "vocab": {"tipos": [["Producción", 1], ["Venta", -1], ["Merma", -1]], "venta": "Venta", "precio": True, "unidad": "porciones"},
    },
    {
        "clave": "datacenter", "nombre_app": "ContinuaDC", "patron": "ordenes",
        "titulo": "Gestión de continuidad operativa de data center",
        "contexto": "El data center de una empresa regional gestiona sus incidentes por correo y planillas; no conoce el RTO de cada activo crítico, no mide tiempos de recuperación y no puede demostrar continuidad operativa ante una auditoría.",
        "actores": ["Jefe de operaciones", "Operador de turno", "Encargado de continuidad", "Administrador TI"],
        "procesos": ["Inventario de activos críticos", "Registro de incidentes", "Contención y recuperación", "Medición de tiempos (MTTR vs RTO)", "Respaldo de registros"],
        "padre": {"tabla": "activos", "titulo": "Activos críticos", "singular": "activo", "campos": [
            ("nombre", "text", "Nombre"), ("tipo", "select:Servidor|Almacenamiento|Enlace|UPS|Climatización|Aplicación", "Tipo"),
            ("criticidad", "select:Alta|Media|Baja", "Criticidad"), ("rto_horas", "number", "RTO (horas)")]},
        "hijo": {"tabla": "incidentes", "titulo": "Incidentes", "singular": "incidente", "fk": "activo_id", "campos": [
            ("titulo", "text", "Título"), ("tipo_evento", "select:Falla de hardware|Corte eléctrico|Caída de enlace|Ciberincidente|Error humano", "Tipo de evento"),
            ("descripcion", "textarea", "Descripción e impacto")]},
        "vocab": {"estados": ["Detectado", "En contención", "En recuperación", "Recuperado", "Cerrado"], "nivel": "Severidad",
                  "niveles": ["S4 Menor", "S3 Moderada", "S2 Alta", "S1 Crítica"], "monto": "", "rto": "rto_horas"},
    },
    {
        "clave": "armado", "nombre_app": "ArmaTech", "patron": "ordenes",
        "titulo": "Diseño y armado de equipos de cómputo",
        "contexto": "Una tienda de armado de computadores cotiza por WhatsApp y anota los armados en una pizarra; se pierden configuraciones, no se sabe en qué etapa está cada equipo, se entregan equipos sin prueba de estrés y el cliente no entiende qué hace cada componente que paga.",
        "actores": ["Técnico armador", "Vendedor", "Cliente", "Administrador TI"],
        "procesos": ["Registro de clientes", "Diseño de la configuración", "Armado y pruebas térmicas", "Entrega con explicación de componentes", "Respaldo de configuraciones"],
        "padre": {"tabla": "clientes", "titulo": "Clientes", "singular": "cliente", "campos": [
            ("nombre", "text", "Nombre"), ("telefono", "tel", "Teléfono"), ("email", "email", "Correo")]},
        "hijo": {"tabla": "armados", "titulo": "Armados", "singular": "armado", "fk": "cliente_id", "campos": [
            ("uso", "select:Oficina|Gaming|Diseño y video|Servidor doméstico", "Uso principal"),
            ("cpu", "select:6 núcleos|8 núcleos|12 núcleos|16 núcleos", "Procesador"),
            ("gpu", "select:Integrada|Gama media|Gama alta", "Tarjeta gráfica"),
            ("ram", "select:16 GB|32 GB|64 GB", "Memoria RAM"),
            ("refrigeracion", "select:Aire estándar|Aire torre doble|Líquida 240 mm|Líquida 360 mm", "Refrigeración"),
            ("notas", "textarea", "Notas de diseño")]},
        "vocab": {"estados": ["Cotizado", "Aprobado", "En armado", "Prueba de estrés", "Entregado"], "nivel": "Prioridad",
                  "niveles": ["Normal", "Preferente", "Urgente"], "monto": "Valor del equipo (CLP)", "rto": "", "vista_equipo": True},
    },
]

# Requerimientos funcionales por patrón (se completan con el vocabulario de cada temática)
RF_PATRON = {
    "inventario": [
        ("Registrar {P} con stock mínimo{precio}; el stock solo cambia mediante movimientos.", "SI-10"),
        ("Registrar movimientos ({tipos}) asociados a un {p} existente, actualizando el stock en una transacción.", "SI-10"),
        ("Rechazar salidas que dejen el stock negativo, informando el stock disponible.", "SI-10"),
        ("Mostrar alertas de stock crítico y la valorización del inventario.", "AC-3"),
        ("Reportar movimientos por día y los {P2} con más salidas; exportar a CSV.", "AU-2"),
    ],
    "reservas": [
        ("Registrar {P} y desactivarlos sin borrar su historial.", "SI-10"),
        ("Registrar {h} para un {p} en {franja}, sin permitir fechas pasadas.", "SI-10"),
        ("Impedir dos {H2} confirmadas del mismo {p} que se crucen ({regla}).", "SI-10"),
        ("Consultar disponibilidad por fecha y marcar cada {h} como cancelada o {completar}.", "AC-3"),
        ("Reportar ocupación por {p}, agenda del día y tasa de cancelación; exportar a CSV.", "AU-2"),
    ],
    "prestamos": [
        ("Registrar {P} con estado (Disponible, Prestado, Mantención).", "SI-10"),
        ("Prestar solo {P2} disponibles, con fecha de compromiso de devolución.", "SI-10"),
        ("Registrar la devolución y liberar el {p} automáticamente.", "SI-10"),
        ("Detectar préstamos atrasados y enviar {P2} a mantención.", "AC-3"),
        ("Reportar {P2} más prestados y préstamos por solicitante; exportar a CSV.", "AU-2"),
    ],
    "ordenes": [
        ("Registrar {P} y abrir {H2} asociados con {nivel} y descripción.", "SI-10"),
        ("Avanzar cada {h} por su flujo de estados ({estados}) sin retroceder.", "AC-3"),
        ("Registrar fecha de cierre y calcular el tiempo de resolución{extra}.", "AU-2"),
        ("Filtrar por estado y {nivel} y destacar los casos críticos abiertos.", "AC-3"),
        ("Reportar casos por estado, por {nivel} y tiempo promedio de cierre; exportar a CSV.", "AU-2"),
    ],
    "membresias": [
        ("Registrar {P} con valor y duración en días.", "SI-10"),
        ("Inscribir {H2} en un {p} calculando automáticamente la fecha de término.", "SI-10"),
        ("Renovar, suspender y reactivar {H2}, recalculando la vigencia.", "AC-3"),
        ("Mostrar {H2} vigentes, vencidos y por vencer en 7 días.", "AC-3"),
        ("Reportar {H2} por {p} e ingreso mensual estimado; exportar a CSV.", "AU-2"),
    ],
}
