# Yatirim Ajani - uzun vadeli aday taramasi (temel veriler Yahoo'dan, yfinance ile). 21.11.2026.
# Kullanim: python3 temel/temel_tarama.py <kesif|tarama|derin|izle> <cikti_klasoru>
import sys, os, json, time, traceback, collections, glob, datetime as dt
import yfinance as yf

def yaz(klasor, ad, metin):
    os.makedirs(klasor, exist_ok=True)
    with open(os.path.join(klasor, ad), "w", encoding="utf-8") as f:
        f.write(metin)

def kesif(klasor):
    L = ["yfinance " + getattr(yf, "__version__", "?")]
    try:
        from yfinance.const import EQUITY_SCREENER_FIELDS as F
        L.append("EQUITY_SCREENER_FIELDS kategoriler: " + ", ".join(sorted(F)))
        for k in sorted(F):
            L.append("  %s: %s" % (k, ", ".join(sorted(F[k]))))
    except Exception as e:
        L.append("alan listesi yok: %r" % e)
    try:
        Q = yf.EquityQuery
        q = Q("and", [Q("eq", ["region", "us"]), Q("btwn", ["intradaymarketcap", 3e8, 4e10]), Q("gte", ["intradayprice", 3])])
        r = yf.screen(q, offset=0, size=25, sortField="intradaymarketcap", sortAsc=False)
        L.append("ekran tamam: total=%s, gelen=%d" % (r.get("total"), len(r.get("quotes", []))))
        if r.get("quotes"):
            L.append("ilk sonuc alanlari: " + ", ".join(sorted(r["quotes"][0].keys())))
            L.append("ilk 5: " + ", ".join(x.get("symbol", "?") for x in r["quotes"][:5]))
    except Exception:
        L.append("ekran HATA:\n" + traceback.format_exc())
    for s in ("CRDO", "THYAO.IS"):
        try:
            i = yf.Ticker(s).info
            L.append("%s info anahtar sayisi %d" % (s, len(i)))
            for k in ("marketCap", "enterpriseValue", "totalRevenue", "revenueGrowth", "grossMargins", "operatingMargins",
                      "freeCashflow", "operatingCashflow", "ebitda", "totalDebt", "totalCash", "returnOnEquity",
                      "returnOnAssets", "heldPercentInsiders", "trailingPE", "forwardPE", "priceToSalesTrailing12Months",
                      "averageDailyVolume3Month", "currentPrice", "financialCurrency", "currency", "sector", "industry"):
                L.append("  %s = %r" % (k, i.get(k)))
        except Exception:
            L.append("%s info HATA:\n%s" % (s, traceback.format_exc()))
    yaz(klasor, "kesif.txt", "\n".join(L) + "\n")
    print("\n".join(L))


ALANLAR = ("shortName", "longName", "sector", "industry", "country", "exchange", "quoteType", "marketCap", "enterpriseValue",
           "totalRevenue", "revenueGrowth", "earningsGrowth", "grossMargins", "operatingMargins", "ebitdaMargins",
           "profitMargins", "freeCashflow", "operatingCashflow", "ebitda", "totalDebt", "totalCash", "returnOnEquity",
           "returnOnAssets", "heldPercentInsiders", "heldPercentInstitutions", "trailingPE", "forwardPE",
           "priceToSalesTrailing12Months", "enterpriseToRevenue", "enterpriseToEbitda", "averageDailyVolume3Month",
           "currentPrice", "previousClose", "financialCurrency", "currency", "fullTimeEmployees", "52WeekChange",
           "beta", "numberOfAnalystOpinions", "sharesOutstanding", "bookValue", "fiftyTwoWeekHigh", "fiftyTwoWeekLow")
BORSALAR = ["NMS", "NGM", "NCM", "NYQ", "ASE"]

def _toplam(q):
    try:
        return yf.screen(q, offset=0, size=1).get("total")
    except Exception as e:
        return "HATA %r" % (e,)

