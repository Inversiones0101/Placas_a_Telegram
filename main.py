"""
main.py — Placas_a_Telegram
Inversiones & Algoritmos · GitHub Actions

Funciones:
  1. generar_Imagen_ARG()  — Captura de pantalla web con Playwright → Telegram
  2. generar_Visor_ARG()   — Tarjeta PNG con precios ADRs/Stocks/CEDEARs → Telegram
  3. generar_Visor_BCRA()  — Tarjeta PNG con datos BCRA → Telegram

Arquitectura: cron en horarios fijos → cada ejecución dura ~40 seg → sale.
Sin time.sleep() internos. Control de doble envío via estado_envios.csv

CAMBIOS v3 (Visor BCRA):
  · Columnas renombradas: T+0(Hoy) → FECHA  /  T-2(48hs) → VALOR
  · Cada fila muestra la FECHA REAL del dato según bcra-connector (ultFechaInformada)
  · El Riesgo País muestra la fecha que devuelve argentinadatos.com
  · Para items calc:X/Y la fecha corresponde al numerador (X)
  · DISEÑO_VISOR_BCRA: nuevas claves value_color y date_color (ver config.py)

FIXES anteriores:
  [FIX-1] Visor ARG y BCRA llaman tg_foto() después de generar el PNG
  [FIX-2] Control ya_se_envio()/marcar_enviado() integrado en el flujo principal
  [FIX-3] AL30_RAVA: usa crop_box para recorte por coordenadas de viewport
  [FIX-4] BCRA: búsqueda dinámica de IDs + fallback para variables discontinuadas
"""

import os, sys, io, requests, textwrap, time
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import pytz

from config import (
    APIS, VISOR_ARG_COL1, VISOR_ARG_COL2, VISOR_ARG_COL3,
    CAPTURAS_WEB, VISOR_BCRA_ITEMS,
    HORARIOS, ARCHIVOS, DISEÑO_VISOR_ARG, DISEÑO_VISOR_BCRA, MENSAJES,
)

from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
# VARIABLES DE ENTORNO
# ═══════════════════════════════════════════════════════════════════

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
        año = hoy.year
        resp = requests.get(f"{APIS['FERIADOS']}{año}", timeout=8)
        fechas = [f["fecha"] for f in resp.json() if "fecha" in f]
        if hoy.strftime("%Y-%m-%d") in fechas:
            print(f"🗓️  Feriado hoy. Sin operación.")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar feriados: {e}")
    return True

def es_hora_exacta(h_obj: str, tolerancia: int = 44) -> bool:
    """±44 min cubre el delay de GitHub Actions (plan free)."""
    ahora = hora_ar()
    hh, mm = map(int, h_obj.split(":"))
    obj = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return abs((ahora - obj).total_seconds() / 60) <= tolerancia


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONTROL DE DOBLE ENVÍO
# ═══════════════════════════════════════════════════════════════════

def _leer_estado_csv(path: str) -> pd.DataFrame:
    cols = ["fecha", "clave"]
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    try:
        if os.path.getsize(path) == 0:
            return pd.DataFrame(columns=cols)
        df = pd.read_csv(path, dtype=str)
        if df.empty or not all(c in df.columns for c in cols):
            return pd.DataFrame(columns=cols)
        return df
    except Exception as e:
        print(f"  ⚠️  Error leyendo {path}: {e}. Reiniciando estado.")
        return pd.DataFrame(columns=cols)

def ya_se_envio(clave: str) -> bool:
    path = ARCHIVOS["estado_envios"]
    df   = _leer_estado_csv(path)
    if df.empty:
        return False
    hoy = hora_ar().strftime("%Y-%m-%d")
    return ((df["fecha"] == hoy) & (df["clave"] == clave)).any()

def marcar_enviado(clave: str):
    path  = ARCHIVOS["estado_envios"]
    hoy   = hora_ar().strftime("%Y-%m-%d")
    nuevo = pd.DataFrame([{"fecha": hoy, "clave": clave}])
    df    = _leer_estado_csv(path)
    pd.concat([df, nuevo], ignore_index=True).to_csv(path, index=False)

def limpiar_estado_viejo():
    path = ARCHIVOS["estado_envios"]
    df   = _leer_estado_csv(path)
    if df.empty:
        return
    try:
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


