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
    "BONOS":         "https://data912.com/live/arg_bonds",
    "FERIADOS":      "https://api.argentinadatos.com/v1/feriados/",
    "RIESGO_PAIS":   "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
    "BCRA_BASE":     "https://api.bcra.gob.ar",
}


# ───────────────────────────────────────────────────────────────────
# 2. VISOR ARG — 3 columnas independientes
# ───────────────────────────────────────────────────────────────────

VISOR_ARG_COL1 = {
    "cabecera": "ADR'S / USD",
    "fuente":   "ADR",
    "activos": [
        ("GGAL",  "Galicia"),
        ("BMA",   "Bco Macro"),
        ("SUPV",  "Supervielle"),
        ("YPF",   "YPF"),
        ("PAM",   "Pampa"),
    ],
}

VISOR_ARG_COL2 = {
    "cabecera": "BYMA / $",
    "fuente":   "STOCKS",
    "activos": [
        ("GGAL",  "Galicia"),
        ("BMA",   "Bco Macro"),
        ("SUPV",  "Supervielle"),
        ("YPFD",  "YPF"),
        ("PAMP",  "Pampa"),
        ("TRAN",  "Transener"),
    ],
}

VISOR_ARG_COL3 = {
    "cabecera": "CEDEARS / $",
    "fuente":   "CEDEARS",
    "activos": [
        ("PAGS",  "PagSeguro"),
        ("ORCL",  "Oracle"),
        ("NU",    "Nu Holdings"),
        ("VIST",  "Vista Energy"),
        ("PBR",   "Petrobras"),
        ("MELI",  "MercadoLibre"),
    ],
}


# ───────────────────────────────────────────────────────────────────
# 3. CAPTURAS DE PANTALLA WEB — generar_Imagen_ARG()
# ───────────────────────────────────────────────────────────────────

CAPTURAS_WEB = {

    "CAUCION_1D_MAE": {
        "url":           "https://marketdata.mae.com.ar/cauciones",
        "wait_selector": "div.tv-lightweight-charts",
        "crop_selector": "div.relative.h-full",
        "iframe_selector": None,
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption_key":   "caucion_caption",
        "ticker_api":    None,
        "activo":        True,
    },

    "USMEP_MAE": {
        "url":           "https://marketdata.mae.com.ar/titulos/FOR/USMEP?plazo=000&segmento=M&moneda=T",
        "wait_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "crop_selector": "div.grid.grid-cols-1.gap-3.mt-2",
        "iframe_selector": None,
        "zoom":          1.8,
        "delay_ms":      4000,
        "caption_key":   "usmep_caption",
        "ticker_api":    None,
        "activo":        True,
    },

    "AL30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/AL30/BONO-REP.-ARGENTINA-USD-STEP-UP-2030/",
        "wait_selector": "#graficoIntradiario svg.highcharts-root",
        "crop_selector": "#graficoIntradiario",
        "iframe_selector": None,
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "al30_caption",
        "ticker_api":    "AL30",
        "activo":        False,
    },

    "GD30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/GD30/BONOS-REP.-ARG.-U-S-STEP-UP-V.09-07-30/",
        "wait_selector": ".highcharts-container svg.highcharts-root",
        "crop_selector": ".highcharts-container",
        "iframe_selector": None,
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "gd30_caption",
        "ticker_api":    "GD30",
        "activo":        False,
    },

    "AL30_RAVA": {
        "url":             "https://www.rava.com/perfil/AL30",
        "wait_selector":   "div.recharts-wrapper svg",
        "crop_selector":   "div.recharts-wrapper",
        "iframe_selector": None,
        "crop_box":        {"x": 0.62, "y": 0.09, "w": 0.35, "h": 0.42},
        "zoom":            2.5,
        "delay_ms":        6000,
        "caption_key":     "al30_caption",
        "ticker_api":      "AL30",
        "activo":          True,
    },

    "GD30_RAVA": {
        "url":             "https://www.rava.com/perfil/GD30",
        "wait_selector":   "div.recharts-wrapper svg",
        "crop_selector":   "div.recharts-wrapper",
        "iframe_selector": None,
        "crop_box":        {"x": 0.62, "y": 0.09, "w": 0.35, "h": 0.42},
        "zoom":            2.5,
        "delay_ms":        6000,
        "caption_key":     "gd30_caption",
        "ticker_api":      "GD30",
        "activo":          True,
    },
}


# ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — API oficial BCRA v4.0
#
# CAMBIO v2: se eliminó la columna "col" (T0/T2).
# Ahora cada fila muestra la FECHA REAL del dato según la API
# y el VALOR correspondiente. Sin distinción T0/T2 en el diseño.
#
# Formato de cada item: (id_var, etiqueta, formato)
#   id_var = None        → Riesgo País (argentinadatos.com)
#   id_var = int         → variable directa via bcra-connector
#   id_var = "calc:X/Y"  → ratio calculado entre ID X e ID Y
#            Para los calc, la fecha mostrada es la del numerador (X)
# ───────────────────────────────────────────────────────────────────

VISOR_BCRA_ITEMS = [
    # id_var          Etiqueta           Formato
    (None,            "RIESGO PAIS",     "bps"),      # argentinadatos.com
    (5,               "USD A3500",       "pesos"),    # USD Mayorista A3500
    (30,              "CER",             "num6"),     # CER
    (7,               "BADLAR",          "pct2"),     # Tasa BADLAR TNA
    (44,              "TAMAR",           "pct2"),     # Tasa TAMAR TNA
    (1,               "RESERVAS INTER",  "usd_m"),    # Reservas (millones USD)
    (15,              "BASE MONETARIA",  "pesos_m"),  # Base Monetaria
    ("calc:15/1",     "B.MON / R.IN",    "pesos"),    # Dólar Convertibilidad
    ("calc:15/5",     "B.MON / USD.OF",  "usd_m"),    # Base Monetaria en USD Oficial
]


# ───────────────────────────────────────────────────────────────────
# 5. HORARIOS DE EJECUCIÓN (hora Argentina)
# ───────────────────────────────────────────────────────────────────

HORARIOS = {
    "imagen_1":      "12:00",
    "visor_arg_1":   "13:00",
    "imagen_2":      "14:00",
    "visor_arg_2":   "15:00",
    "imagen_3":      "16:00",
    "imagen_cierre": "17:00",
    "visor_arg_3":   "17:00",
    "visor_bcra":    "17:30",
}


# ───────────────────────────────────────────────────────────────────
# 6. ARCHIVOS TEMPORALES
# ───────────────────────────────────────────────────────────────────

ARCHIVOS = {
    "estado_envios":  "estado_envios.csv",
    "visor_arg_img":  "visor_arg.png",
    "visor_bcra_img": "visor_bcra.png",
}


# ───────────────────────────────────────────────────────────────────
# 7. DISEÑO VISUAL — Tarjeta Visor ARG (Pillow)
# ───────────────────────────────────────────────────────────────────

DISEÑO_VISOR_ARG = {
    "card_w":      220,
    "card_h":      100,
    "padding":     12,
    "gap":         5,
    "margin":      18,
    "col_gap":     8,

    "bg_canvas":   "#0d1117",
    "bg_card":     "#161b22",
    "bg_header":   "#1c2128",
    "bg_col_hdr":  "#21262d",
    "border":      "#30363d",
    "accent":      "#388bfd",
    "col_accent":  "#58a6ff",
    "text_white":  "#e6edf3",
    "text_muted":  "#8b949e",
    "up":          "#3fb950",
    "down":        "#f85149",
    "neutral":     "#8b949e",

    "font_header":  19,
    "font_sub":     11,
    "font_col_hdr": 12,
    "font_ticker":  15,
    "font_nombre":  10,
    "font_precio":  17,
    "font_pct":     13,
}


# ───────────────────────────────────────────────────────────────────
# 8. DISEÑO VISUAL — Tarjeta Visor BCRA (Pillow)
# ───────────────────────────────────────────────────────────────────

DISEÑO_VISOR_BCRA = {
    "width":       700,
    "bg":          "#dbeafe",
    "border":      "#1e40af",
    "header_bg":   "#1e40af",
    "header_text": "#ffffff",
    "col_header":  "#1e3a5f",
    "label_color": "#1e3a5f",
    "value_color": "#1e40af",    # color único para VALOR (antes value_t0 / value_t2)
    "date_color":  "#374151",    # color para la columna FECHA
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

MENSAJES = {
    "caucion_caption":   "📊 Caución 1D — MAE A3",
    "usmep_caption":     "💵 Dólar MEP (USMEP) — MAE A3",
    "al30_caption":      "📈 AL30 Intradiario: {precio} ({variacion}%)",
    "gd30_caption":      "📈 GD30 Intradiario: {precio} ({variacion}%)",
    "merval_abierto":    "🟢 Mercado Abierto",
    "merval_cerrado":    "🔴 Mercado Cerrado",
    "visor_arg_titulo":  "🇦🇷  VISOR ARG",
    "visor_bcra_titulo": "VISOR BCRA",
    "visor_arg_tg":      "🇦🇷 Visor ARG",
    "visor_bcra_tg":     "🏦 Visor BCRA",
    "fuente_datos":      "Fuente: data912.com",
}
