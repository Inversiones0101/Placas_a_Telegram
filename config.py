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

VISOR_ARG_PARES = {
    # ── ADRs (NYSE) con par local en BYMA ─────────────────────────
    "GGAL": {
        "fuente_us": "ADR",
        "ticker_ba": "GGAL",
        "fuente_ba": "STOCKS",
        "nombre":    "Galicia",
    },
    "YPF": {
        "fuente_us": "ADR",
        "ticker_ba": "YPFD",   # en BYMA cotiza como YPFD
        "fuente_ba": "STOCKS",
        "nombre":    "YPF",
    },
    "BMA": {
        "fuente_us": "ADR",
        "ticker_ba": "BMA",
        "fuente_ba": "STOCKS",
        "nombre":    "Bco Macro",
    },
    "SUPV": {
        "fuente_us": "ADR",
        "ticker_ba": "SUPV",
        "fuente_ba": "STOCKS",
        "nombre":    "Supervielle",
    },
    "PAM": {
        "fuente_us": "ADR",
        "ticker_ba": "PAMP",   # en BYMA cotiza como PAMP
        "fuente_ba": "STOCKS",
        "nombre":    "Pampa",
    },
    # ── CEDEARs — solo cotizan en BYMA (col US = CEDEAR en $, col BA = vacía) ──
    "MELI": {
        "fuente_us": "CEDEARS",   # MELI CEDEAR en pesos (col izquierda)
        "ticker_ba": None,
        "fuente_ba": None,
        "nombre":    "MercadoLibre",
    },
    "ORCL": {
        # ORCL cotiza como CEDEAR en BYMA (símbolo: ORCL en pesos)
        # No tiene ADR propio en data912, así que se muestra solo el CEDEAR
        "fuente_us": "CEDEARS",
        "ticker_ba": None,
        "fuente_ba": None,
        "nombre":    "Oracle",
    },
    # ── Acciones locales BYMA sin par en NYSE ─────────────────────
    "TRAN": {
        # Transener — solo cotiza en BYMA (arg_stocks)
        # No tiene ADR en NYSE, la tarjeta muestra solo columna BA
        "fuente_us": None,
        "ticker_ba": "TRAN",
        "fuente_ba": "STOCKS",
        "nombre":    "Transener",
    },
    # ── Fase 2 — comentados, listos para activar ──────────────────
    # "VIST": {
    #     "fuente_us": "ADR",
    #     "ticker_ba": "VISTD",
    #     "fuente_ba": "CEDEARS",
    #     "nombre":    "Vista Energy",
    # },
    # "TGS": {
    #     "fuente_us": "ADR",
    #     "ticker_ba": "TGSU2",
    #     "fuente_ba": "STOCKS",
    #     "nombre":    "TGS",
    # },
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

DISEÑO_VISOR_ARG = {
    # Dimensiones
    "card_w":      260,    # ancho de cada tarjeta individual (px)
    "card_h":      110,    # alto de cada tarjeta
    "cols":        2,      # columnas (US | BA)
    "padding":     14,     # padding interno de tarjeta
    "gap":         6,      # separación entre tarjetas
    "margin":      20,     # margen exterior del canvas

    # Colores
    "bg_canvas":   "#0d1117",   # fondo general (negro GitHub)
    "bg_card":     "#161b22",   # fondo tarjeta
    "bg_header":   "#1c2128",   # fondo header de sección
    "border":      "#30363d",   # borde tarjeta
    "accent":      "#388bfd",   # azul acento (títulos)
    "text_white":  "#e6edf3",   # texto principal
    "text_muted":  "#8b949e",   # texto secundario
    "up":          "#3fb950",   # verde (sube)
    "down":        "#f85149",   # rojo (baja)
    "neutral":     "#8b949e",   # gris (sin cambio)

    # Tipografías (fallback a fuentes del sistema)
    "font_title":  18,     # tamaño nombre activo
    "font_price":  22,     # tamaño precio
    "font_pct":    16,     # tamaño variación %
    "font_label":  12,     # etiquetas US/BA
}


# ───────────────────────────────────────────────────────────────────
# 8. DISEÑO VISUAL — Tarjeta Visor BCRA (Pillow)
# ───────────────────────────────────────────────────────────────────

DISEÑO_VISOR_BCRA = {
    "width":       700,
    "bg":          "#dbeafe",   # celeste claro (como el boceto)
    "border":      "#1e40af",   # azul oscuro
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

MENSAJES = {
    "merval_abierto":  "🟢 Merval Abierto",
    "merval_cerrado":  "🔴 Merval Cerrado",
    "visor_arg":       "🇦🇷 Visor ARG",
    "visor_bcra":      "🏦 Visor BCRA",
}
