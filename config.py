# ═══════════════════════════════════════════════════════════════════
#  config.py — Panel de Control · Placas_a_Telegram
#  Inversiones & Algoritmos
#
#  ESTE ES EL ÚNICO ARCHIVO QUE NECESITÁS EDITAR para:
#  · Agregar / quitar activos del Visor ARG
#  · Cambiar fuentes de datos (URLs de APIs)
#  · Modificar horarios de envío
#  · Ajustar el diseño visual de las tarjetas (colores, tamaños)
#  · Configurar capturas de pantalla web (generar_Imagen_ARG)
#  · Configurar el Visor BCRA
# ═══════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────
# 1. FUENTES DE DATOS — URLs de las APIs
# ───────────────────────────────────────────────────────────────────

APIS = {
    "ADR":           "https://data912.com/live/usa_adrs",
    "STOCKS":        "https://data912.com/live/arg_stocks",
    "CEDEARS":       "https://data912.com/live/arg_cedears",
    "BONOS":         "https://data912.com/live/arg_bonds",   # AL30, GD30, etc.
    "FERIADOS":      "https://api.argentinadatos.com/v1/feriados/2026",
    "RIESGO_PAIS":   "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
    # ── Visor BCRA — API oficial v4.0 via bcra-connector ──────────
    # Sin token. pip install bcra-connector. verify_ssl=False nativo.
    "BCRA_BASE":     "https://api.bcra.gob.ar",
}


# ───────────────────────────────────────────────────────────────────
# 2. VISOR ARG — Activos a mostrar en la tarjeta PNG
# ───────────────────────────────────────────────────────────────────
# Estructura de cada par:
#   "TICKER_US": { "fuente_us": clave de APIS,
#                  "ticker_ba": símbolo en BYMA / arg_stocks,
#                  "fuente_ba": clave de APIS,
#                  "nombre":    nombre corto a mostrar }
#
# Para agregar un nuevo par: copiar un bloque y ajustar los campos.
# Para quitar uno: comentar o borrar el bloque.
# Si un activo no tiene par local (BA), dejar "ticker_ba": None.

# ───────────────────────────────────────────────────────────────────
# 2. VISOR ARG — 3 columnas independientes
# ───────────────────────────────────────────────────────────────────
# Cada columna es una lista independiente de activos.
# Para agregar: sumar una línea con ("TICKER", "Nombre corto")
# Para quitar:  comentar o borrar la línea
# Para cambiar nombre de columna: editar el campo "cabecera"

VISOR_ARG_COL1 = {
    # ── Columna 1: ADR'S / USD — ADRs argentinos en NYSE ──────────
    "cabecera": "ADR'S / USD",
    "fuente":   "ADR",           # → https://data912.com/live/usa_adrs
    "activos": [
        ("GGAL",  "Galicia"),
        ("BMA",   "Bco Macro"),
        ("SUPV",  "Supervielle"),
        ("YPF",   "YPF"),
        ("PAM",   "Pampa"),
    ],
}

VISOR_ARG_COL2 = {
    # ── Columna 2: BYMA / $ — Acciones locales en pesos ───────────
    "cabecera": "BYMA / $",
    "fuente":   "STOCKS",        # → https://data912.com/live/arg_stocks
    "activos": [
        ("GGAL",  "Galicia"),
        ("BMA",   "Bco Macro"),
        ("SUPV",  "Supervielle"),
        ("YPFD",  "YPF"),        # en BYMA cotiza como YPFD
        ("PAMP",  "Pampa"),      # en BYMA cotiza como PAMP
        ("TRAN",  "Transener"),
    ],
}

VISOR_ARG_COL3 = {
    # ── Columna 3: CEDEARS / $ — CEDEARs en pesos en BYMA ─────────
    "cabecera": "CEDEARS / $",
    "fuente":   "CEDEARS",       # → https://data912.com/live/arg_cedears
    "activos": [
        ("PAGS",  "PagSeguro"),
        ("ORCL",  "Oracle"),
        ("NU",    "Nu Holdings"),
        ("VIST",  "Vista Energy"),
        ("PBR",   "Petrobras"),   # en data912 puede ser PBR o PBRD
        ("MELI",  "MercadoLibre"),
    ],
}


