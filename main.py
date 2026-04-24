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
    APIS, VISOR_ARG_COL1, VISOR_ARG_COL2, VISOR_ARG_COL3,
    CAPTURAS_WEB, VISOR_BCRA_ITEMS,
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
    # Caption del caption_key mapea cada captura a su texto en MENSAJES
    caption_keys = {
        "CAUCION_1D_MAE": "caucion_caption",
        "USMEP_MAE":      "usmep_caption",
        "AL30_IOL":       "al30_caption",
        "GD30_IOL":       "gd30_caption",
    }

    for nombre, cfg in activas.items():
        if nombre not in imgs_capturadas:
            print(f"    ⚠️  {nombre}: no capturado, omitiendo envío.")
            continue

        tmp_path = f"captura_{nombre.lower()}.png"
        imgs_capturadas[nombre].save(tmp_path, "PNG", optimize=True)

        # Buscar el texto de caption en MENSAJES, fallback al campo caption del config
        clave_msg = caption_keys.get(nombre)
        texto_cap = MENSAJES.get(clave_msg, cfg.get("caption", nombre))

        caption = (
            f"{emoji} *{texto_estado}* — {ts} AR\n"
            f"{texto_cap}"
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
    Genera el Visor ARG con 3 columnas independientes:
      Col 1: ADR'S / USD  (data912 usa_adrs)
      Col 2: BYMA / $     (data912 arg_stocks)
      Col 3: CEDEARS / $  (data912 arg_cedears)

    Cada columna tiene su propia lista de activos configurada en config.py.
    Las filas de cada columna son independientes entre sí.
    """
    D    = DISEÑO_VISOR_ARG
    ts   = hhmm()
    hoy  = hora_ar().strftime("%d/%m/%Y")
    cache = {}

    print(f"🃏 Generando Visor ARG ({ts})...")

    # ── Cargar datos de las 3 columnas ────────────────────────────
    columnas = [VISOR_ARG_COL1, VISOR_ARG_COL2, VISOR_ARG_COL3]

    datos_cols = []   # lista de listas: [[{ticker,nombre,precio,pct},...], ...]
    for col in columnas:
        filas_col = []
        for ticker, nombre in col["activos"]:
            precio, pct = _dato_activo(ticker, col["fuente"], cache)
            filas_col.append({"ticker": ticker, "nombre": nombre,
                               "precio": precio, "pct": pct})
            p_str = f"${precio:.2f}" if precio else "—"
            v_str = f"{pct:+.2f}%" if pct is not None else "—"
            print(f"  [{col['cabecera']}] {ticker}: {p_str} {v_str}")
        datos_cols.append(filas_col)

    # ── Dimensiones del canvas ────────────────────────────────────
    cw      = D["card_w"]
    ch      = D["card_h"]
    gap     = D["gap"]
    mg      = D["margin"]
    pad     = D["padding"]
    col_gap = D["col_gap"]

    header_h  = 56    # altura del header principal
    col_hdr_h = 26    # altura de la franja de cabecera de columna
    n_filas   = max(len(d) for d in datos_cols)   # máx filas entre columnas

    canvas_w = mg * 2 + cw * 3 + col_gap * 2
    canvas_h = (mg + header_h + col_hdr_h + gap
                + n_filas * (ch + gap) + mg)

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg_canvas"])
    draw = ImageDraw.Draw(img)

    # ── Fuentes ───────────────────────────────────────────────────
    f_header  = _get_font(D["font_header"],  bold=True)
    f_sub     = _get_font(D["font_sub"],     bold=False)
    f_col_hdr = _get_font(D["font_col_hdr"], bold=True)
    f_ticker  = _get_font(D["font_ticker"],  bold=True)
    f_nombre  = _get_font(D["font_nombre"],  bold=False)
    f_precio  = _get_font(D["font_precio"],  bold=True)
    f_pct     = _get_font(D["font_pct"],     bold=False)

    # ── Header principal ──────────────────────────────────────────
    draw.rounded_rectangle(
        [mg, mg, canvas_w - mg, mg + header_h],
        radius=8, fill=D["bg_header"], outline=D["border"]
    )
    draw.text((mg + pad, mg + 8),
              MENSAJES["visor_arg_titulo"], font=f_header, fill=D["accent"])
    draw.text((mg + pad, mg + 34),
              f"{ts} AR  ·  {hoy}  ·  {MENSAJES['fuente_datos']}",
              font=f_sub, fill=D["text_muted"])

    # ── Cabeceras de columna ──────────────────────────────────────
    y_col_hdr = mg + header_h
    for ci, col in enumerate(columnas):
        cx = mg + ci * (cw + col_gap)
        draw.rounded_rectangle(
            [cx, y_col_hdr, cx + cw, y_col_hdr + col_hdr_h],
            radius=4, fill=D["bg_col_hdr"], outline=D["border"]
        )
        # Centrar texto de cabecera
        draw.text((cx + pad, y_col_hdr + 6),
                  col["cabecera"], font=f_col_hdr, fill=D["col_accent"])

    # ── Tarjetas de activos ───────────────────────────────────────
    y_start = mg + header_h + col_hdr_h + gap

    for ci, (col, filas_col) in enumerate(zip(columnas, datos_cols)):
        cx = mg + ci * (cw + col_gap)

        for ri, row in enumerate(filas_col):
            y       = y_start + ri * (ch + gap)
            precio  = row["precio"]
            pct     = row["pct"]
            color_v = _color_variacion(pct, D)

            # Fondo tarjeta
            draw.rounded_rectangle(
                [cx, y, cx + cw, y + ch],
                radius=5, fill=D["bg_card"], outline=D["border"]
            )

            # Barra lateral de color
            draw.rectangle([cx, y + 4, cx + 3, y + ch - 4], fill=color_v)

            x0 = cx + pad

            # Ticker
            draw.text((x0, y + 5), row["ticker"],
                      font=f_ticker, fill=D["text_white"])

            # Nombre corto
            draw.text((x0, y + 24), row["nombre"],
                      font=f_nombre, fill=D["text_muted"])

            if precio is not None:
                # Formato precio: si es grande (BYMA/CEDEARS) → sin decimales
                if precio >= 1000:
                    p_str = f"${precio:,.0f}"
                elif precio >= 10:
                    p_str = f"${precio:.2f}"
                else:
                    p_str = f"${precio:.3f}"
                draw.text((x0, y + 38), p_str,
                          font=f_precio, fill=D["text_white"])

                # Variación %
                pct_str = f"{_flecha(pct)} {pct:+.2f}%"
                draw.text((x0, y + 62), pct_str,
                          font=f_pct, fill=color_v)
            else:
                draw.text((x0, y + 38), "Sin dato",
                          font=f_nombre, fill=D["neutral"])

    path = ARCHIVOS["visor_arg_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor ARG guardado: {path}  ({canvas_w}×{canvas_h}px)")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 6 — VISOR BCRA (Tarjeta PNG con Pillow)
# ═══════════════════════════════════════════════════════════════════

def _bcra_variable(var_id: int) -> float | None:
    """
    Obtiene el valor más reciente de una variable BCRA.
    Endpoint oficial: GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/{id}

    Intenta primero con verify=True (usando el certificado Let's Encrypt
    instalado en el .yml). Si falla por SSL, reintenta con verify=False.
    Respuesta JSON: { "results": [ {"fecha": "YYYY-MM-DD", "valor": X}, ... ] }
    """
    from datetime import timedelta
    import urllib3

    hoy   = hora_ar().strftime("%Y-%m-%d")
    desde = (hora_ar() - timedelta(days=15)).strftime("%Y-%m-%d")
    url   = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/{var_id}"
    params = {"desde": desde, "hasta": hoy}

    for verify in (True, False):
        try:
            if not verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            r = requests.get(url, params=params, verify=verify, timeout=15)
            r.raise_for_status()
            resultados = r.json().get("results", [])
            if resultados:
                valor = float(resultados[-1]["valor"])
                print(f"    ✅ ID {var_id}: {valor} (verify={verify})")
                return valor
            else:
                print(f"    ⚠️  ID {var_id}: sin datos en {desde} → {hoy}")
                return None
        except Exception as e:
            if verify:
                print(f"    🔄 ID {var_id}: SSL con certs → reintentando sin verify...")
            else:
                print(f"    ⚠️  bcra ID {var_id}: {e}")
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
      · API BCRA v4.0 directa con requests verify=False → IDs 1,2,4,6,10,11,12,13
      · argentinadatos.com → Riesgo País
    """
    D    = DISEÑO_VISOR_BCRA
    hoy  = hora_ar().strftime("%d/%m/%Y")
    ts   = hhmm()

    print(f"\n🏦 Generando Visor BCRA ({ts})...")

    # ── 1. Recolectar datos via API BCRA directa ──────────────────
    IDS_DIRECTOS = [1, 2, 4, 6, 10, 11, 12, 13]
    raw = {}
    for vid in IDS_DIRECTOS:
        print(f"  → Consultando BCRA ID {vid}...")
        raw[vid] = _bcra_variable(vid)

    print(f"  → Consultando Riesgo País (argentinadatos.com)...")
    raw["rp"] = _riesgo_pais()

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
        tg_foto(path, f"*{MENSAJES['visor_arg_tg']}* — {ts} AR\n_{MENSAJES['fuente_datos']}_")
        marcar_enviado("visor_arg_1")

    # 5 · IMAGEN WEB 14:00 — Merval Abierto
    if es_hora_exacta(HORARIOS["imagen_2"]) and not ya_se_envio("imagen_2"):
        generar_Imagen_ARG(estado="Abierto")
        marcar_enviado("imagen_2")

    # 6 · VISOR ARG 15:00
    if es_hora_exacta(HORARIOS["visor_arg_2"]) and not ya_se_envio("visor_arg_2"):
        path = generar_Visor_ARG()
        tg_foto(path, f"*{MENSAJES['visor_arg_tg']}* — {ts} AR\n_{MENSAJES['fuente_datos']}_")
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
        tg_foto(path, f"*{MENSAJES['visor_arg_tg']}* — Cierre {ts} AR\n_{MENSAJES['fuente_datos']}_")
        marcar_enviado("visor_arg_3")

    # 9 · VISOR BCRA 17:30
    if es_hora_exacta(HORARIOS["visor_bcra"]) and not ya_se_envio("visor_bcra"):
        path = generar_Visor_BCRA()
        tg_foto(path, f"*{MENSAJES['visor_bcra_tg']}* — {ts} AR")
        marcar_enviado("visor_bcra")

    print(f"✅ Completado — {hhmm()}")


if __name__ == "__main__":
    main()
