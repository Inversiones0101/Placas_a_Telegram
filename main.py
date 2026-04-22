"""
main.py — Placas_a_Telegram
Inversiones & Algoritmos · GitHub Actions

Funciones:
  1. generar_Imagen_ARG()  — Captura de pantalla web con Playwright → Telegram
  2. generar_Visor_ARG()   — Tarjeta PNG con precios ADRs/Stocks/CEDEARs → Telegram
  3. generar_Visor_BCRA()  — Tarjeta PNG con datos BCRA → Telegram

Arquitectura: cron en horarios fijos → cada ejecución dura ~40 seg → sale.
Sin time.sleep() internos. Control de doble envío via estado_envios.csv
"""

import os, sys, io, requests, textwrap
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import pytz

from config import (
    APIS, VISOR_ARG_PARES, CAPTURAS_WEB, VISOR_BCRA_ITEMS,
    HORARIOS, ARCHIVOS, DISEÑO_VISOR_ARG, DISEÑO_VISOR_BCRA, MENSAJES,
)

# ── Pillow ──────────────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont

TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TZ_AR   = pytz.timezone("America/Argentina/Buenos_Aires")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 1 — UTILIDADES
# ═══════════════════════════════════════════════════════════════════

def hora_ar() -> datetime:
    return datetime.now(TZ_AR)

def hhmm(dt=None) -> str:
    return (dt or hora_ar()).strftime("%H:%M")

def es_dia_habil() -> bool:
    hoy = hora_ar()
    if hoy.weekday() >= 5:
        print(f"⏸️  Fin de semana. Sin operación.")
        return False
    try:
        resp = requests.get(APIS["FERIADOS"], timeout=8)
        fechas = [f["fecha"] for f in resp.json() if "fecha" in f]
        if hoy.strftime("%Y-%m-%d") in fechas:
            print(f"🗓️  Feriado hoy. Sin operación.")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar feriados: {e}")
    return True

def es_hora_exacta(h_obj: str, tolerancia: int = 29) -> bool:
    """±29 min cubre el delay de GitHub Actions gratuito."""
    ahora = hora_ar()
    hh, mm = map(int, h_obj.split(":"))
    obj = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return abs((ahora - obj).total_seconds() / 60) <= tolerancia


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONTROL DE DOBLE ENVÍO
# ═══════════════════════════════════════════════════════════════════

def ya_se_envio(clave: str) -> bool:
    path = ARCHIVOS["estado_envios"]
    if not os.path.exists(path):
        return False
    try:
        df  = pd.read_csv(path, dtype=str)
        hoy = hora_ar().strftime("%Y-%m-%d")
        return ((df["fecha"] == hoy) & (df["clave"] == clave)).any()
    except Exception:
        return False

def marcar_enviado(clave: str):
    path  = ARCHIVOS["estado_envios"]
    hoy   = hora_ar().strftime("%Y-%m-%d")
    nuevo = pd.DataFrame([{"fecha": hoy, "clave": clave}])
    if not os.path.exists(path):
        nuevo.to_csv(path, index=False)
    else:
        df = pd.read_csv(path, dtype=str)
        pd.concat([df, nuevo], ignore_index=True).to_csv(path, index=False)

def limpiar_estado_viejo():
    path = ARCHIVOS["estado_envios"]
    if not os.path.exists(path):
        return
    try:
        df  = pd.read_csv(path, dtype=str)
        hoy = hora_ar().date()
        df  = df[df["fecha"].apply(lambda f: (hoy - date.fromisoformat(f)).days <= 3)]
        df.to_csv(path, index=False)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 3 — TELEGRAM
# ═══════════════════════════════════════════════════════════════════

