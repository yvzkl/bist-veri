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

if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else "kesif"
    klasor = sys.argv[2] if len(sys.argv) > 2 else "cikti"
    if mod == "kesif":
        kesif(klasor)
    else:
        print("bilinmeyen mod", mod); sys.exit(2)