def fetch_with_retry(url: str, retries: int = 3, timeout: int = 10):
    """Fetch con retry exponencial. Backoff: 2s, 4s, 8s."""
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries - 1:
                raise
            wait_time = 2 ** i
            print(f"  ⚠️  Reintentando en {wait_time}s... ({i+1}/{retries})")
            time.sleep(wait_time)


def _capturar_elemento(page, cfg: dict) -> bytes | None:
    """
    Estrategia de captura en 4 capas de fallback:
    1. crop_selector en DOM principal
    2. iframe_selector + crop_selector
    3. crop_box por coordenadas de viewport (fracción 0.0–1.0)
    4. Fallback: screenshot completo del viewport
    """
    crop_selector   = cfg.get("crop_selector")
    iframe_selector = cfg.get("iframe_selector")
    crop_box        = cfg.get("crop_box")

    if crop_selector:
        elemento = page.query_selector(crop_selector)
        if elemento:
            try:
                return elemento.screenshot()
            except Exception as e:
                print(f"    ⚠️  screenshot() en DOM principal falló: {e}")

    if iframe_selector and crop_selector:
        try:
            frame = page.frame_locator(iframe_selector)
            el_en_frame = frame.locator(crop_selector).first
            el_en_frame.wait_for(timeout=8000)
            return el_en_frame.screenshot()
        except Exception as e:
            print(f"    ⚠️  screenshot() en iframe '{iframe_selector}' falló: {e}")

    if crop_box:
        try:
            vp   = page.viewport_size
            W, H = vp["width"], vp["height"]
            clip = {
                "x":      int(crop_box["x"] * W),
                "y":      int(crop_box["y"] * H),
                "width":  int(crop_box["w"] * W),
                "height": int(crop_box["h"] * H),
            }
            print(f"    📐 Recorte por coordenadas: {clip}")
            return page.screenshot(full_page=False, clip=clip)
        except Exception as e:
            print(f"    ⚠️  crop_box falló: {e}")

    print(f"    ⚠️  Sin selector válido. Captura de viewport completo.")
    return page.screenshot(full_page=False)


def _recortar_y_redimensionar(img: Image.Image, zoom: float,
                               max_lado: int = 4096) -> Image.Image:
    if zoom != 1.0:
        img = img.resize(
            (int(img.width * zoom), int(img.height * zoom)),
            Image.LANCZOS
        )
    if img.width > max_lado or img.height > max_lado:
        img = img.crop((0, 0, min(img.width, max_lado), min(img.height, max_lado)))
        print(f"    ✂️  Imagen recortada a {img.width}×{img.height}px (límite Telegram)")
    return img