def tg_foto(img_path: str, caption: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(img_path, "rb") as f:
            r = requests.post(url,
                data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": f}, timeout=30)
        print(f"{'📨' if r.status_code==200 else '⚠️ '} Telegram foto [{r.status_code}]")
        if r.status_code != 200:
            print(r.text[:300])
    except Exception as e:
        print(f"⚠️  tg_foto: {e}")

def tg_texto(msg: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url,
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=20)
        print(f"{'📨' if r.status_code==200 else '⚠️ '} Telegram texto [{r.status_code}]")
    except Exception as e:
        print(f"⚠️  tg_texto: {e}")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 4 — CAPTURA DE PANTALLA WEB (Playwright)
# ═══════════════════════════════════════════════════════════════════

def _get_font(size: int, bold: bool = False):
    """Busca fuentes del sistema. Fallback a PIL default."""
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def generar_Imagen_ARG(estado: str = "Abierto"):
    """
    Visita cada URL activa en CAPTURAS_WEB con Playwright.
    Captura el elemento CSS indicado, aplica zoom con Pillow.

    Lógica de combinación (campo 'combinar_con'):
      - Si la captura A tiene combinar_con="B", se espera a tener
        también la captura B y se pegan verticalmente en una sola
        imagen antes de enviar.
      - Si combinar_con es None, se envía individualmente.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️  Playwright no instalado. Saltando capturas web.")
        return

    ts           = hhmm()
    emoji        = "🟢" if estado == "Abierto" else "🔴"
    texto_estado = MENSAJES["merval_abierto"] if estado == "Abierto" else MENSAJES["merval_cerrado"]

    activas = {k: v for k, v in CAPTURAS_WEB.items() if v.get("activo", True)}
    if not activas:
        print("ℹ️  Sin capturas activas.")
        return

    print(f"📸 Capturas web ({len(activas)}) — {ts}")

    # Diccionario para almacenar imágenes capturadas {nombre: PIL.Image}
    imgs_capturadas: dict[str, Image.Image] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,   # retina → más resolución
        )
        page = ctx.new_page()

        for nombre, cfg in activas.items():
            try:
                print(f"  → {nombre}")
                page.goto(cfg["url"], wait_until="networkidle", timeout=35000)

                if cfg.get("wait_selector"):
                    try:
                        page.wait_for_selector(cfg["wait_selector"], timeout=15000)
                    except Exception:
                        print(f"    ⚠️  wait_selector no encontrado, continuando...")

                if cfg.get("delay_ms", 0) > 0:
                    page.wait_for_timeout(cfg["delay_ms"])

                elemento = page.query_selector(cfg["crop_selector"])
                img_bytes = elemento.screenshot() if elemento else page.screenshot(full_page=False)

                if not elemento:
                    print(f"    ⚠️  crop_selector '{cfg['crop_selector']}' no encontrado. Captura completa.")

                img  = Image.open(io.BytesIO(img_bytes))
                zoom = cfg.get("zoom", 1.0)
                if zoom != 1.0:
                    img = img.resize(
                        (int(img.width * zoom), int(img.height * zoom)),
                        Image.LANCZOS
                    )
                imgs_capturadas[nombre] = img
                print(f"    ✅ Capturado {img.width}×{img.height}px")

            except Exception as e:
                print(f"    ⚠️  Error en {nombre}: {e}")

        browser.close()

    # ── Enviar cada imagen individualmente ────────────────────────
    for nombre, cfg in activas.items():
        if nombre not in imgs_capturadas:
            print(f"    ⚠️  {nombre}: no capturado, omitiendo envío.")
            continue

        tmp_path = f"captura_{nombre.lower()}.png"
        imgs_capturadas[nombre].save(tmp_path, "PNG", optimize=True)
        caption = (
            f"{emoji} *{texto_estado}* — {ts} AR\n"
            f"{cfg.get('caption', nombre)}"
        )
        tg_foto(tmp_path, caption)
        print(f"    📨 Enviado: {nombre}")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 5 — VISOR ARG (Tarjeta PNG con Pillow)
# ═══════════════════════════════════════════════════════════════════

def _fetch_api(clave: str) -> dict:
    """Descarga la API indicada y devuelve dict {symbol: {c, pct_change}}."""
    try:
        r = requests.get(APIS[clave], timeout=10)
        r.raise_for_status()
        return {item["symbol"]: item for item in r.json()}
    except Exception as e:
        print(f"⚠️  Error API {clave}: {e}")
        return {}

def _dato_activo(symbol: str, fuente: str, cache: dict) -> tuple:
    """
    Retorna (precio, pct_change) del símbolo en la fuente dada.
    Usa cache para no re-descargar la misma API dos veces.
    """
    if fuente not in cache:
        cache[fuente] = _fetch_api(fuente)
    data = cache[fuente]
    item = data.get(symbol)
    if item:
        return float(item.get("c", 0)), float(item.get("pct_change", 0))
    return None, None

def _color_variacion(pct, D):
    if pct is None:
        return D["neutral"]
    if pct > 0:
        return D["up"]
    if pct < 0:
        return D["down"]
    return D["neutral"]

def _flecha(pct):
    if pct is None: return "—"
    if pct > 0:  return "▲"
    if pct < 0:  return "▼"
    return "▬"

def generar_Visor_ARG() -> str:
    """
    Genera una imagen PNG tipo tarjeta con precios de ADRs, Stocks y CEDEARs.
    Diseño: grid de pares US | BA, fondo oscuro estilo GitHub.
    Retorna la ruta de la imagen generada.
    """
    D    = DISEÑO_VISOR_ARG
    ts   = hhmm()
    hoy  = hora_ar().strftime("%d/%m/%Y")
    pares = list(VISOR_ARG_PARES.items())
    cache = {}   # cache de APIs ya descargadas

    print(f"🃏 Generando Visor ARG ({ts})...")

    # ── Recolectar datos ──────────────────────────────────────────
    filas = []
    for ticker_us, cfg in pares:
        nombre = cfg["nombre"]

        # Columna izquierda (US/CEDEAR): puede ser None para activos solo-BYMA
        p_us, v_us = (None, None)
        if cfg.get("fuente_us") and cfg.get("fuente_us") in APIS:
            p_us, v_us = _dato_activo(ticker_us, cfg["fuente_us"], cache)

        # Columna derecha (BA): puede ser None para activos solo-US o CEDEARs sin par
        p_ba, v_ba = (None, None)
        if cfg.get("ticker_ba") and cfg.get("fuente_ba"):
            p_ba, v_ba = _dato_activo(cfg["ticker_ba"], cfg["fuente_ba"], cache)

        filas.append({
            "ticker_us": ticker_us,
            "ticker_ba": cfg.get("ticker_ba"),
            "nombre":    nombre,
            "p_us": p_us, "v_us": v_us,
            "p_ba": p_ba, "v_ba": v_ba,
        })
        # Log seguro — nunca falla aunque p_us/p_ba/v_us/v_ba sean None
        us_str = f"US ${p_us:.3f} {v_us:+.2f}%" if p_us is not None else "US —"
        ba_str = f"BA ${p_ba:.2f} {v_ba:+.2f}%" if p_ba is not None else "BA —"
        print(f"  {ticker_us}: {us_str}  |  {ba_str}")

    # ── Layout ────────────────────────────────────────────────────
    cw   = D["card_w"]
    ch   = D["card_h"]
    gap  = D["gap"]
    mg   = D["margin"]
    pad  = D["padding"]

    # Cada fila = 2 tarjetas (US | BA) lado a lado
    # + 1 fila de header arriba
    header_h = 60
    n_filas  = len(filas)
    canvas_w = mg*2 + cw*2 + gap
    canvas_h = mg + header_h + gap + n_filas * (ch + gap) + mg

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg_canvas"])
    draw = ImageDraw.Draw(img)

    f_title  = _get_font(D["font_title"],  bold=True)
    f_price  = _get_font(D["font_price"],  bold=True)
    f_pct    = _get_font(D["font_pct"],    bold=False)
    f_label  = _get_font(D["font_label"],  bold=False)
    f_header = _get_font(20, bold=True)
    f_sub    = _get_font(12, bold=False)

    # ── Header del canvas ─────────────────────────────────────────
    draw.rounded_rectangle(
        [mg, mg, canvas_w - mg, mg + header_h],
        radius=8, fill=D["bg_header"], outline=D["border"]
    )
    draw.text((mg + pad, mg + 10), "🇦🇷  VISOR ARG", font=f_header, fill=D["accent"])
    draw.text((mg + pad, mg + 35), f"{ts} AR  ·  {hoy}  ·  Fuente: data912.com",
              font=f_sub, fill=D["text_muted"])

    # ── Columnas US / BA ─────────────────────────────────────────
    col_labels = ["NYSE / NASDAQ", "BYMA (Pesos)"]
    for ci, lbl in enumerate(col_labels):
        cx = mg + ci * (cw + gap)
        draw.text((cx + cw//2 - 40, mg + header_h + gap//2),
                  lbl, font=f_label, fill=D["text_muted"])

    # ── Tarjetas de cada activo ───────────────────────────────────
    y_start = mg + header_h + gap + 18

    for i, row in enumerate(filas):
        y = y_start + i * (ch + gap)

        for col_idx in range(2):
            is_us = col_idx == 0
            cx    = mg + col_idx * (cw + gap)

            precio = row["p_us"] if is_us else row["p_ba"]
            pct    = row["v_us"] if is_us else row["v_ba"]
            ticker = row["ticker_us"] if is_us else (row["ticker_ba"] or "—")

            # Fondo tarjeta
            draw.rounded_rectangle(
                [cx, y, cx + cw, y + ch],
                radius=6, fill=D["bg_card"], outline=D["border"]
            )

            color_v = _color_variacion(pct, D)

            # Barra lateral de color (indicador sube/baja)
            bar_w = 4
            draw.rectangle([cx, y+6, cx+bar_w, y+ch-6], fill=color_v)

            x0 = cx + pad
            # Ticker + nombre
            draw.text((x0, y + 8),  ticker,        font=f_title, fill=D["text_white"])
            draw.text((x0, y + 30), row["nombre"],  font=f_label, fill=D["text_muted"])

            if precio is not None:
                # Precio
                precio_str = f"${precio:,.2f}" if precio >= 10 else f"${precio:.3f}"
                draw.text((x0, y + 52), precio_str, font=f_price, fill=D["text_white"])

                # Variación con flecha
                pct_str = f"{_flecha(pct)} {pct:+.2f}%"
                draw.text((x0, y + 82), pct_str, font=f_pct, fill=color_v)
            else:
                draw.text((x0, y + 52), "Sin dato", font=f_label, fill=D["neutral"])

    # ── Footer ───────────────────────────────────────────────────
    footer_y = canvas_h - mg + 4
    draw.text((mg, footer_y - 16),
              "data912.com  ·  Inversiones & Algoritmos",
              font=f_label, fill=D["text_muted"])

    path = ARCHIVOS["visor_arg_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor ARG guardado: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 6 — VISOR BCRA (Tarjeta PNG con Pillow)
# ═══════════════════════════════════════════════════════════════════

def _bcra_variable(var_id: int) -> float | None:
    """
    Obtiene el valor más reciente de una variable BCRA usando bcraapi.
    El patch SSL (verify=False) se aplica en generar_Visor_BCRA() antes
    de llamar a esta función, por lo que bcraapi ya no falla con SSLError.
    """
    try:
        from bcraapi import estadisticas
        from datetime import timedelta
        hoy   = hora_ar().strftime("%Y-%m-%d")
        desde = (hora_ar() - timedelta(days=15)).strftime("%Y-%m-%d")
        df = estadisticas.datos_monetarias(
            id_variable=var_id,
            desde=desde,
            hasta=hoy,
        )
        if df is not None and not df.empty:
            valor = float(df["valor"].iloc[-1])
            print(f"    ✅ ID {var_id}: {valor}")
            return valor
    except Exception as e:
        print(f"    ⚠️  bcraapi ID {var_id}: {e}")
    return None


def _riesgo_pais() -> float | None:
    """
    Obtiene el Riesgo País desde argentinadatos.com.
    Endpoint: /v1/finanzas/indices/riesgo-pais
    Devuelve lista de {fecha, valor} — tomamos el último.
    """
    try:
        r    = requests.get(APIS["RIESGO_PAIS"], timeout=8)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            # La lista viene ordenada por fecha ascendente
            ultimo = data[-1]
            valor  = float(ultimo.get("valor", ultimo.get("value", 0)))
            print(f"    ✅ Riesgo País: {valor} bps")
            return valor
    except Exception as e:
        print(f"    ⚠️  Riesgo País: {e}")
    return None


def _formatear_bcra(var_id, valor: float) -> str:
    """
    Formatea el valor BCRA según el tipo de variable para mostrarlo
    de forma legible en la tarjeta.
    """
    if valor is None:
        return "—"
    if var_id is None:                   # Riesgo País
        return f"{int(valor):,} bps"
    if var_id in (1, 6):                 # Reservas / Base Mon. → en millones
        return f"$ {valor / 1_000_000:,.0f} M"
    if var_id in (2, 13):                # BADLAR / TAMAR → TNA %
        return f"{valor:.2f} % TNA"
    if var_id == 10:                     # CER → coeficiente con 6 decimales
        return f"{valor:.6f}"
    if var_id == 4:                      # USD Oficial → $ con 2 decimales
        return f"$ {valor:,.2f}"
    if var_id == "6/1":                  # B.MON / R.IN → ratio
        return f"{valor:,.2f}"
    if var_id == "6/4":                  # B.MON / USD.OF → millones de USD
        return f"$ {valor / 1_000_000:,.0f} M"
    if var_id == "12/11*100":            # PREST / DEPOS → porcentaje
        return f"{valor:.1f} %"
    return f"{valor:,.4f}"


def generar_Visor_BCRA() -> str:
    """
    Genera la tarjeta PNG del Visor BCRA con Pillow.

    Fuentes de datos:
      · bcraapi (pip install bcraapi) → Variables ID: 1,2,4,6,10,11,12,13
      · argentinadatos.com            → Riesgo País

    Diseño fiel al boceto:
      · Fondo celeste, borde azul
      · Header: 'VISOR BCRA' + fecha
      · Tabla con columnas: INDICADOR | T+0 (Hoy) | T-2 (48hs)
      · Filas alternadas para legibilidad
      · Línea vertical separadora entre columnas
    """
    D    = DISEÑO_VISOR_BCRA
    hoy  = hora_ar().strftime("%d/%m/%Y")
    ts   = hhmm()

    print(f"\n🏦 Generando Visor BCRA ({ts})...")

    # ── Deshabilitar SSL globalmente para esta función ─────────────
    # api.bcra.gob.ar tiene un certificado SSL que no está en la cadena
    # de confianza de Ubuntu (GitHub Actions). Se aplica el patch una
    # sola vez antes de todas las consultas y se restaura al terminar.
    import urllib3
    import requests as _req
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _orig_session_init = _req.Session.__init__
    def _ssl_off(self, *a, **kw):
        _orig_session_init(self, *a, **kw)
        self.verify = False
    _req.Session.__init__ = _ssl_off
    print("  🔓 SSL verify deshabilitado para api.bcra.gob.ar")

    # ── 1. Recolectar datos via bcraapi ───────────────────────────
    # IDs directos necesarios (incluye los usados en ratios)
    IDS_DIRECTOS = [1, 2, 4, 6, 10, 11, 12, 13]
    raw = {}
    for vid in IDS_DIRECTOS:
        print(f"  → Consultando bcraapi ID {vid}...")
        raw[vid] = _bcra_variable(vid)

    # Riesgo País (fuente diferente)
    print(f"  → Consultando Riesgo País (argentinadatos.com)...")
    raw["rp"] = _riesgo_pais()

    # ── Restaurar SSL ──────────────────────────────────────────────
    _req.Session.__init__ = _orig_session_init
    print("  🔒 SSL verify restaurado")

    # ── 2. Calcular ratios ────────────────────────────────────────
    def v(k):
        return raw.get(k)

    ratios = {
        "6/1":       (v(6) / v(1))         if v(6) and v(1)  else None,
        "6/4":       (v(6) / v(4))         if v(6) and v(4)  else None,
        "12/11*100": (v(12) / v(11) * 100) if v(12) and v(11) else None,
    }

    def get_valor(var_id):
        """Resuelve el valor de un ítem (directo, ratio o riesgo país)."""
        if var_id is None:           return raw.get("rp")
        if isinstance(var_id, str):  return ratios.get(var_id)
        return raw.get(var_id)

    # ── 3. Dibujar tarjeta con Pillow ────────────────────────────
    pad      = D["padding"]
    rh       = D["row_height"]
    n_items  = len(VISOR_BCRA_ITEMS)
    header_h = 80
    colhdr_h = 36       # altura fila de cabeceras de columna
    canvas_w = D["width"]
    canvas_h = header_h + colhdr_h + n_items * rh + pad

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg"])
    draw = ImageDraw.Draw(img)

    # Borde exterior
    draw.rectangle([0, 0, canvas_w - 1, canvas_h - 1],
                   outline=D["border"], width=3)

    # ── Header azul ───────────────────────────────────────────────
    draw.rectangle([0, 0, canvas_w, header_h], fill=D["header_bg"])
    fh1 = _get_font(D["font_header"], bold=True)
    fh2 = _get_font(D["font_sub"],    bold=False)
    draw.text((pad, 14), "VISOR BCRA",               font=fh1, fill=D["header_text"])
    draw.text((pad, 48), f"Fuente: BCRA  —  {hoy}",  font=fh2, fill="#bfdbfe")

    # ── Cabeceras de columnas ─────────────────────────────────────
    # Posiciones X de cada columna (ajustadas a 700px de ancho)
    x_label = pad           # columna INDICADOR
    x_t0    = 340           # columna T+0 (Hoy)
    x_t2    = 540           # columna T-2 (48hs)
    x_div1  = 330           # línea vertical izquierda
    x_div2  = 530           # línea vertical derecha

    col_y = header_h + 6
    fch   = _get_font(D["font_label"], bold=True)
    draw.text((x_label, col_y), "INDICADOR",   font=fch, fill=D["col_header"])
    draw.text((x_t0,    col_y), "T+0 (Hoy)",   font=fch, fill=D["col_header"])
    draw.text((x_t2,    col_y), "T-2 (48hs)",  font=fch, fill=D["col_header"])

    sep_y = header_h + colhdr_h
    draw.line([(pad, sep_y), (canvas_w - pad, sep_y)], fill=D["border"], width=2)

    # ── Filas de datos ────────────────────────────────────────────
    fl = _get_font(D["font_label"], bold=False)
    fv = _get_font(D["font_value"], bold=True)

    for idx, (var_id, etiqueta, col, _) in enumerate(VISOR_BCRA_ITEMS):
        y    = sep_y + idx * rh
        fill = "#dbeafe" if idx % 2 == 0 else "#e0f2fe"
        draw.rectangle([1, y, canvas_w - 1, y + rh - 1], fill=fill)

        # Etiqueta del indicador
        draw.text((x_label, y + 11), etiqueta, font=fl, fill=D["label_color"])

        # Líneas verticales separadoras
        draw.line([(x_div1, y), (x_div1, y + rh)], fill=D["divider"], width=1)
        draw.line([(x_div2, y), (x_div2, y + rh)], fill=D["divider"], width=1)

        # Valor formateado
        valor     = get_valor(var_id)
        valor_str = _formatear_bcra(var_id, valor)
        color_val = D["value_t0"] if col == "T0" else D["value_t2"]
        x_val     = x_t0 if col == "T0" else x_t2
        draw.text((x_val, y + 11), valor_str, font=fv, fill=color_val)

    # Línea final
    y_final = sep_y + n_items * rh
    draw.line([(pad, y_final), (canvas_w - pad, y_final)],
              fill=D["border"], width=2)

    path = ARCHIVOS["visor_bcra_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor BCRA guardado: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 7 — LÓGICA PRINCIPAL (RELOJ INTELIGENTE)
# ═══════════════════════════════════════════════════════════════════

def main():
    ahora = hora_ar()
    ts    = hhmm(ahora)

    print(f"\n{'═'*54}")
    print(f"  Placas_a_Telegram  ·  {ahora.strftime('%Y-%m-%d  %H:%M:%S')} AR")
    print(f"{'═'*54}")

    # 1 · Día hábil
    if not es_dia_habil():
        sys.exit(0)

    # 2 · Fuera de horario (11:00 — 18:00)
    if ts < "11:00" or ts > "18:05":
        print(f"⏰ Fuera de horario ({ts}).")
        sys.exit(0)

    limpiar_estado_viejo()

    # ── Acciones del día ───────────────────────────────────────────

    # 3 · IMAGEN WEB 12:00 — Merval Abierto
    if es_hora_exacta(HORARIOS["imagen_1"]) and not ya_se_envio("imagen_1"):
        generar_Imagen_ARG(estado="Abierto")
        marcar_enviado("imagen_1")

    # 4 · VISOR ARG 13:00
    if es_hora_exacta(HORARIOS["visor_arg_1"]) and not ya_se_envio("visor_arg_1"):
        path = generar_Visor_ARG()
        tg_foto(path, f"🇦🇷 *{MENSAJES['visor_arg']}* — {ts} AR\n_Fuente: data912.com_")
        marcar_enviado("visor_arg_1")

    # 5 · IMAGEN WEB 14:00 — Merval Abierto
    if es_hora_exacta(HORARIOS["imagen_2"]) and not ya_se_envio("imagen_2"):
        generar_Imagen_ARG(estado="Abierto")
        marcar_enviado("imagen_2")

    # 6 · VISOR ARG 15:00
    if es_hora_exacta(HORARIOS["visor_arg_2"]) and not ya_se_envio("visor_arg_2"):
        path = generar_Visor_ARG()
        tg_foto(path, f"🇦🇷 *{MENSAJES['visor_arg']}* — {ts} AR\n_Fuente: data912.com_")
        marcar_enviado("visor_arg_2")

    # 7 · IMAGEN WEB 16:00 — Merval Abierto
    if es_hora_exacta(HORARIOS["imagen_3"]) and not ya_se_envio("imagen_3"):
        generar_Imagen_ARG(estado="Abierto")
        marcar_enviado("imagen_3")

    # 8 · IMAGEN WEB 17:00 + VISOR ARG — Merval Cerrado
    if es_hora_exacta(HORARIOS["imagen_cierre"]) and not ya_se_envio("imagen_cierre"):
        generar_Imagen_ARG(estado="Cerrado")
        marcar_enviado("imagen_cierre")

    if es_hora_exacta(HORARIOS["visor_arg_3"]) and not ya_se_envio("visor_arg_3"):
        path = generar_Visor_ARG()
        tg_foto(path, f"🇦🇷 *{MENSAJES['visor_arg']}* — Cierre {ts} AR\n_Fuente: data912.com_")
        marcar_enviado("visor_arg_3")

    # 9 · VISOR BCRA 17:30
    if es_hora_exacta(HORARIOS["visor_bcra"]) and not ya_se_envio("visor_bcra"):
        path = generar_Visor_BCRA()
        tg_foto(path, f"🏦 *{MENSAJES['visor_bcra']}* — {ts} AR")
        marcar_enviado("visor_bcra")

    print(f"✅ Completado — {hhmm()}")


if __name__ == "__main__":
    main()