# ───────────────────────────────────────────────────────────────────
# 3. CAPTURAS DE PANTALLA WEB — generar_Imagen_ARG()
# ───────────────────────────────────────────────────────────────────
# Cada entrada = una URL → una imagen → un mensaje a Telegram.
#
# Campos:
#   url            → página a abrir con Playwright
#   wait_selector  → CSS a esperar antes de capturar (gráficos JS)
#   crop_selector  → elemento CSS a recortar
#   zoom           → factor de ampliación
#   delay_ms       → ms extra para que el canvas JS termine de dibujar
#   caption_key    → clave en MENSAJES para el texto base del caption
#   ticker_api     → símbolo a buscar en APIS["BONOS"] para precio dinámico
#                    None = caption estático sin precio
#   fuente_api     → clave en APIS donde buscar el ticker (default "BONOS")
#   activo         → True/False para activar/desactivar sin borrar
#
# Caption dinámico: si ticker_api está definido, el bot busca el precio
# en la API y reemplaza {precio} y {variacion} en el texto de MENSAJES.
# Ejemplo: "📈 AL30: ${precio} ({variacion}%)" → "📈 AL30: $91,320 (+1.01%)"

CAPTURAS_WEB = {

    # ── CAUCIÓN 1D — MAE A3 ───────────────────────────────────────
    "CAUCION_1D_MAE": {
        "url":           "https://marketdata.mae.com.ar/cauciones",
        "wait_selector": "div.tv-lightweight-charts",
        "crop_selector": "div.relative.h-full",
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption_key":   "caucion_caption",
        "ticker_api":    None,          # sin precio dinámico
        "activo":        True,
    },

    # ── DÓLAR MEP (USMEP) — MAE A3 ────────────────────────────────
    "USMEP_MAE": {
        "url":           "https://marketdata.mae.com.ar/titulos/FOR/USMEP?plazo=000&segmento=M&moneda=T",
        "wait_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "crop_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption_key":   "usmep_caption",
        "ticker_api":    None,
        "activo":        True,
    },

    # ── AL30 Intradiario — IOL ────────────────────────────────────
    "AL30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/AL30/BONO-REP.-ARGENTINA-USD-STEP-UP-2030/",
        "wait_selector": "#graficoIntradiario svg.highcharts-root",
        "crop_selector": "#graficoIntradiario",
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "al30_caption",
        "ticker_api":    "AL30",        # busca precio en APIS["BONOS"]
        "activo":        True,
    },

    # ── GD30 Intradiario — IOL ────────────────────────────────────
    "GD30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/GD30/BONOS-REP.-ARG.-U-S-STEP-UP-V.09-07-30/",
        "wait_selector": ".highcharts-container svg.highcharts-root",
        "crop_selector": ".highcharts-container",
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "gd30_caption",
        "ticker_api":    "GD30",        # busca precio en APIS["BONOS"]
        "activo":        True,
    },

    # ── AL30 Intradiario — RAVA ───────────────────────────────────
    # Alternativa a IOL. Rava usa TradingView embebido con ID estable.
    # Activar cambiando "activo": True (y opcionalmente desactivar AL30_IOL)
    "AL30_RAVA": {
        "url":           "https://www.rava.com/perfil/AL30",
        "wait_selector": "#grafico_tradingview",
        "crop_selector": "#grafico_tradingview",
        "zoom":          2.0,
        "delay_ms":      6000,          # Rava puede tardar más en renderizar
        "caption_key":   "al30_caption",
        "ticker_api":    "AL30",
        "activo":        False,         # ← cambiar a True para activar
    },

    # ── Agregar más capturas aquí ──────────────────────────────────
    # "GD30_RAVA": {
    #     "url":           "https://www.rava.com/perfil/GD30",
    #     "wait_selector": "#grafico_tradingview",
    #     "crop_selector": "#grafico_tradingview",
    #     "zoom":          2.0,
    #     "delay_ms":      6000,
    #     "caption_key":   "gd30_caption",
    #     "ticker_api":    "GD30",
    #     "activo":        False,
    # },
}

