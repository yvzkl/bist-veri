# B sepeti (sistematik, mekanik): derin olcutlerle kapilar + yuzdelik puan, ilk 20. Kullanim: python3 sepet_b.py
from derin_olc import hepsi
from puanla import yuzdelik

KAPILAR = (
    ("piyasa degeri <= 20 milyar $", lambda m: m["mcap"] <= 2e10),
    ("gelir bilesik buyume (3 yil; yoksa 2) >= %15", lambda m: (m["cagr"] or -1) >= 0.15),
    ("FCF - SBC (son 4 ceyrek) > 0", lambda m: (m["fcf_sbc_getiri"] or -1) > 0),
    ("FCF - SBC getirisi <= %15 (ustu: veri supheli, ornegin musteri fonu nakit akisina karisiyor)", lambda m: (m["fcf_sbc_getiri"] or 0) <= 0.15),
    ("hisse sayisi artisi (3 yil) <= %20", lambda m: m["seyrelme"] is None or m["seyrelme"] <= 0.20),
    ("analist gelecek yil gelir buyumesi >= %10 (tahmin yoksa gecer)", lambda m: m["tahmin_gelecek_yil"] is None or m["tahmin_gelecek_yil"] >= 0.10),
)
AGIRLIK = (("fcf_sbc_getiri", 0.30, True), ("cagr", 0.20, True), ("tahmin_gelecek_yil", 0.15, True),
           ("brut_son", 0.15, True), ("faal_marj_ttm", 0.10, True), ("mcap", 0.10, False))

def sec(M, n=20):
    gecen, kalan = {}, {}
    for s, m in M.items():
        neden = next((ad for ad, f in KAPILAR if not f(m)), None)
        (kalan if neden else gecen)[s] = neden or m
    for s, m in gecen.items():
        m["puan_b"] = round(100 * sum(w * yuzdelik([x[a] for x in gecen.values()], m[a], iyi) for a, w, iyi in AGIRLIK), 1)
    sira = sorted(gecen, key=lambda s: -gecen[s]["puan_b"])
    return sira[:n], sira, gecen, kalan

if __name__ == "__main__":
    import collections
    M, D = hepsi()
    ilk, sira, G, K = sec(M)
    print("kapilardan gecen", len(G), "/", len(M), "| elenme:", dict(collections.Counter(K.values())))
    for i, s in enumerate(sira, 1):
        m = G[s]
        print("%2d %-5s puan %5.1f | FCF-SBC %5.1f%% | CAGR %3.0f%% | tahmin+1 %3s%% | brut %2.0f%% | faal %3.0f%% | mcap %5.1f mlr$ | %s" % (
            i, s, m["puan_b"], 100 * m["fcf_sbc_getiri"], 100 * m["cagr"], "-" if m["tahmin_gelecek_yil"] is None else "%.0f" % (100 * m["tahmin_gelecek_yil"]),
            100 * (m["brut_son"] or 0), 100 * (m["faal_marj_ttm"] or 0), m["mcap"] / 1e9, (m["info"].get("industry") or "")[:30]))