def evren_abd(L):
    """Yahoo ekranindan ABD hisseleri: borsada islem goren, piyasa degeri 300 milyon-40 milyar $, fiyat >= 3 $,
    3 aylik ortalama hacim >= 200 bin adet, 1 yillik gelir buyumesi >= %15, brut marj >= %40, kaldiracli serbest
    nakit akisi > 0 (son 12 ay)."""
    Q = yf.EquityQuery
    taban = [Q("eq", ["region", "us"]), Q("is-in", ["exchange"] + BORSALAR), Q("btwn", ["intradaymarketcap", 3e8, 4e10]),
             Q("gte", ["intradayprice", 3]), Q("gte", ["avgdailyvol3m", 200000])]
    # birim denetimi: marj yuzde mi kesir mi?
    L.append("taban toplam: %s" % _toplam(Q("and", taban)))
    L.append("marj yuzde (40-100): %s | kesir (0.4-1): %s" % (
        _toplam(Q("and", taban + [Q("btwn", ["grossprofitmargin.lasttwelvemonths", 40, 100])])),
        _toplam(Q("and", taban + [Q("btwn", ["grossprofitmargin.lasttwelvemonths", 0.4, 1])]))))
    q = Q("and", taban + [Q("gte", ["totalrevenues1yrgrowth.lasttwelvemonths", 15]),
                          Q("gte", ["grossprofitmargin.lasttwelvemonths", 40]),
                          Q("gt", ["leveredfreecashflow.lasttwelvemonths", 0])])
    S, off = [], 0
    while True:
        r = yf.screen(q, offset=off, size=250, sortField="intradaymarketcap", sortAsc=True)
        qs = r.get("quotes", [])
        S += [x["symbol"] for x in qs if x.get("symbol")]
        L.append("sayfa offset=%d gelen=%d toplam=%s" % (off, len(qs), r.get("total")))
        if len(qs) < 250 or off >= 2000:
            break
        off += 250
    return sorted(set(S))

def bilgi(s, tekrar=2):
    for k in range(tekrar):
        try:
            i = yf.Ticker(s).info or {}
            d = {a: i.get(a) for a in ALANLAR}
            d["ozet"] = (i.get("longBusinessSummary") or "")[:600]
            d["sembol"] = s
            return d
        except Exception as e:
            hata = repr(e)
            time.sleep(3 + 5 * k)
    return {"sembol": s, "hata": hata}

def tarama(klasor):
    import datetime as dt
    L = ["yfinance " + getattr(yf, "__version__", "?"), "zaman " + dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]
    ev = evren_abd(L)
    L.append("ABD evreni: %d hisse" % len(ev))
    sys.path.insert(0, os.getcwd())
    try:
        import bist_cek
        bist = [k + ".IS" for k in bist_cek.BIST]
    except Exception as e:
        bist = []; L.append("BIST listesi alinamadi: %r" % e)
    try:
        usdtry = yf.Ticker("USDTRY=X").fast_info["lastPrice"]
    except Exception as e:
        usdtry = None; L.append("USDTRY alinamadi: %r" % e)
    K = {"zaman": L[1][6:], "usdtry": usdtry, "abd": [], "bist": []}
    for grup, liste in (("abd", ev), ("bist", bist)):
        for n, s in enumerate(liste):
            K[grup].append(bilgi(s))
            time.sleep(0.4)
            if n % 50 == 0:
                print(grup, n, "/", len(liste), flush=True)
    hatali = [d["sembol"] for g in ("abd", "bist") for d in K[g] if "hata" in d]
    L.append("bilgi alinamayan: %d %s" % (len(hatali), ",".join(hatali[:30])))
    os.makedirs("sonuc", exist_ok=True)
    with open("sonuc/temel-tarama.json", "w", encoding="utf-8") as f:
        json.dump(K, f, ensure_ascii=False)
    yaz(klasor, "tarama.txt", "\n".join(L) + "\n")
    print("\n".join(L))

