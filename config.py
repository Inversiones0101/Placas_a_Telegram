# ═══════════════════════════════════════════════════════════════════
#  config.py — Panel de Control · Placas_a_Telegram
#  Inversiones & Algoritmos
#
#  ESTE ES EL ÚNICO ARCHIVO QUE NECESITÁS EDITAR para:
#  · Agregar / quitar activos del Visor ARG y Visor RF
#  · Cambiar fuentes de datos (URLs de APIs)
#  · Modificar horarios de envío
#  · Ajustar el diseño visual de las tarjetas (colores, tamaños)
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
    "LETRAS":        "https://data912.com/live/arg_notes",
    "MEP":           "https://data912.com/live/mep",
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
# 3. VISOR RENTA FIJA ARG
#
# Cada sección tiene:
#   titulo  → texto de la cabecera de sección
#   items   → lista de (symbol, nombre_display, fuente_api)
#             fuente_api: "BONOS", "LETRAS" o "MEP"
#
# Items MEP se muestran en dorado (tipo cambio implícito).
# Para agregar activos: editá la lista "items" de cada sección.
# Para agregar secciones: copiá un bloque y agregalo a la lista.
# ───────────────────────────────────────────────────────────────────

VISOR_RF_SECCIONES = [
    {
        "titulo": "SOBERANOS ($ & USD)",
        "items": [
            # symbol       nombre_display            fuente
            ("AL30",      "AL30 - Ley Local $",     "BONOS"),
            ("AL30D",     "AL30 - Ley Local USD",   "BONOS"),
            ("MEP/AL30",  "Tipo Cambio MEP",         "MEP"),
            ("GD30",      "GD30 - Ley NY $",        "BONOS"),
            ("GD30D",     "GD30 - Ley NY USD",      "BONOS"),
            ("MEP/GD30",  "Tipo Cambio MEP",         "MEP"),
            ("TX28",      "TX28 - Boncer CER $",    "BONOS"),
            ("TX28D",     "TX28 - Boncer USD Eq",   "BONOS"),
            ("MEP/TX28",  "TC MEP Implícito",        "MEP"),
        ],
    },
    {
        "titulo": "LETRAS $ (LECAP/LEDE)",
        "items": [
            # symbol   nombre_display      fuente
            ("S17L6",  "LECAP - 17-Jul",  "LETRAS"),
            ("S14G6",  "LECAP - 14-Ago",  "LETRAS"),
            ("S15S6",  "LECAP - 15-Sep",  "LETRAS"),
            ("S31L6",  "LEDE - 31-Jul",   "LETRAS"),
            ("S31G6",  "LEDE - 31-Ago",   "LETRAS"),
            ("S30S6",  "LEDE - 30-Sep",   "LETRAS"),
        ],
    },
]


# ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — API oficial BCRA v4.0
#
# Formato de cada item: (id_var, etiqueta, formato)
#   id_var = None        → Riesgo País (argentinadatos.com)
#   id_var = int         → variable directa via bcra-connector
#   id_var = "calc:X/Y"  → ratio calculado entre ID X e ID Y
# ───────────────────────────────────────────────────────────────────

VISOR_BCRA_ITEMS = [
    (None,            "RIESGO PAIS",     "bps"),
    (5,               "USD A3500",       "pesos"),
    (30,              "CER",             "num6"),
    (7,               "BADLAR",          "pct2"),
    (44,              "TAMAR",           "pct2"),
    (1,               "RESERVAS INTER",  "usd_m"),
    (15,              "BASE MONETARIA",  "pesos_m"),
    ("calc:15/1",     "B.MON / R.IN",    "pesos"),
    ("calc:15/5",     "B.MON / USD.OF",  "usd_m"),
]


# ───────────────────────────────────────────────────────────────────
# 5. HORARIOS DE EJECUCIÓN (hora Argentina)
# ───────────────────────────────────────────────────────────────────

HORARIOS = {
    "visor_rf_1":    "12:00",   # Visor Renta Fija — apertura
    "visor_arg_1":   "13:00",   # Visor ARG
    "visor_rf_2":    "14:00",   # Visor Renta Fija — media rueda
    "visor_arg_2":   "15:00",   # Visor ARG
    "visor_rf_3":    "16:00",   # Visor Renta Fija
    "visor_rf_4":    "17:00",   # Visor Renta Fija — cierre
    "visor_arg_3":   "17:00",   # Visor ARG final
    "visor_bcra":    "17:30",   # Visor BCRA
}


# ───────────────────────────────────────────────────────────────────
# 6. ARCHIVOS TEMPORALES
# ───────────────────────────────────────────────────────────────────

ARCHIVOS = {
    "estado_envios":  "estado_envios.csv",
    "visor_arg_img":  "visor_arg.png",
    "visor_rf_img":   "visor_rf.png",
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
# 8. DISEÑO VISUAL — Tarjeta Visor Renta Fija (Pillow)
#    Mismo estilo oscuro que Visor ARG, organizado en secciones.
# ───────────────────────────────────────────────────────────────────

DISEÑO_VISOR_RF = {
    "card_w":      220,
    "card_h":      90,
    "gap":         5,
    "margin":      18,
    "col_gap":     8,
    "cols":        3,
    "sec_h":       28,

    "bg_canvas":   "#0d1117",
    "bg_card":     "#161b22",
    "bg_header":   "#1c2128",
    "bg_sec_hdr":  "#21262d",
    "border":      "#30363d",
    "accent":      "#388bfd",
    "col_accent":  "#58a6ff",
    "mep_accent":  "#d29922",
    "text_white":  "#e6edf3",
    "text_muted":  "#8b949e",
    "up":          "#3fb950",
    "down":        "#f85149",
    "neutral":     "#8b949e",

    "font_header":  19,
    "font_sub":     11,
    "font_sec":     12,
    "font_ticker":  14,
    "font_nombre":  9,
    "font_precio":  16,
    "font_pct":     12,
}


# ───────────────────────────────────────────────────────────────────
# 9. DISEÑO VISUAL — Tarjeta Visor BCRA (Pillow)
# ───────────────────────────────────────────────────────────────────

DISEÑO_VISOR_BCRA = {
    "width":       700,
    "bg":          "#dbeafe",
    "border":      "#1e40af",
    "header_bg":   "#1e40af",
    "header_text": "#ffffff",
    "col_header":  "#1e3a5f",
    "label_color": "#1e3a5f",
    "value_color": "#1e40af",
    "date_color":  "#374151",
    "divider":     "#93c5fd",
    "font_header": 22,
    "font_sub":    13,
    "font_label":  14,
    "font_value":  14,
    "row_height":  38,
    "padding":     24,
}


# ───────────────────────────────────────────────────────────────────
# 10. MENSAJES TELEGRAM
# ───────────────────────────────────────────────────────────────────

MENSAJES = {
    "visor_arg_titulo":  "🇦🇷  VISOR ARG",
    "visor_rf_titulo":   "🇦🇷  VISOR RENTA FIJA ARG",
    "visor_bcra_titulo": "VISOR BCRA",
    "visor_arg_tg":      "🇦🇷 Visor ARG",
    "visor_rf_tg":       "📊 Visor Renta Fija ARG",
    "visor_bcra_tg":     "🏦 Visor BCRA",
    "fuente_datos":      "Fuente: data912.com",
}
