# Derin olcutler: temel-tarama.json + temel-derin.json -> her hisse icin cok yillik olcutler. Kullanim: python3 derin_olc.py
import json

def _seri(tab, satir):
    s = (tab or {}).get(satir) or {}
    return sorted(((d, v) for d, v in s.items() if v is not None), reverse=True)

def _ttm(ceyrek, yillik, satir):
    q = _seri(ceyrek, satir)
    if len(q) >= 4:
        return sum(v for _, v in q[:4]), "4c"
    y = _seri(yillik, satir)
    return (y[0][1], "yil") if y else (None, None)

def _df_satir(df, ad, sutun):
    if not df:
        return None
    try:
        i = df["index"].index(ad); j = df["columns"].index(sutun)
        return df["data"][i][j]
    except Exception:
        return None

def olc(info, tab, fiyat):
    yg, yn, cg, cn = (tab.get(k) or {} for k in ("yillik_gelir", "yillik_nakit", "ceyrek_gelir", "ceyrek_nakit"))
    r = _seri(yg, "Total Revenue")
    m = {}
    if len(r) >= 4 and r[3][1] > 0:
        m["cagr"], m["cagr_yil"] = (r[0][1] / r[3][1]) ** (1 / 3) - 1, 3
    elif len(r) >= 3 and r[2][1] > 0:
        m["cagr"], m["cagr_yil"] = (r[0][1] / r[2][1]) ** (1 / 2) - 1, 2
    else:
        m["cagr"], m["cagr_yil"] = None, 0
    m["gelir_yillar"] = [round(v / 1e6) for _, v in r[:4]]
    gp = _seri(yg, "Gross Profit")
    m["brut_son"] = gp[0][1] / r[0][1] if gp and r and r[0][1] else None
    m["brut_ilk"] = gp[-1][1] / dict(r)[gp[-1][0]] if gp and dict(r).get(gp[-1][0]) else None
    rev_ttm, kay = _ttm(cg, yg, "Total Revenue")
    fcf_ttm, _ = _ttm(cn, yn, "Free Cash Flow")
    sbc_ttm, _ = _ttm(cn, yn, "Stock Based Compensation")
    op_ttm, _ = _ttm(cg, yg, "Operating Income")
    mc = info["marketCap"]
    m["gelir_ttm"] = rev_ttm
    m["fcf_ttm"] = fcf_ttm
    m["sbc_ttm"] = sbc_ttm or 0.0
    m["sbc_gelir"] = (sbc_ttm or 0) / rev_ttm if rev_ttm else None
    m["fcf_sbc_getiri"] = (fcf_ttm - (sbc_ttm or 0)) / mc if fcf_ttm is not None else None
    m["faal_marj_ttm"] = op_ttm / rev_ttm if op_ttm is not None and rev_ttm else None
    rd = _seri(yg, "Research And Development")
    m["arge_gelir"] = rd[0][1] / r[0][1] if rd and r and r[0][1] else 0.0
    sh = _seri(yg, "Diluted Average Shares") or _seri(yg, "Basic Average Shares")
    m["seyrelme"] = (sh[0][1] / sh[min(3, len(sh) - 1)][1] - 1) if len(sh) >= 2 and sh[min(3, len(sh) - 1)][1] else None
    m["seyrelme_yil"] = min(3, len(sh) - 1) if len(sh) >= 2 else 0
    gt = tab.get("gelir_tahmini")
    m["tahmin_bu_yil"] = _df_satir(gt, "0y", "growth")
    m["tahmin_gelecek_yil"] = _df_satir(gt, "+1y", "growth")
    m["tahmin_analist"] = _df_satir(gt, "+1y", "numberOfAnalysts")
    ia = tab.get("iceriden_alim")
    try:
        satirlar = {row[0]: row[1] for row in ia["data"]}
        m["iceriden_net_6a"] = satirlar.get("% Net Shares Purchased (Sold)")
    except Exception:
        m["iceriden_net_6a"] = None
    m["net_nakit"] = ((info.get("totalCash") or 0) - (info.get("totalDebt") or 0)) / mc
    m["mcap"] = mc
    m["fiyat"] = fiyat
    return m

def hepsi(K=None, D=None):
    from puanla import hazirla
    if K is None:
        K = json.load(open("temel-tarama.json"))
    if D is None:
        D = json.load(open("temel-derin.json"))
    U, _ = hazirla(K)
    out = {}
    for d in U:
        s = d["sembol"]
        out[s] = dict(olc(d, D["tablo"][s], D["fiyat"][s]), info=d)
    return out, D