def generar_Imagen_ARG(estado: str = "Abierto"):
    """
    Visita cada URL activa en CAPTURAS_WEB con Playwright,
    captura el elemento CSS indicado y envía cada imagen a Telegram.
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

    datos_bonos = {}
    tickers_necesarios = {cfg["ticker_api"] for cfg in activas.values()
                          if cfg.get("ticker_api")}
    if tickers_necesarios:
        try:
            fuentes_unicas = set()
            for cfg in activas.values():
                if cfg.get("ticker_api"):
                    fuentes_unicas.add(cfg.get("fuente_api", "BONOS"))
            for fuente in fuentes_unicas:
                print(f"  💹 Cargando precios desde APIS['{fuente}']...")
                data = fetch_with_retry(APIS[fuente], retries=3, timeout=10)
                datos_bonos.update({item["symbol"]: item for item in data})
            print(f"  ✅ Precios cargados: {', '.join(tickers_necesarios)}")
        except Exception as e:
            print(f"  ⚠️  No se pudieron cargar precios de bonos: {e}")

    imgs_capturadas: dict[str, Image.Image] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,
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

                img_bytes = _capturar_elemento(page, cfg)
                if img_bytes is None:
                    print(f"    ⚠️  No se pudo capturar {nombre}. Saltando.")
                    continue

                img  = Image.open(io.BytesIO(img_bytes))
                zoom = cfg.get("zoom", 1.0)
                img  = _recortar_y_redimensionar(img, zoom, max_lado=4096)

                imgs_capturadas[nombre] = img
                print(f"    ✅ Capturado {img.width}×{img.height}px")

            except Exception as e:
                print(f"    ⚠️  Error en {nombre}: {e}")

        browser.close()

    for nombre, cfg in activas.items():
        if nombre not in imgs_capturadas:
            print(f"    ⚠️  {nombre}: no capturado, omitiendo envío.")
            continue

        tmp_path = f"captura_{nombre.lower()}.png"
        imgs_capturadas[nombre].save(tmp_path, "PNG", optimize=True)

        caption_key = cfg.get("caption_key")
        texto_base  = MENSAJES.get(caption_key, cfg.get("caption", nombre))

        ticker = cfg.get("ticker_api")
        if ticker and ticker in datos_bonos:
            d          = datos_bonos[ticker]
            precio_str = f"{d['c']:,.2f}"
            var_str    = f"{d['pct_change']:+.2f}"
            texto_base = (texto_base
                          .replace("{precio}", f"${precio_str}")
                          .replace("{variacion}", var_str))
            print(f"    💹 {ticker}: ${precio_str} ({var_str}%)")
        elif ticker:
            texto_base = (texto_base
                          .replace(": ${precio} ({variacion}%)", "")
                          .replace("${precio}", "—")
                          .replace("{precio}", "—")
                          .replace("{variacion}", "—"))

        caption = f"{emoji} *{texto_estado}* — {ts} AR\n{texto_base}"
        tg_foto(tmp_path, caption)
        print(f"    📨 Enviado: {nombre}")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 5 — VISOR ARG (Tarjeta PNG con Pillow)
# ═══════════════════════════════════════════════════════════════════

def _fetch_api(clave: str) -> dict:
    try:
        data = fetch_with_retry(APIS[clave], retries=3, timeout=10)
        return {item["symbol"]: item for item in data}
    except Exception as e:
        print(f"⚠️  Error API {clave}: {e}")
        return {}

def _dato_activo(symbol: str, fuente: str, cache: dict) -> tuple:
    if fuente not in cache:
        cache[fuente] = _fetch_api(fuente)
    data = cache[fuente]
    item = data.get(symbol)
    if item:
        return float(item.get("c", 0)), float(item.get("pct_change", 0))
    return None, None

def _color_variacion(pct, D):
    if pct is None:  return D["neutral"]
    if pct > 0:      return D["up"]
    if pct < 0:      return D["down"]
    return D["neutral"]

def _flecha(pct):
    if pct is None: return "—"
    if pct > 0:  return "▲"
    if pct < 0:  return "▼"
    return "▬"

def generar_Visor_ARG() -> str:
    D    = DISEÑO_VISOR_ARG
    ts   = hhmm()
    hoy  = hora_ar().strftime("%d/%m/%Y")
    cache = {}

    print(f"🃏 Generando Visor ARG ({ts})...")

    columnas   = [VISOR_ARG_COL1, VISOR_ARG_COL2, VISOR_ARG_COL3]
    datos_cols = []

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

    cw      = D["card_w"]
    ch      = D["card_h"]
    gap     = D["gap"]
    mg      = D["margin"]
    pad     = D["padding"]
    col_gap = D["col_gap"]

    header_h  = 56
    col_hdr_h = 26
    n_filas   = max(len(d) for d in datos_cols)

    canvas_w = mg * 2 + cw * 3 + col_gap * 2
    canvas_h = (mg + header_h + col_hdr_h + gap
                + n_filas * (ch + gap) + mg)

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg_canvas"])
    draw = ImageDraw.Draw(img)

    f_header  = _get_font(D["font_header"],  bold=True)
    f_sub     = _get_font(D["font_sub"],     bold=False)
    f_col_hdr = _get_font(D["font_col_hdr"], bold=True)
    f_ticker  = _get_font(D["font_ticker"],  bold=True)
    f_nombre  = _get_font(D["font_nombre"],  bold=False)
    f_precio  = _get_font(D["font_precio"],  bold=True)
    f_pct     = _get_font(D["font_pct"],     bold=False)

    draw.rounded_rectangle(
        [mg, mg, canvas_w - mg, mg + header_h],
        radius=8, fill=D["bg_header"], outline=D["border"]
    )
    draw.text((mg + pad, mg + 8),
              MENSAJES["visor_arg_titulo"], font=f_header, fill=D["accent"])
    draw.text((mg + pad, mg + 34),
              f"{ts} AR  ·  {hoy}  ·  {MENSAJES['fuente_datos']}",
              font=f_sub, fill=D["text_muted"])

    y_col_hdr = mg + header_h
    for ci, col in enumerate(columnas):
        cx = mg + ci * (cw + col_gap)
        draw.rounded_rectangle(
            [cx, y_col_hdr, cx + cw, y_col_hdr + col_hdr_h],
            radius=4, fill=D["bg_col_hdr"], outline=D["border"]
        )
        draw.text((cx + pad, y_col_hdr + 6),
                  col["cabecera"], font=f_col_hdr, fill=D["col_accent"])

    y_start = mg + header_h + col_hdr_h + gap

    for ci, (col, filas_col) in enumerate(zip(columnas, datos_cols)):
        cx = mg + ci * (cw + col_gap)
        for ri, row in enumerate(filas_col):
            y       = y_start + ri * (ch + gap)
            precio  = row["precio"]
            pct     = row["pct"]
            color_v = _color_variacion(pct, D)

            draw.rounded_rectangle(
                [cx, y, cx + cw, y + ch],
                radius=5, fill=D["bg_card"], outline=D["border"]
            )
            draw.rectangle([cx, y + 4, cx + 3, y + ch - 4], fill=color_v)

            x0 = cx + pad
            draw.text((x0, y + 5),  row["ticker"], font=f_ticker, fill=D["text_white"])
            draw.text((x0, y + 24), row["nombre"], font=f_nombre, fill=D["text_muted"])

            if precio is not None:
                if precio >= 1000:
                    p_str = f"${precio:,.0f}"
                elif precio >= 10:
                    p_str = f"${precio:.2f}"
                else:
                    p_str = f"${precio:.3f}"
                draw.text((x0, y + 38), p_str,
                          font=f_precio, fill=D["text_white"])
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
# SECCIÓN 6 — VISOR BCRA (Tarjeta PNG con Pillow)  — v3
# Columnas: INDICADOR | FECHA | VALOR
# La FECHA es la real de la API (ultFechaInformada de bcra-connector).
# ═══════════════════════════════════════════════════════════════════

def _bcra_variable(var_id: int, todas: dict) -> tuple:
    """
    Retorna (valor: float|None, fecha: str|None).
    fecha se formatea DD/MM/YYYY a partir de ultFechaInformada.
    """
    item = todas.get(var_id)
    if item is None:
        return None, None
    try:
        valor = float(item.ultValorInformado) if item.ultValorInformado is not None else None
        fecha = None
        if hasattr(item, "ultFechaInformada") and item.ultFechaInformada:
            fecha = item.ultFechaInformada.strftime("%d/%m/%Y")
        return valor, fecha
    except Exception:
        return None, None


def _bcra_buscar_por_descripcion(todas: dict, palabras_clave: list) -> tuple:
    """
    Búsqueda dinámica por palabras clave en la descripción de la variable.
    Retorna (valor: float|None, fecha: str|None).
    """
    palabras_lower = [p.lower() for p in palabras_clave]
    for var_id, v in todas.items():
        desc = getattr(v, "descripcion", "") or ""
        if all(p in desc.lower() for p in palabras_lower):
            try:
                valor = float(v.ultValorInformado) if v.ultValorInformado is not None else None
                fecha = None
                if hasattr(v, "ultFechaInformada") and v.ultFechaInformada:
                    fecha = v.ultFechaInformada.strftime("%d/%m/%Y")
                print(f"    🔍 ID {var_id} '{desc[:50]}': {valor} — {fecha}")
                return valor, fecha
            except Exception:
                pass
    return None, None


def _riesgo_pais() -> tuple:
    """
    Riesgo País desde argentinadatos.com.
    Retorna (valor: float|None, fecha: str|None).
    """
    try:
        data = fetch_with_retry(APIS["RIESGO_PAIS"], retries=3, timeout=8)
        if isinstance(data, list) and len(data) > 0:
            ultimo     = data[-1]
            valor      = float(ultimo.get("valor", 0))
            fecha_raw  = ultimo.get("fecha", "")
            fecha      = None
            if fecha_raw:
                fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
            print(f"    ✅ Riesgo País: {valor} bps — {fecha}")
            return valor, fecha
    except Exception as e:
        print(f"    ⚠️  Riesgo País: {e}")
    return None, None


def _formatear_bcra(fmt: str, valor) -> str:
    if valor is None:
        return "—"
    try:
        v = float(valor)
        if fmt == "bps":     return f"{int(v):,} bps"
        if fmt == "usd4":    return f"$ {v:,.4f}"
        if fmt == "usd_m":   return f"u$s {v:,.0f} M"
        if fmt == "pesos_m": return f"$ {v/1_000:,.0f} M"
        if fmt == "pesos":   return f"$ {v:,.2f}"
        if fmt == "pct2":    return f"{v:.2f} %"
        if fmt == "ratio":   return f"{v:,.2f}"
        if fmt == "num6":    return f"{v:.6f}"
        return f"{v:,.4f}"
    except Exception:
        return "—"


def generar_Visor_BCRA() -> str:
    """
    Genera la tarjeta PNG del Visor BCRA con columnas INDICADOR | FECHA | VALOR.
    Cada fila muestra la FECHA REAL del dato según la API del BCRA.
    Retorna el path del PNG generado.
    """
    D   = DISEÑO_VISOR_BCRA
    hoy = hora_ar().strftime("%d/%m/%Y")
    ts  = hhmm()

    print(f"\n🏦 Generando Visor BCRA ({ts})...")

    # ── 1. Descargar TODAS las variables BCRA ────────────────────
    todas = {}
    try:
        from bcra_connector import BCRAConnector
        conn      = BCRAConnector(verify_ssl=False)
        variables = conn.get_principales_variables()
        todas     = {v.idVariable: v for v in variables}
        print(f"  ✅ bcra-connector: {len(todas)} variables descargadas")
    except Exception as e:
        print(f"  ⚠️  bcra-connector: {e}")

    # ── 2. Riesgo País ────────────────────────────────────────────
    rp_valor, rp_fecha = _riesgo_pais()

    # Fallbacks para IDs que el BCRA puede discontinuar
    FALLBACKS_BCRA = {
        44: ["tamar", "bancos", "privados"],
        15: ["base", "monetaria"],
    }

    # ── 3. Recolectar valores y fechas ────────────────────────────
    # raw = { id_var: {"valor": float|None, "fecha": str|None} }
    raw = {}
    for (var_id, etiqueta, fmt) in VISOR_BCRA_ITEMS:

        if var_id is None:
            raw[var_id] = {"valor": rp_valor, "fecha": rp_fecha}

        elif isinstance(var_id, str) and var_id.startswith("calc:"):
            ids    = var_id[5:].split("/")
            id_num = int(ids[0])
            id_den = int(ids[1])
            v_num, f_num = _bcra_variable(id_num, todas)
            v_den, _     = _bcra_variable(id_den, todas)
            resultado    = (v_num / v_den) if (v_num and v_den) else None
            # Fecha del numerador como referencia
            raw[var_id] = {"valor": resultado, "fecha": f_num}

        else:
            valor, fecha = _bcra_variable(var_id, todas)
            if valor is None and var_id in FALLBACKS_BCRA:
                print(f"  🔍 ID {var_id} no encontrado. Buscando por descripción...")
                valor, fecha = _bcra_buscar_por_descripcion(todas, FALLBACKS_BCRA[var_id])
            raw[var_id] = {"valor": valor, "fecha": fecha}

        entry = raw[var_id]
        print(f"  → {etiqueta}: {_formatear_bcra(fmt, entry['valor'])}  [{entry['fecha'] or '—'}]")

    # ── 4. Dibujar tarjeta Pillow ─────────────────────────────────
    pad      = D["padding"]
    rh       = D["row_height"]
    n_items  = len(VISOR_BCRA_ITEMS)
    header_h = 80
    colhdr_h = 36
    canvas_w = D["width"]
    canvas_h = header_h + colhdr_h + n_items * rh + pad

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg"])
    draw = ImageDraw.Draw(img)

    # Borde exterior
    draw.rectangle([0, 0, canvas_w - 1, canvas_h - 1],
                   outline=D["border"], width=3)

    # Header azul
    draw.rectangle([0, 0, canvas_w, header_h], fill=D["header_bg"])
    fh1 = _get_font(D["font_header"], bold=True)
    fh2 = _get_font(D["font_sub"],    bold=False)
    draw.text((pad, 14), MENSAJES["visor_bcra_titulo"], font=fh1, fill=D["header_text"])
    draw.text((pad, 48), f"Fuente: BCRA  —  {hoy}",    font=fh2, fill="#bfdbfe")

    # ── Coordenadas de las 3 columnas ────────────────────────────
    # INDICADOR: x=pad    (~280px ancho)
    # FECHA:     x=330    (~160px ancho)
    # VALOR:     x=500    (hasta el borde)
    x_label = pad
    x_fecha = 330
    x_valor = 500
    x_div1  = 322   # separador vertical tras INDICADOR
    x_div2  = 492   # separador vertical tras FECHA

    # Fila de cabeceras de columna
    col_y = header_h + 6
    fch   = _get_font(D["font_label"], bold=True)
    draw.text((x_label, col_y), "INDICADOR", font=fch, fill=D["col_header"])
    draw.text((x_fecha, col_y), "FECHA",     font=fch, fill=D["col_header"])
    draw.text((x_valor, col_y), "VALOR",     font=fch, fill=D["col_header"])

    # Línea separadora bajo cabecera de columnas
    sep_y = header_h + colhdr_h
    draw.line([(pad, sep_y), (canvas_w - pad, sep_y)], fill=D["border"], width=2)

    # Fuentes para filas de datos
    fl = _get_font(D["font_label"], bold=False)   # etiqueta (normal)
    fv = _get_font(D["font_value"], bold=True)    # valor (bold)
    fd = _get_font(D["font_value"], bold=False)   # fecha (normal)

    for idx, (var_id, etiqueta, fmt) in enumerate(VISOR_BCRA_ITEMS):
        y    = sep_y + idx * rh
        fill = "#dbeafe" if idx % 2 == 0 else "#e0f2fe"
        draw.rectangle([1, y, canvas_w - 1, y + rh - 1], fill=fill)

        # Separadores verticales de columna
        draw.line([(x_div1, y), (x_div1, y + rh)], fill=D["divider"], width=1)
        draw.line([(x_div2, y), (x_div2, y + rh)], fill=D["divider"], width=1)

        entry      = raw.get(var_id, {"valor": None, "fecha": None})
        valor_str  = _formatear_bcra(fmt, entry["valor"])
        fecha_str  = entry["fecha"] or "—"

        draw.text((x_label, y + 11), etiqueta,  font=fl, fill=D["label_color"])
        draw.text((x_fecha, y + 11), fecha_str, font=fd, fill=D["date_color"])
        draw.text((x_valor, y + 11), valor_str, font=fv, fill=D["value_color"])

    # Línea de cierre inferior
    draw.line([(pad, sep_y + n_items * rh), (canvas_w - pad, sep_y + n_items * rh)],
              fill=D["border"], width=2)

    path = ARCHIVOS["visor_bcra_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor BCRA guardado: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 Iniciando Placas_a_Telegram")
    print(f"🕐 Hora actual: {hora_ar().strftime('%d/%m/%Y %H:%M:%S')} AR")
    print()

    if not es_dia_habil():
        print("✅ Script finalizado (día no hábil)")
        sys.exit(0)

    limpiar_estado_viejo()

    ahora = hhmm()

    tareas_a_ejecutar = [
        tarea for tarea, horario in HORARIOS.items()
        if es_hora_exacta(horario)
    ]

    if not tareas_a_ejecutar:
        print(f"⏰ No hay tarea programada para {ahora}")
        print("💡 Los horarios configurados son:")
        for tarea, horario in HORARIOS.items():
            print(f"   - {tarea}: {horario}")
        sys.exit(0)

    print(f"📋 Tareas detectadas: {', '.join(tareas_a_ejecutar)}")
    print()

    for tarea_ejecutar in tareas_a_ejecutar:

        if ya_se_envio(tarea_ejecutar):
            print(f"⏭️  {tarea_ejecutar}: ya enviado hoy. Saltando.")
            continue

        print(f"▶️  Ejecutando: {tarea_ejecutar}")

        if tarea_ejecutar.startswith("imagen"):
            estado = "Cerrado" if "cierre" in tarea_ejecutar else "Abierto"
            generar_Imagen_ARG(estado=estado)
            marcar_enviado(tarea_ejecutar)

        elif tarea_ejecutar.startswith("visor_arg"):
            path = generar_Visor_ARG()
            ts   = hhmm()
            hoy  = hora_ar().strftime("%d/%m/%Y")
            caption = f"{MENSAJES['visor_arg_tg']} — {ts} AR  ·  {hoy}"
            tg_foto(path, caption)
            print(f"  📨 Visor ARG enviado a Telegram")
            marcar_enviado(tarea_ejecutar)

        elif tarea_ejecutar == "visor_bcra":
            path = generar_Visor_BCRA()
            ts   = hhmm()
            hoy  = hora_ar().strftime("%d/%m/%Y")
            caption = f"{MENSAJES['visor_bcra_tg']} — {hoy}"
            tg_foto(path, caption)
            print(f"  📨 Visor BCRA enviado a Telegram")
            marcar_enviado(tarea_ejecutar)

        print()

    print("✅ Script finalizado correctamente")