# ───────────────────────────────────────────────────────────────────
# 4. # ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — API oficial BCRA v4.0 via bcra-connector
# ───────────────────────────────────────────────────────────────────
# Librería: bcra-connector (pip install bcra-connector)
#   → verify_ssl=False nativo, sin SSL issues en GitHub Actions
#   → sin token, sin registro, sin límite de consultas
#   → datos oficiales y actualizados del BCRA
#
# IDs v4.0 según documentación oficial BCRA:
#   1  → Reservas Internacionales (millones USD)   T-2
#   4  → USD Oficial A3500                         T+0
#   6  → Base Monetaria (millones $)               T-2
#   7  → Tasa BADLAR TNA (%)                       T+0
#   15 → CER                                       T+0
#   34 → Tasa Política Monetaria TNA (%)           T+0
#
# id_var = None        → Riesgo País (argentinadatos.com)
# id_var = int         → variable directa bcra-connector
# id_var = "calc:X/Y"  → ratio calculado entre ID X e ID Y
#
# Formatos: "bps", "usd4", "usd_m", "pesos_m", "pct2", "num6", "ratio"

VISOR_BCRA_ITEMS = [
    # id_var        Etiqueta           Col   Formato
    (None,          "RIESGO PAIS",    "T0", "bps"),    # argentinadatos.com
    (4,             "USD A3500",      "T0", "usd4"),   # USD Oficial Mayorista
    (15,            "CER",            "T0", "num6"),   # Coef. Estab. Referencia
    (7,             "BADLAR",         "T0", "pct2"),   # Tasa BADLAR TNA
    (34,            "TASA POL.MON.",  "T0", "pct2"),   # Tasa Política Monetaria
    (1,             "RESERVAS INTER", "T2", "usd_m"),  # Millones USD (T-2)
    (6,             "BASE MONETARIA", "T2", "pesos_m"),# Millones $ (T-2)
    ("calc:6/1",    "B.MON / R.IN",   "T2", "ratio"),  # Base / Reservas
    ("calc:6/4",    "B.MON / USD.OF", "T2", "pesos_m"),# Base / USD Oficial
]


# ───────────────────────────────────────────────────────────────────
# 5. HORARIOS DE EJECUCIÓN (hora Argentina)
# ───────────────────────────────────────────────────────────────────
# Tolerancia de detección: ±29 minutos (cubre el delay de GitHub Actions)

HORARIOS = {
    "imagen_1":      "12:00",   # generar_Imagen_ARG → "Merval Abierto"
    "visor_arg_1":   "13:00",   # Visor ARG
    "imagen_2":      "14:00",   # generar_Imagen_ARG → "Merval Abierto"
    "visor_arg_2":   "15:00",   # Visor ARG
    "imagen_3":      "16:00",   # generar_Imagen_ARG → "Merval Abierto"
    "imagen_cierre": "17:00",   # generar_Imagen_ARG → "Merval Cerrado"
    "visor_arg_3":   "17:00",   # Visor ARG final
    "visor_bcra":    "17:30",   # Visor BCRA (único envío del día)
}


# ───────────────────────────────────────────────────────────────────
# 6. ARCHIVOS TEMPORALES
# ───────────────────────────────────────────────────────────────────

ARCHIVOS = {
    "estado_envios": "estado_envios.csv",
    "visor_arg_img": "visor_arg.png",
    "visor_bcra_img": "visor_bcra.png",
}


