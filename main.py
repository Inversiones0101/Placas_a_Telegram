"""
main.py — Placas_a_Telegram
Inversiones & Algoritmos · GitHub Actions

Funciones:
  1. generar_Visor_RF_ARG()  — Tarjeta PNG Renta Fija (Bonos/Letras/MEP) → Telegram
  2. generar_Visor_ARG()     — Tarjeta PNG ADRs/Stocks/CEDEARs → Telegram
  3. generar_Visor_BCRA()    — Tarjeta PNG datos BCRA → Telegram

Arquitectura: cron en horarios fijos → cada ejecución dura ~1 min → sale.
Sin Playwright. Control de doble envío via estado_envios.csv.
"""

import os, sys, requests, time
import pandas as pd
from datetime import datetime, date
import pytz

from config import (
    APIS,
    VISOR_ARG_COL1, VISOR_ARG_COL2, VISOR_ARG_COL3,
    VISOR_RF_SECCIONES,
    VISOR_BCRA_ITEMS,
    HORARIOS, ARCHIVOS,
    DISEÑO_VISOR_ARG, DISEÑO_VISOR_RF, DISEÑO_VISOR_BCRA,
    MENSAJES,
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
        print("⏸️  Fin de semana. Sin operación.")
        return False
    try:
        resp   = requests.get(f"{APIS['FERIADOS']}{hoy.year}", timeout=8)
        fechas = [f["fecha"] for f in resp.json() if "fecha" in f]
        if hoy.strftime("%Y-%m-%d") in fechas:
            print("🗓️  Feriado hoy. Sin operación.")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar feriados: {e}")
    return True

def es_hora_exacta(h_obj: str, tolerancia: int = 44) -> bool:
    ahora  = hora_ar()
    hh, mm = map(int, h_obj.split(":"))
    obj    = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
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
    df  = _leer_estado_csv(ARCHIVOS["estado_envios"])
    hoy = hora_ar().strftime("%Y-%m-%d")
    return not df.empty and ((df["fecha"] == hoy) & (df["clave"] == clave)).any()

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
        print(f"{'📨' if r.status_code == 200 else '⚠️ '} Telegram foto [{r.status_code}]")
        if r.status_code != 200:
            print(r.text[:300])
    except Exception as e:
        print(f"⚠️  tg_foto: {e}")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 4 — UTILIDADES GRÁFICAS (Pillow)
# ═══════════════════════════════════════════════════════════════════

def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ] if bold else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def fetch_with_retry(url: str, retries: int = 3, timeout: int = 10):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries - 1:
                raise
            wait = 2 ** i
            print(f"  ⚠️  Reintentando en {wait}s... ({i+1}/{retries})")
            time.sleep(wait)

def _fetch_api(clave: str) -> dict:
    """Descarga la API indicada y devuelve dict {symbol: item}."""
    try:
        data = fetch_with_retry(APIS[clave], retries=3, timeout=10)
        return {item["symbol"]: item for item in data}
    except Exception as e:
        print(f"⚠️  Error API {clave}: {e}")
        return {}

def _color_var(pct, D: dict) -> str:
    if pct is None: return D["neutral"]
    if pct > 0:     return D["up"]
    if pct < 0:     return D["down"]
    return D["neutral"]

def _flecha(pct) -> str:
    if pct is None: return "—"
    if pct > 0:     return "▲"
    if pct < 0:     return "▼"
    return "▬"

def _fmt_precio(precio) -> str:
    if precio is None:  return "—"
    if precio >= 1000:  return f"${precio:,.0f}"
    if precio >= 10:    return f"${precio:,.2f}"
    return f"${precio:.3f}"


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 5 — VISOR RENTA FIJA ARG
# ═══════════════════════════════════════════════════════════════════

