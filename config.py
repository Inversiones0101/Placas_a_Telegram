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
    "ADR":       "https://data912.com/live/usa_adrs",
    "STOCKS":    "https://data912.com/live/arg_stocks",
    "CEDEARS":   "https://data912.com/live/arg_cedears",
    "FERIADOS":  "https://api.argentinadatos.com/v1/feriados/2026",
    "RIESGO_PAIS": "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
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
#   zoom           → factor de ampliación (1.8 = x1.8)
#   delay_ms       → ms extra para que el canvas JS termine de dibujar
#   caption        → texto del mensaje en Telegram
#   activo         → True/False para activar/desactivar sin borrar

CAPTURAS_WEB = {

    # ── CAUCIÓN 1D — MAE A3 ───────────────────────────────────────
    "CAUCION_1D_MAE": {
        "url":           "https://marketdata.mae.com.ar/cauciones",
        "wait_selector": "div.tv-lightweight-charts",
        "crop_selector": "div.relative.h-full",
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption":       "📊 Caución 1D — MAE A3",
        "activo":        True,
    },

    # ── DÓLAR MEP (USMEP) — MAE A3 ────────────────────────────────
    "USMEP_MAE": {
        "url":           "https://marketdata.mae.com.ar/titulos/FOR/USMEP?plazo=000&segmento=M&moneda=T",
        "wait_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "crop_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption":       "💵 Dólar MEP (USMEP) — MAE A3",
        "activo":        True,
    },

    # ── AL30 Intradiario — IOL ────────────────────────────────────
    "AL30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/AL30/BONO-REP.-ARGENTINA-USD-STEP-UP-2030/",
        "wait_selector": "#graficoIntradiario svg.highcharts-root",
        "crop_selector": "#graficoIntradiario",
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption":       "📈 AL30 Intradiario — IOL",
        "activo":        True,
    },

    # ── GD30 Intradiario — IOL ────────────────────────────────────
    "GD30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/GD30/BONOS-REP.-ARG.-U-S-STEP-UP-V.09-07-30/",
        "wait_selector": ".highcharts-container svg.highcharts-root",
        "crop_selector": ".highcharts-container",
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption":       "📈 GD30 Intradiario — IOL",
        "activo":        True,
    },

    # ── Agregar más capturas aquí ──────────────────────────────────
    # "MERVAL_IOL": {
    #     "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/IMV/INDICE-MERVAL/",
    #     "wait_selector": "svg.highcharts-root",
    #     "crop_selector": "svg.highcharts-root",
    #     "zoom":          2.2,
    #     "delay_ms":      5000,
    #     "caption":       "📊 Merval Intradiario — IOL",
    #     "activo":        False,
    # },
}

# ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — Variables del Banco Central
# ───────────────────────────────────────────────────────────────────
# Cada ítem: (ID_bcra_wrapper, "Etiqueta", columna "T0"/"T2", es_calculado)
# IDs: 1=Reservas, 2=BADLAR, 4=USD Ofic, 6=Base Mon,
#      10=CER, 11=Depositos, 12=Prestamos, 13=TAMAR

VISOR_BCRA_ITEMS = [
    (None,        "RIESGO PAIS",    "T0", False),  # argentinadatos.com
    (4,           "USD A3500",      "T0", False),
    (10,          "CER",            "T0", False),
    (2,           "BADLAR",         "T0", False),
    (13,          "TAMAR",          "T0", False),
    (1,           "RESERVAS INTER", "T2", False),
    (6,           "BASE MONETARIA", "T2", False),
    ("6/1",       "B.MON / R.IN",   "T2", True),
    ("6/4",       "B.MON / USD.OF", "T2", True),
    ("12/11*100", "PREST / DEPOS",  "T2", True),
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
    # Lo que aparece debajo de cada imagen en el chat de Telegram
    "caucion_caption":  "📊 Caución 1D",          # ← cambiá el texto acá
    "usmep_caption":    "💵 Dólar MEP",
    "al30_caption":     "📈 AL30 Intradiario",
    "gd30_caption":     "📈 GD30 Intradiario",

    # ── Estado del mercado ────────────────────────────────────────
    "merval_abierto":   "🟢 Merval Abierto",       # ← mensaje cuando el mercado está abierto
    "merval_cerrado":   "🔴 Merval Cerrado",        # ← mensaje cuando cierra

    # ── Títulos de las tarjetas PNG ───────────────────────────────
    "visor_arg_titulo": "🇦🇷  VISOR ARG",           # ← título en el header de la tarjeta
    "visor_bcra_titulo": "VISOR BCRA",              # ← título en el header de la tarjeta BCRA

    # ── Captions de Telegram para Visor ARG y BCRA ───────────────
    "visor_arg_tg":     "🇦🇷 Visor ARG",           # ← texto del mensaje en Telegram
    "visor_bcra_tg":    "🏦 Visor BCRA",
    "fuente_datos":     "Fuente: data912.com",
}