# ───────────────────────────────────────────────────────────────────
# 7. DISEÑO VISUAL — Tarjeta Visor ARG (Pillow)
# ───────────────────────────────────────────────────────────────────
# ╔══════════════════════════════════════════════════════╗
# ║  GUÍA RÁPIDA PARA EDITAR LA ESTÉTICA DEL VISOR ARG  ║
# ╚══════════════════════════════════════════════════════╝
#
# ── TAMAÑOS DE LETRA ────────────────────────────────────
#   "font_header"  → título "VISOR ARG" del header principal
#   "font_sub"     → subtítulo hora/fecha debajo del header
#   "font_col_hdr" → cabeceras de columna (ADR'S/USD, BYMA/$, CEDEARS/$)
#   "font_ticker"  → nombre del ticker dentro de cada tarjeta (ej: GGAL)
#   "font_nombre"  → nombre corto debajo del ticker (ej: Galicia)
#   "font_precio"  → precio en grande (ej: $47.81)
#   "font_pct"     → variación % con flecha (ej: ▼ -2.03%)
#
# ── COLORES ─────────────────────────────────────────────
#   Usar formato hex "#RRGGBB"
#   "bg_canvas"  → fondo general de toda la imagen
#   "bg_card"    → fondo de cada tarjeta de activo
#   "bg_header"  → fondo del header "VISOR ARG"
#   "border"     → bordes de tarjetas y header
#   "accent"     → color del título "VISOR ARG"
#   "text_white" → texto principal (tickers, precios)
#   "text_muted" → texto secundario (nombres, hora, fuente)
#   "up"         → color cuando el precio sube (verde)
#   "down"       → color cuando el precio baja (rojo)
#   "neutral"    → color cuando no cambia (gris)
#
# ── DIMENSIONES ─────────────────────────────────────────
#   "card_w" → ancho de cada tarjeta (px). Las 3 columnas
#              tendrán este ancho. Aumentar si el precio no entra.
#   "card_h" → alto de cada tarjeta. Aumentar si el texto se superpone.
#   "gap"    → separación entre tarjetas (px)
#   "margin" → margen exterior de toda la imagen (px)
#   "padding"→ espacio interno dentro de cada tarjeta (px)
#
# ── NOMBRE DE LA TARJETA ────────────────────────────────
#   El título "VISOR ARG" se define en MENSAJES["visor_arg_titulo"]
#   El subtítulo muestra hora y fecha automáticamente.
#   La fuente "data912.com" se muestra en el footer.

DISEÑO_VISOR_ARG = {
    # ── Dimensiones ──────────────────────────────────────
    "card_w":      220,    # ancho de cada tarjeta (3 columnas × 220px)
    "card_h":      100,    # alto de cada tarjeta
    "padding":     12,     # espacio interno de tarjeta
    "gap":         5,      # separación entre tarjetas
    "margin":      18,     # margen exterior del canvas
    "col_gap":     8,      # separación entre columnas

    # ── Colores ──────────────────────────────────────────
    "bg_canvas":   "#0d1117",   # fondo general (negro oscuro)
    "bg_card":     "#161b22",   # fondo de tarjeta
    "bg_header":   "#1c2128",   # fondo del header principal
    "bg_col_hdr":  "#21262d",   # fondo de cabecera de columna
    "border":      "#30363d",   # bordes
    "accent":      "#388bfd",   # azul acento (título VISOR ARG)
    "col_accent":  "#58a6ff",   # color texto de cabeceras de columna
    "text_white":  "#e6edf3",   # texto principal
    "text_muted":  "#8b949e",   # texto secundario
    "up":          "#3fb950",   # verde (precio sube)
    "down":        "#f85149",   # rojo (precio baja)
    "neutral":     "#8b949e",   # gris (sin cambio)

    # ── Tamaños de letra ─────────────────────────────────
    "font_header":  19,    # título "VISOR ARG" en el header
    "font_sub":     11,    # subtítulo hora/fecha
    "font_col_hdr": 12,    # cabeceras de columna
    "font_ticker":  15,    # ticker del activo (ej: GGAL)
    "font_nombre":  10,    # nombre corto (ej: Galicia)
    "font_precio":  17,    # precio en grande
    "font_pct":     13,    # variación % con flecha
}