# --- derin: secilen hisselerin yillik/ceyreklik tablolari + kayit gunu kapanis fiyatlari ---
KAYIT_GUNU = "2026-11-20"
KIYAS = ["IWM", "RSP", "SPY", "QQQ"]
SATIR_GELIR = ("Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Research And Development",
               "Diluted Average Shares", "Basic Average Shares")
SATIR_NAKIT = ("Free Cash Flow", "Operating Cash Flow", "Capital Expenditure", "Stock Based Compensation",
               "Repurchase Of Capital Stock")

def _sayi(v):
    try:
        v = float(v)
    except Exception:
        return None
    return None if v != v else v

def _tablo(df, satirlar):
    out = {}
    if df is None or getattr(df, "empty", True):
        return out
    for r in satirlar:
        if r in df.index:
            out[r] = {str(k.date() if hasattr(k, "date") else k): _sayi(v) for k, v in df.loc[r].items()}
    return out

def _df(df):
    if df is None or getattr(df, "empty", True):
        return None
    return json.loads(df.to_json(orient="split", date_format="iso", default_handler=str))

def derin_bir(s):
    t = yf.Ticker(s)
    d = {"sembol": s}
    isler = (("yillik_gelir", lambda: _tablo(t.income_stmt, SATIR_GELIR)),
             ("yillik_nakit", lambda: _tablo(t.cashflow, SATIR_NAKIT)),
             ("ceyrek_gelir", lambda: _tablo(t.quarterly_income_stmt, SATIR_GELIR)),
             ("ceyrek_nakit", lambda: _tablo(t.quarterly_cashflow, SATIR_NAKIT)),
             ("gelir_tahmini", lambda: _df(t.revenue_estimate)),
             ("iceriden_alim", lambda: _df(t.insider_purchases)))
    for ad, fn in isler:
        for k in range(2):
            try:
                d[ad] = fn()
                d.pop(ad + "_hata", None)
                break
            except Exception as e:
                d[ad + "_hata"] = repr(e)[:200]
                time.sleep(2 + 3 * k)
    return d

def _indir(semboller, bas, son=None):
    return yf.download(semboller, start=bas, end=son, auto_adjust=False, progress=False, threads=True, group_by="column")

def kayit_fiyatlari(semboller, gun):
    g = dt.date.fromisoformat(gun)
    df = _indir(semboller, (g - dt.timedelta(days=6)).isoformat(), (g + dt.timedelta(days=1)).isoformat())
    F = {}
    for s in semboller:
        try:
            c = df["Close"][s].dropna(); a = df["Adj Close"][s].dropna()
            c = c[c.index.date <= g]; a = a[a.index.date <= g]
            F[s] = {"tarih": str(c.index[-1].date()), "kapanis": round(float(c.iloc[-1]), 4), "duz_kapanis": round(float(a.iloc[-1]), 4)}
        except Exception as e:
            F[s] = {"hata": repr(e)[:120]}
    return F

def derin(klasor):
    L = ["yfinance " + getattr(yf, "__version__", "?"), "zaman " + dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]
    liste = [x.strip() for x in open("temel/derin_liste.txt") if x.strip()]
    evren = [x.strip() for x in open("temel/evren_liste.txt") if x.strip()]
    K = {"zaman": L[1][6:], "kayit_gunu": KAYIT_GUNU,
         "fiyat": kayit_fiyatlari(sorted(set(evren + liste + KIYAS)), KAYIT_GUNU), "tablo": {}}
    for n, s in enumerate(liste):
        K["tablo"][s] = derin_bir(s)
        time.sleep(0.3)
        if n % 25 == 0:
            print("derin", n, "/", len(liste), flush=True)
    eksik_f = [s for s, v in K["fiyat"].items() if "hata" in v]
    eksik_t = [s for s, v in K["tablo"].items() if not v.get("yillik_gelir")]
    L.append("fiyat alinamayan: %d %s" % (len(eksik_f), ",".join(eksik_f[:30])))
    L.append("yillik tablo alinamayan: %d %s" % (len(eksik_t), ",".join(eksik_t[:30])))
    L.append("fiyat tarihleri: %s" % dict(collections.Counter(v.get("tarih") for v in K["fiyat"].values())))
    hatalar = collections.Counter(k for v in K["tablo"].values() for k in v if k.endswith("_hata"))
    L.append("tablo hatalari: %s" % dict(hatalar))
    os.makedirs("sonuc", exist_ok=True)
    with open("sonuc/temel-derin.json", "w", encoding="utf-8") as f:
        json.dump(K, f, ensure_ascii=False)
    yaz(klasor, "derin.txt", "\n".join(L) + "\n")
    print("\n".join(L))

