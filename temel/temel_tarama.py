# Yatirim Ajani - uzun vadeli aday taramasi (temel veriler Yahoo'dan, yfinance ile). 21.11.2026.
# Kullanim: python3 temel/temel_tarama.py <kesif|tarama> <cikti_klasoru>
import sys, os, json, time, traceback
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

if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else "kesif"
    klasor = sys.argv[2] if len(sys.argv) > 2 else "cikti"
    if mod == "kesif":
        kesif(klasor)
    elif mod == "tarama":
        tarama(klasor)
    else:
        print("bilinmeyen mod", mod); sys.exit(2)