def generar_Visor_RF_ARG() -> str:
    """
    Genera tarjeta PNG del Visor Renta Fija ARG con secciones
    (Soberanos y Letras). Retorna el path del PNG.

    Fuentes de datos (config.py → APIS):
      "BONOS"  → https://data912.com/live/arg_bonds
      "LETRAS" → https://data912.com/live/arg_notes
      "MEP"    → https://data912.com/live/mep

    Los items MEP (tipo cambio implícito) se muestran en dorado.
    """
    D   = DISEÑO_VISOR_RF
    ts  = hhmm()
    hoy = hora_ar().strftime("%d/%m/%Y")

    print(f"📊 Generando Visor Renta Fija ARG ({ts})...")

    # ── 1. Descargar APIs (una vez por fuente) ───────────────────
    cache: dict[str, dict] = {}

    # ── 2. Recolectar datos por sección ─────────────────────────
    secciones_datos = []
    for sec in VISOR_RF_SECCIONES:
        filas = []
        for symbol, nombre, fuente in sec["items"]:
            if fuente not in cache:
                cache[fuente] = _fetch_api(fuente)
            item   = cache[fuente].get(symbol)
            precio = float(item["c"])          if item and item.get("c")          is not None else None
            pct    = float(item["pct_change"]) if item and item.get("pct_change") is not None else None
            filas.append({
                "symbol": symbol,
                "nombre": nombre,
                "fuente": fuente,
                "precio": precio,
                "pct":    pct,
            })
            p_str = _fmt_precio(precio)
            v_str = f"{pct:+.2f}%" if pct is not None else "—"
            print(f"  [{sec['titulo'][:15]}] {symbol}: {p_str} {v_str}")
        secciones_datos.append({"titulo": sec["titulo"], "filas": filas})

    # ── 3. Calcular dimensiones del canvas ───────────────────────
    COLS    = D["cols"]
    CARD_W  = D["card_w"]
    CARD_H  = D["card_h"]
    GAP     = D["gap"]
    MG      = D["margin"]
    COL_GAP = D["col_gap"]
    SEC_H   = D["sec_h"]
    HDR_H   = 56

    total_filas_tarjetas = sum(
        (len(s["filas"]) + COLS - 1) // COLS
        for s in secciones_datos
    )
    n_secs   = len(secciones_datos)
    canvas_w = MG * 2 + CARD_W * COLS + COL_GAP * (COLS - 1)
    canvas_h = (MG + HDR_H + GAP
                + n_secs * (SEC_H + GAP)
                + total_filas_tarjetas * (CARD_H + GAP)
                + MG)

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg_canvas"])
    draw = ImageDraw.Draw(img)

    # Fuentes
    f_hdr    = _get_font(D["font_header"], bold=True)
    f_sub    = _get_font(D["font_sub"])
    f_sec    = _get_font(D["font_sec"], bold=True)
    f_ticker = _get_font(D["font_ticker"], bold=True)
    f_nombre = _get_font(D["font_nombre"])
    f_precio = _get_font(D["font_precio"], bold=True)
    f_pct    = _get_font(D["font_pct"])

    # ── 4. Header principal ──────────────────────────────────────
    draw.rounded_rectangle(
        [MG, MG, canvas_w - MG, MG + HDR_H],
        radius=8, fill=D["bg_header"], outline=D["border"]
    )
    draw.text((MG + 14, MG + 8),
              MENSAJES["visor_rf_titulo"], font=f_hdr, fill=D["accent"])
    draw.text((MG + 14, MG + 34),
              f"{ts} AR  ·  {hoy}  ·  {MENSAJES['fuente_datos']}",
              font=f_sub, fill=D["text_muted"])

    # ── 5. Secciones y cards ─────────────────────────────────────
    y = MG + HDR_H + GAP

    for sec_data in secciones_datos:
        filas  = sec_data["filas"]
        n_rows = (len(filas) + COLS - 1) // COLS

        # Cabecera de sección (ancho completo)
        draw.rounded_rectangle(
            [MG, y, canvas_w - MG, y + SEC_H],
            radius=4, fill=D["bg_sec_hdr"], outline=D["border"]
        )
        draw.text((MG + 10, y + 7), sec_data["titulo"],
                  font=f_sec, fill=D["col_accent"])
        y += SEC_H + GAP

        # Cards de la sección
        for i, row in enumerate(filas):
            r   = i // COLS
            c   = i % COLS
            cx  = MG + c * (CARD_W + COL_GAP)
            cy  = y + r * (CARD_H + GAP)

            is_mep  = row["fuente"] == "MEP"
            precio  = row["precio"]
            pct     = row["pct"]
            color_v = (D["mep_accent"] if is_mep
                       else _color_var(pct, D))

            draw.rounded_rectangle(
                [cx, cy, cx + CARD_W, cy + CARD_H],
                radius=5, fill=D["bg_card"], outline=D["border"]
            )
            # Barra lateral de color
            draw.rectangle(
                [cx, cy + 4, cx + 3, cy + CARD_H - 4],
                fill=color_v
            )

            x0 = cx + 12
            ticker_color = D["mep_accent"] if is_mep else D["text_white"]
            draw.text((x0, cy + 4),  row["symbol"], font=f_ticker, fill=ticker_color)
            draw.text((x0, cy + 21), row["nombre"], font=f_nombre, fill=D["text_muted"])
            draw.text((x0, cy + 33), _fmt_precio(precio), font=f_precio, fill=D["text_white"])

            if pct is not None:
                draw.text((x0, cy + 60),
                          f"{_flecha(pct)} {pct:+.2f}%",
                          font=f_pct, fill=color_v)
            else:
                draw.text((x0, cy + 60), "Sin dato",
                          font=f_nombre, fill=D["neutral"])

        y += n_rows * (CARD_H + GAP) + GAP

    path = ARCHIVOS["visor_rf_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor RF guardado: {path}  ({canvas_w}×{canvas_h}px)")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 6 — VISOR ARG (ADRs / Stocks / CEDEARs)
