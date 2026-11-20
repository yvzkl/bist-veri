# Uzun vadeli aday puanlamasi (temel-tarama.json -> sirali tablo). Kullanim: python3 puanla.py <json> [ilk_n]
import json, sys, math

def yuzdelik(degerler, x, buyuk_iyi=True):
    v = sorted(d for d in degerler if d is not None)
    if x is None or not v:
        return 0.5
    k = sum(1 for d in v if d < x) + 0.5 * sum(1 for d in v if d == x)
    p = k / len(v)
    return p if buyuk_iyi else 1 - p

def hazirla(K):
    U, ele = [], {}
    for d in K["abd"]:
        s = d.get("sembol")
        def r(n): ele[n] = ele.get(n, 0) + 1
        if "hata" in d: r("bilgi yok"); continue
        if d.get("quoteType") not in (None, "EQUITY"): r("hisse degil"); continue
        if d.get("sector") in ("Financial Services", "Real Estate"): r("finans/gayrimenkul"); continue
        if d.get("financialCurrency") and d.get("currency") and d["financialCurrency"] != d["currency"]: r("raporlama para birimi farkli"); continue
        mc, fcf, gm, rg = d.get("marketCap"), d.get("freeCashflow"), d.get("grossMargins"), d.get("revenueGrowth")
        if not all(isinstance(x, (int, float)) for x in (mc, fcf, gm, rg)) or mc <= 0: r("eksik veri"); continue
        hacim = (d.get("averageDailyVolume3Month") or 0) * (d.get("currentPrice") or 0)
        if hacim < 5e6: r("gunluk islem < 5 milyon $"); continue
        if d.get("sector") in ("Energy", "Basic Materials", "Utilities") or d.get("industry") == "Marine Shipping": r("emtia/dongusel sektor"); continue
        if mc > 4e10: r("piyasa degeri > 40 milyar $"); continue
        if (d.get("operatingMargins") or -1) < 0: r("faaliyet zarari"); continue
        if rg > 1.5: r("buyume > %150 (tek seferlik/birlesme supheli)"); continue
        if fcf / mc > 0.25: r("FCF getirisi > %25 (veri supheli)"); continue
        if gm < 0.40: r("brut marj < %40"); continue
        if rg < 0.10: r("son ceyrek buyume < %10"); continue
        if fcf <= 0 or (d.get("operatingCashflow") or 0) <= 0: r("nakit akisi negatif"); continue
        d = dict(d)
        d["fcf_getiri"] = fcf / mc
        d["net_nakit"] = ((d.get("totalCash") or 0) - (d.get("totalDebt") or 0)) / mc
        d["karlilik"] = d.get("returnOnEquity") if isinstance(d.get("returnOnEquity"), (int, float)) else d.get("operatingMargins")
        d["hacim"] = hacim
        U.append(d)
    return U, ele

def puanla(U):
    al = lambda a: [d.get(a) for d in U]
    for d in U:
        p = (0.30 * yuzdelik(al("fcf_getiri"), d["fcf_getiri"]) +
             0.20 * yuzdelik(al("revenueGrowth"), d["revenueGrowth"]) +
             0.15 * yuzdelik(al("grossMargins"), d["grossMargins"]) +
             0.15 * yuzdelik(al("karlilik"), d["karlilik"]) +
             0.10 * yuzdelik(al("net_nakit"), d["net_nakit"]) +
             0.10 * yuzdelik(al("marketCap"), d["marketCap"], buyuk_iyi=False))
        if (d.get("heldPercentInsiders") or 0) >= 0.05: p += 0.03
        d["puan"] = round(100 * p, 1)
    return sorted(U, key=lambda d: -d["puan"])

def satir(d):
    f = lambda x, k=100, n=0: ("%.*f" % (n, x * k)) if isinstance(x, (int, float)) else "-"
    return "%-6s %-28s %-24s mcap %6s mn$ | FCF get %s%% | buyume %s%% | brut %s%% | faal %s%% | ROE %s%% | net nakit %s%% | iceriden %s%% | F/K ileri %s | EV/S %s | analist %s | puan %.1f" % (
        d["sembol"], (d.get("shortName") or "")[:28], (d.get("industry") or "")[:24], f(d["marketCap"], 1e-6),
        f(d["fcf_getiri"], 100, 1), f(d.get("revenueGrowth")), f(d.get("grossMargins")), f(d.get("operatingMargins")),
        f(d.get("returnOnEquity")), f(d["net_nakit"]), f(d.get("heldPercentInsiders")), f(d.get("forwardPE"), 1, 1),
        f(d.get("enterpriseToRevenue"), 1, 1), d.get("numberOfAnalystOpinions") or "-", d["puan"])

if __name__ == "__main__":
    K = json.load(open(sys.argv[1]))
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    U, ele = hazirla(K)
    print("zaman", K.get("zaman"), "| ABD ekrandan gelen", len(K["abd"]), "| elemeden gecen", len(U), "| elenenler", ele)
    S = puanla(U)
    for d in S[:n]:
        print(satir(d))