# --- izle: kayitli sepetlerin kayit gununden bugune toplam getirisi (temettu duzeltmeli, ayni seriden) ---
def izle(klasor):
    L = ["zaman " + dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]
    for yol in sorted(glob.glob("temel/kayit/uzun-vade-kayit-*.json")):
        R = json.load(open(yol, encoding="utf-8"))
        kid, gun = R["kayit_id"], R["kayit_fiyati_tarihi"]
        hedef = "sonuc/uzun-vade-izleme-%s.json" % kid
        onceki = json.load(open(hedef, encoding="utf-8")) if os.path.exists(hedef) else {"getiri": {}}
        semboller = sorted(set(s for v in R["sepetler"].values() for s in v) | set(R["kiyas"]))
        df = _indir(semboller, gun)
        G = {}
        for s in semboller:
            try:
                a = df["Adj Close"][s].dropna()
                if a.empty or str(a.index[0].date()) != gun:
                    raise ValueError("kayit gunu verisi yok")
                G[s] = {"getiri": round(float(a.iloc[-1] / a.iloc[0] - 1), 5), "son_tarih": str(a.index[-1].date()), "kaynak": "yahoo"}
            except Exception as e:
                o = onceki["getiri"].get(s)
                G[s] = dict(o, kaynak="onceki_izleme (" + repr(e)[:60] + ")") if o else {"getiri": None, "kaynak": "yok (" + repr(e)[:60] + ")"}
        S = {}
        for ad, liste in R["sepetler"].items():
            x = sorted(G[s]["getiri"] for s in liste if G[s]["getiri"] is not None)
            if x:
                S[ad] = {"n": len(x), "eksik": len(liste) - len(x), "esit_agirlik": round(sum(x) / len(x), 5),
                         "medyan": round(x[len(x) // 2] if len(x) % 2 else (x[len(x) // 2 - 1] + x[len(x) // 2]) / 2, 5),
                         "kat3_ustu": sum(1 for v in x if v >= 2.0), "yari_kayip": sum(1 for v in x if v <= -0.5)}
        son = max((v["son_tarih"] for v in G.values() if v.get("son_tarih")), default=None)
        Z = {"kayit_id": kid, "kayit_fiyati_tarihi": gun, "guncelleme": L[0][6:], "son_gun": son,
             "sepet": S, "kiyas": {s: G[s]["getiri"] for s in R["kiyas"]}, "getiri": G}
        os.makedirs("sonuc", exist_ok=True)
        with open(hedef, "w", encoding="utf-8") as f:
            json.dump(Z, f, ensure_ascii=False, indent=1)
        L.append("%s son gun %s | %s | kiyas %s" % (kid, son, {k: v["esit_agirlik"] for k, v in S.items()}, Z["kiyas"]))
    yaz(klasor, "izle.txt", "\n".join(L) + "\n")
    print("\n".join(L))

if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else "kesif"
    klasor = sys.argv[2] if len(sys.argv) > 2 else "cikti"
    if mod == "kesif":
        kesif(klasor)
    elif mod == "tarama":
        tarama(klasor)
    elif mod == "derin":
        derin(klasor)
    elif mod == "izle":
        izle(klasor)
    else:
        print("bilinmeyen mod", mod); sys.exit(2)