# ═══════════════════════════════════════════════════════════════════

def _dato_activo(symbol: str, fuente: str, cache: dict) -> tuple:
    if fuente not in cache:
        cache[fuente] = _fetch_api(fuente)
    item = cache[fuente].get(symbol)
    if item:
        return float(item.get("c", 0)), float(item.get("pct_change", 0))
    return None, None

def generar_Visor_ARG() -> str:
    D     = DISEÑO_VISOR_ARG
    ts    = hhmm()
    hoy   = hora_ar().strftime("%d/%m/%Y")
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
            p_str = _fmt_precio(precio)
            v_str = f"{pct:+.2f}%" if pct is not None else "—"
            print(f"  [{col['cabecera']}] {ticker}: {p_str} {v_str}")
        datos_cols.append(filas_col)

    cw      = D["card_w"]
    ch      = D["card_h"]
    gap     = D["gap"]
    mg      = D["margin"]
    pad     = D["padding"]
    col_gap = D["col_gap"]
    hdr_h   = 56
    chdr_h  = 26
    n_filas = max(len(d) for d in datos_cols)

    canvas_w = mg * 2 + cw * 3 + col_gap * 2
    canvas_h = mg + hdr_h + chdr_h + gap + n_filas * (ch + gap) + mg

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg_canvas"])
    draw = ImageDraw.Draw(img)

    f_header  = _get_font(D["font_header"],  bold=True)
    f_sub     = _get_font(D["font_sub"])
    f_col_hdr = _get_font(D["font_col_hdr"], bold=True)
    f_ticker  = _get_font(D["font_ticker"],  bold=True)
    f_nombre  = _get_font(D["font_nombre"])
    f_precio  = _get_font(D["font_precio"],  bold=True)
    f_pct     = _get_font(D["font_pct"])

    draw.rounded_rectangle(
        [mg, mg, canvas_w - mg, mg + hdr_h],
        radius=8, fill=D["bg_header"], outline=D["border"]
    )
    draw.text((mg + pad, mg + 8),
              MENSAJES["visor_arg_titulo"], font=f_header, fill=D["accent"])
    draw.text((mg + pad, mg + 34),
              f"{ts} AR  ·  {hoy}  ·  {MENSAJES['fuente_datos']}",
              font=f_sub, fill=D["text_muted"])

    y_chdr = mg + hdr_h
    for ci, col in enumerate(columnas):
        cx = mg + ci * (cw + col_gap)
        draw.rounded_rectangle(
            [cx, y_chdr, cx + cw, y_chdr + chdr_h],
            radius=4, fill=D["bg_col_hdr"], outline=D["border"]
        )
        draw.text((cx + pad, y_chdr + 6),
                  col["cabecera"], font=f_col_hdr, fill=D["col_accent"])

    y_start = mg + hdr_h + chdr_h + gap
    for ci, (col, filas_col) in enumerate(zip(columnas, datos_cols)):
        cx = mg + ci * (cw + col_gap)
        for ri, row in enumerate(filas_col):
            y       = y_start + ri * (ch + gap)
            precio  = row["precio"]
            pct     = row["pct"]
            color_v = _color_var(pct, D)

            draw.rounded_rectangle(
                [cx, y, cx + cw, y + ch],
                radius=5, fill=D["bg_card"], outline=D["border"]
            )
            draw.rectangle([cx, y + 4, cx + 3, y + ch - 4], fill=color_v)

            x0 = cx + pad
            draw.text((x0, y + 5),  row["ticker"], font=f_ticker, fill=D["text_white"])
            draw.text((x0, y + 24), row["nombre"], font=f_nombre, fill=D["text_muted"])
            draw.text((x0, y + 38), _fmt_precio(precio), font=f_precio, fill=D["text_white"])

            if pct is not None:
                draw.text((x0, y + 62),
                          f"{_flecha(pct)} {pct:+.2f}%",
                          font=f_pct, fill=color_v)
            else:
                draw.text((x0, y + 38), "Sin dato",
                          font=f_nombre, fill=D["neutral"])

    path = ARCHIVOS["visor_arg_img"]
    img.save(path, "PNG", optimize=True)
    print(f"✅ Visor ARG guardado: {path}  ({canvas_w}×{canvas_h}px)")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 7 — VISOR BCRA