# ───────────────────────────────────────────────────────────────────
# 8. DISEÑO VISUAL — Tarjeta Visor BCRA (Pillow)
# ───────────────────────────────────────────────────────────────────
# ╔═══════════════════════════════════════════════════════╗
# ║  GUÍA RÁPIDA PARA EDITAR LA ESTÉTICA DEL VISOR BCRA  ║
# ╚═══════════════════════════════════════════════════════╝
#
# ── TAMAÑOS DE LETRA ────────────────────────────────────
#   "font_header" → título "VISOR BCRA" del header (el más grande)
#   "font_sub"    → subtítulo "Fuente: BCRA — DD/MM/YYYY"
#   "font_label"  → etiquetas de fila (RIESGO PAIS, USD A3500, etc.)
#   "font_value"  → valores numéricos en cada celda
#
# ── COLORES ─────────────────────────────────────────────
#   "bg"          → fondo celeste de la tarjeta
#   "header_bg"   → fondo azul del header
#   "header_text" → texto del header (blanco)
#   "label_color" → color de etiquetas de fila
#   "value_t0"    → color valores columna T+0 (hoy)
#   "value_t2"    → color valores columna T-2 (48hs)
#   "divider"     → color de líneas separadoras
#
# ── DIMENSIONES ─────────────────────────────────────────
#   "width"      → ancho total de la tarjeta (px)
#   "row_height" → alto de cada fila de datos
#   "padding"    → margen interior general
#
# ── NOMBRE DE LA TARJETA ────────────────────────────────
#   El título "VISOR BCRA" se define en MENSAJES["visor_bcra_titulo"]

DISEÑO_VISOR_BCRA = {
    "width":       700,
    "bg":          "#dbeafe",
    "border":      "#1e40af",
    "header_bg":   "#1e40af",
    "header_text": "#ffffff",
    "col_header":  "#1e3a5f",
    "label_color": "#1e3a5f",
    "value_t0":    "#1e3a5f",
    "value_t2":    "#1e40af",
    "divider":     "#93c5fd",
    "font_header": 22,
    "font_sub":    13,
    "font_label":  14,
    "font_value":  14,
    "row_height":  38,
    "padding":     24,
}


# ───────────────────────────────────────────────────────────────────
# 9. MENSAJES TELEGRAM
# ───────────────────────────────────────────────────────────────────
# ╔══════════════════════════════════════════════════════════════╗
# ║  ACÁ CAMBIÁS LOS TEXTOS QUE APARECEN EN LOS MENSAJES        ║
# ║  DE TELEGRAM Y EN LOS TÍTULOS DE LAS TARJETAS               ║
# ╚══════════════════════════════════════════════════════════════╝

MENSAJES = {
    # ── Captions de las capturas web (Playwright) ─────────────────
    # Captions estáticos (sin ticker_api): texto fijo
    "caucion_caption":  "📊 Caución 1D — MAE A3",
    "usmep_caption":    "💵 Dólar MEP (USMEP) — MAE A3",

    # Captions dinámicos (con ticker_api): usan {precio} y {variacion}
    # El bot reemplaza automáticamente con el precio real de la API
    # Ejemplo resultado: "📈 AL30 Intradiario: $91,320.00 (+1.01%)"
    "al30_caption":     "📈 AL30 Intradiario: ${precio} ({variacion}%)",
    "gd30_caption":     "📈 GD30 Intradiario: ${precio} ({variacion}%)",

    # ── Estado del mercado ────────────────────────────────────────
    "merval_abierto":   "🟢 Merval Abierto",
    "merval_cerrado":   "🔴 Merval Cerrado",

    # ── Títulos de las tarjetas PNG ───────────────────────────────
    "visor_arg_titulo":  "🇦🇷  VISOR ARG",
    "visor_bcra_titulo": "VISOR BCRA",

    # ── Captions de Telegram para Visor ARG y BCRA ───────────────
    "visor_arg_tg":     "🇦🇷 Visor ARG",
    "visor_bcra_tg":    "🏦 Visor BCRA",
    "fuente_datos":     "Fuente: data912.com",
}
