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
# Campos:
#   url            → página a abrir con Playwright
#   wait_selector  → CSS a esperar antes de capturar (gráficos JS)
#   crop_selector  → elemento CSS a recortar (en DOM principal o dentro del iframe)
#   iframe_selector→ [NUEVO] selector del <iframe> que contiene el gráfico.
#                    Si está definido y crop_selector no se encuentra en el DOM
#                    principal, Playwright entra al iframe y busca adentro.
#                    Usar cuando el gráfico es un widget externo embebido (TradingView).
#                    Dejar None o no definir si el gráfico está en el DOM principal.
#   zoom           → factor de ampliación
#   delay_ms       → ms extra para que el canvas JS termine de dibujar
#   caption_key    → clave en MENSAJES para el texto base del caption
#   ticker_api     → símbolo a buscar en APIS["BONOS"] para precio dinámico
#   fuente_api     → clave en APIS donde buscar el ticker (default "BONOS")
#   activo         → True/False para activar/desactivar sin borrar

CAPTURAS_WEB = {

    # ── CAUCIÓN 1D — MAE A3 ───────────────────────────────────────
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

    # ── DÓLAR MEP (USMEP) — MAE A3 ────────────────────────────────
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

    # ── AL30 Intradiario — IOL ────────────────────────────────────
    "AL30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/AL30/BONO-REP.-ARGENTINA-USD-STEP-UP-2030/",
        "wait_selector": "#graficoIntradiario svg.highcharts-root",
        "crop_selector": "#graficoIntradiario",
        "iframe_selector": None,
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "al30_caption",
        "ticker_api":    "AL30",
        "activo":        True,
    },

    # ── GD30 Intradiario — IOL ────────────────────────────────────
    "GD30_IOL": {
        "url":           "https://iol.invertironline.com/titulo/cotizacion/BCBA/GD30/BONOS-REP.-ARG.-U-S-STEP-UP-V.09-07-30/",
        "wait_selector": ".highcharts-container svg.highcharts-root",
        "crop_selector": ".highcharts-container",
        "iframe_selector": None,
        "zoom":          2.2,
        "delay_ms":      5000,
        "caption_key":   "gd30_caption",
        "ticker_api":    "GD30",
        "activo":        True,
    },

    # ── AL30 Intradiario — RAVA ───────────────────────────────────
    # [FIX-3] Rava usa TradingView embebido en un <iframe>.
    # Playwright no puede ver el contenido del iframe en el DOM principal,
    # por eso el selector anterior fallaba silenciosamente.
    #
    # Solución: definir iframe_selector con el <iframe> de TradingView.
    # main.py usa frame_locator(iframe_selector) para entrar al frame
    # y luego busca crop_selector adentro.
    #
    # iframe_selector: el iframe de TradingView en Rava tiene
    # title="Advanced Chart Widget" o puede identificarse por src con "tradingview.com".
    # Si el bot sigue fallando, probar con: "iframe[src*='tradingview.com']"
    "AL30_RAVA": {
        "url":            "https://www.rava.com/perfil/AL30",
        "wait_selector":  "iframe[src*='tradingview.com']",    # espera a que cargue el iframe
        "crop_selector":  ".chart-container",                  # selector DENTRO del iframe
        "iframe_selector": "iframe[src*='tradingview.com']",   # [FIX-3] entrar al iframe
        "zoom":           2.0,
        "delay_ms":       10000,   # TradingView necesita tiempo para renderizar el canvas
        "caption_key":    "al30_caption",
        "ticker_api":     "AL30",
        "activo":         True,
    },

    # ── Agregar más capturas aquí ──────────────────────────────────
    # "GD30_RAVA": {
    #     "url":            "https://www.rava.com/perfil/GD30",
    #     "wait_selector":  "iframe[src*='tradingview.com']",
    #     "crop_selector":  ".chart-container",
    #     "iframe_selector": "iframe[src*='tradingview.com']",
    #     "zoom":           2.0,
    #     "delay_ms":       10000,
    #     "caption_key":    "gd30_caption",
    #     "ticker_api":     "GD30",
    #     "activo":         False,
    # },
}


# ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — API oficial BCRA v4.0 via bcra-connector
# ───────────────────────────────────────────────────────────────────
# IDs v4.0 confirmados operativos (verificado mayo 2026):
#   1  → Reservas Internacionales (millones USD)   T-2  ✅
#   4  → USD Oficial A3500                         T+0  ✅
#   6  → Base Monetaria (millones $)               T-2  ⚠️ puede estar discontinuado
#   7  → Tasa BADLAR TNA (%)                       T+0  ✅
#   15 → CER                                       T+0  ✅
#   34 → Tasa Política Monetaria TNA (%)           T+0  ⚠️ discontinuado desde 2024
#
# [FIX-4] Si un ID devuelve "—", main.py busca automáticamente
# la variable por palabras clave en la descripción (fallback dinámico).
# Ver FALLBACKS_BCRA en main.py para ajustar las palabras clave.
#
# id_var = None        → Riesgo País (argentinadatos.com)
# id_var = int         → variable directa bcra-connector
# id_var = "calc:X/Y"  → ratio calculado entre ID X e ID Y

VISOR_BCRA_ITEMS = [
    # id_var        Etiqueta           Col   Formato
    (None,          "RIESGO PAIS",    "T0", "bps"),
    (4,             "USD A3500",      "T0", "usd4"),
    (15,            "CER",            "T0", "num6"),
    (7,             "BADLAR",         "T0", "pct2"),
    (34,            "TASA POL.MON.",  "T0", "pct2"),   # fallback automático si ID 34 falla
    (1,             "RESERVAS INTER", "T2", "usd_m"),
    (6,             "BASE MONETARIA", "T2", "pesos_m"), # fallback automático si ID 6 falla
    ("calc:6/1",    "B.MON / R.IN",   "T2", "ratio"),
    ("calc:6/4",    "B.MON / USD.OF", "T2", "pesos_m"),
]


# ───────────────────────────────────────────────────────────────────
# 5. HORARIOS DE EJECUCIÓN (hora Argentina)
# ───────────────────────────────────────────────────────────────────
# Tolerancia de detección: ±29 minutos (cubre el delay de GitHub Actions)
# El control de doble envío (estado_envios.csv) evita reenvíos si dos
# ejecuciones se solapan dentro de la ventana de tolerancia.

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
    "caucion_caption":   "📊 Caución 1D — MAE A3",
    "usmep_caption":     "💵 Dólar MEP (USMEP) — MAE A3",
    "al30_caption":      "📈 AL30 Intradiario: {precio} ({variacion}%)",
    "gd30_caption":      "📈 GD30 Intradiario: {precio} ({variacion}%)",
    "merval_abierto":    "🟢 Merval Abierto",
    "merval_cerrado":    "🔴 Merval Cerrado",
    "visor_arg_titulo":  "🇦🇷  VISOR ARG",
    "visor_bcra_titulo": "VISOR BCRA",
    "visor_arg_tg":      "🇦🇷 Visor ARG",
    "visor_bcra_tg":     "🏦 Visor BCRA",
    "fuente_datos":      "Fuente: data912.com",
}