# ═══════════════════════════════════════════════════════════════════

def _bcra_variable(var_id: int, todas: dict) -> tuple:
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
    try:
        data = fetch_with_retry(APIS["RIESGO_PAIS"], retries=3, timeout=8)
        if isinstance(data, list) and data:
            ultimo    = data[-1]
            valor     = float(ultimo.get("valor", 0))
            fecha_raw = ultimo.get("fecha", "")
            fecha     = (datetime.strptime(fecha_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
                         if fecha_raw else None)
            print(f"    ✅ Riesgo País: {valor} bps — {fecha}")
            return valor, fecha
    except Exception as e:
        print(f"    ⚠️  Riesgo País: {e}")
    return None, None

def _formatear_bcra(fmt: str, valor) -> str:
    if valor is None: return "—"
    try:
        v = float(valor)
        if fmt == "bps":     return f"{int(v):,} bps"
        if fmt == "usd_m":   return f"u$s {v:,.0f} M"
        if fmt == "pesos_m": return f"$ {v/1_000:,.0f} M"
        if fmt == "pesos":   return f"$ {v:,.2f}"
        if fmt == "pct2":    return f"{v:.2f} %"
        if fmt == "num6":    return f"{v:.6f}"
        return f"{v:,.4f}"
    except Exception:
        return "—"

def generar_Visor_BCRA() -> str:
    D   = DISEÑO_VISOR_BCRA
    hoy = hora_ar().strftime("%d/%m/%Y")
    ts  = hhmm()

    print(f"\n🏦 Generando Visor BCRA ({ts})...")

    todas = {}
    try:
        from bcra_connector import BCRAConnector
        conn      = BCRAConnector(verify_ssl=False)
        variables = conn.get_principales_variables()
        todas     = {v.idVariable: v for v in variables}
        print(f"  ✅ bcra-connector: {len(todas)} variables")
    except Exception as e:
        print(f"  ⚠️  bcra-connector: {e}")

    rp_valor, rp_fecha = _riesgo_pais()

    FALLBACKS_BCRA = {
        44: ["tamar", "bancos", "privados"],
        15: ["base", "monetaria"],
    }

    raw = {}
    for (var_id, etiqueta, fmt) in VISOR_BCRA_ITEMS:
        if var_id is None:
            raw[var_id] = {"valor": rp_valor, "fecha": rp_fecha}
        elif isinstance(var_id, str) and var_id.startswith("calc:"):
            ids    = var_id[5:].split("/")
            v_num, f_num = _bcra_variable(int(ids[0]), todas)
            v_den, _     = _bcra_variable(int(ids[1]), todas)
            raw[var_id]  = {"valor": (v_num / v_den if v_num and v_den else None),
                             "fecha": f_num}
        else:
            valor, fecha = _bcra_variable(var_id, todas)
            if valor is None and var_id in FALLBACKS_BCRA:
                print(f"  🔍 ID {var_id} no encontrado. Buscando por descripción...")
                valor, fecha = _bcra_buscar_por_descripcion(todas, FALLBACKS_BCRA[var_id])
            raw[var_id] = {"valor": valor, "fecha": fecha}
        entry = raw[var_id]
        print(f"  → {etiqueta}: {_formatear_bcra(fmt, entry['valor'])}  [{entry['fecha'] or '—'}]")

    pad      = D["padding"]
    rh       = D["row_height"]
    n_items  = len(VISOR_BCRA_ITEMS)
    header_h = 80
    colhdr_h = 36
    canvas_w = D["width"]
    canvas_h = header_h + colhdr_h + n_items * rh + pad

    img  = Image.new("RGB", (canvas_w, canvas_h), D["bg"])
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, canvas_w - 1, canvas_h - 1],
                   outline=D["border"], width=3)
    draw.rectangle([0, 0, canvas_w, header_h], fill=D["header_bg"])
    fh1 = _get_font(D["font_header"], bold=True)
    fh2 = _get_font(D["font_sub"])
    draw.text((pad, 14), MENSAJES["visor_bcra_titulo"], font=fh1, fill=D["header_text"])
    draw.text((pad, 48), f"Fuente: BCRA  —  {hoy}",    font=fh2, fill="#bfdbfe")

    x_label = pad;  x_fecha = 330;  x_valor = 500
    x_div1  = 322;  x_div2  = 492

    col_y = header_h + 6
    fch   = _get_font(D["font_label"], bold=True)
    draw.text((x_label, col_y), "INDICADOR", font=fch, fill=D["col_header"])
    draw.text((x_fecha, col_y), "FECHA",     font=fch, fill=D["col_header"])
    draw.text((x_valor, col_y), "VALOR",     font=fch, fill=D["col_header"])

    sep_y = header_h + colhdr_h
    draw.line([(pad, sep_y), (canvas_w - pad, sep_y)], fill=D["border"], width=2)

    fl = _get_font(D["font_label"])
    fv = _get_font(D["font_value"], bold=True)
    fd = _get_font(D["font_value"])

    for idx, (var_id, etiqueta, fmt) in enumerate(VISOR_BCRA_ITEMS):
        y    = sep_y + idx * rh
        fill = "#dbeafe" if idx % 2 == 0 else "#e0f2fe"
        draw.rectangle([1, y, canvas_w - 1, y + rh - 1], fill=fill)
        draw.line([(x_div1, y), (x_div1, y + rh)], fill=D["divider"], width=1)
        draw.line([(x_div2, y), (x_div2, y + rh)], fill=D["divider"], width=1)
        entry = raw.get(var_id, {"valor": None, "fecha": None})
        draw.text((x_label, y + 11), etiqueta,                   font=fl, fill=D["label_color"])
        draw.text((x_fecha, y + 11), entry["fecha"] or "—",      font=fd, fill=D["date_color"])
        draw.text((x_valor, y + 11), _formatear_bcra(fmt, entry["valor"]),
                  font=fv, fill=D["value_color"])

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

    tareas = [t for t, h in HORARIOS.items() if es_hora_exacta(h)]

    if not tareas:
        ahora = hhmm()
        print(f"⏰ No hay tarea programada para {ahora}")
        print("💡 Horarios configurados:")
        for t, h in HORARIOS.items():
            print(f"   - {t}: {h}")
        sys.exit(0)

    print(f"📋 Tareas detectadas: {', '.join(tareas)}")
    print()

    for tarea in tareas:
        if ya_se_envio(tarea):
            print(f"⏭️  {tarea}: ya enviado hoy. Saltando.")
            continue

        print(f"▶️  Ejecutando: {tarea}")
        ts  = hhmm()
        hoy = hora_ar().strftime("%d/%m/%Y")

        # ── Visor Renta Fija ─────────────────────────────────────
        if tarea.startswith("visor_rf"):
            path    = generar_Visor_RF_ARG()
            caption = f"{MENSAJES['visor_rf_tg']} — {ts} AR  ·  {hoy}"
            tg_foto(path, caption)
            print(f"  📨 Visor RF enviado a Telegram")
            marcar_enviado(tarea)

        # ── Visor ARG ────────────────────────────────────────────
        elif tarea.startswith("visor_arg"):
            path    = generar_Visor_ARG()
            caption = f"{MENSAJES['visor_arg_tg']} — {ts} AR  ·  {hoy}"
            tg_foto(path, caption)
            print(f"  📨 Visor ARG enviado a Telegram")
            marcar_enviado(tarea)

        # ── Visor BCRA ───────────────────────────────────────────
        elif tarea == "visor_bcra":
            path    = generar_Visor_BCRA()
            caption = f"{MENSAJES['visor_bcra_tg']} — {hoy}"
            tg_foto(path, caption)
            print(f"  📨 Visor BCRA enviado a Telegram")
            marcar_enviado(tarea)

        print()

    print("✅ Script finalizado correctamente")
