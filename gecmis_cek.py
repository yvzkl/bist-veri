#!/usr/bin/env python3
# Yatırım Ajanı — geçmiş veri çekici (eğitim için)
# bist_cek.py'deki havuzun (BIST 100 + 30 ABD + 15 kripto) 2015'ten bugüne günlük verisini Yahoo'dan çeker.
# Fiyatlar bölünme ve temettüye göre düzeltilmiştir (auto_adjust=True); yalnızca kapanmış günler yazılır.
# Çıktı motor.py'nin okuduğu biçimdedir, gzip ile sıkıştırılır: gecmis/gecmis-veri.txt.gz
# Kullanım: python3 gecmis_cek.py [cikti.txt.gz] [baslangic=2015-01-01]
import sys
import gzip
import time
import datetime
import yfinance as yf
from bist_cek import BIST, US, KR, kesimler, gunluk, sayi

BAS = "2015-01-01"


def indir(semboller):
    out = {}
    for b in range(0, len(semboller), 40):
        parti = semboller[b:b + 40]
        df = None
        for deneme in range(3):
            try:
                df = yf.download(parti, start=BAS, interval="1d", group_by="ticker", auto_adjust=True,
                                 actions=False, threads=True, progress=False)
                break
            except Exception as e:
                print("indirme hatasi (deneme %d): %s" % (deneme + 1, e))
                time.sleep(30 * (deneme + 1))
        if df is not None and not df.empty:
            for s in parti:
                try:
                    out[s] = df[s]
                except KeyError:
                    pass
        time.sleep(3)
    return out


def main():
    global BAS
    cikti = "gecmis/gecmis-veri.txt.gz"
    for a in sys.argv[1:]:
        if a.startswith("baslangic="):
            BAS = a.split("=", 1)[1]
        else:
            cikti = a
    simdi = datetime.datetime.now(datetime.timezone.utc)
    K = {m: d.isoformat() for m, d in kesimler(simdi).items()}
    istek = [("BIST", "BIST_" + k, [k + ".IS"]) for k in BIST] + [("US", "US_" + k, [k]) for k in US] + \
            [("KR", "KR_" + a, L) for a, L in KR]
    GD = indir(sorted({s for _, _, L in istek for s in L}))
    satirlar, hatalar, ozet = [], [], []
    for mk, anahtar, L in istek:
        G = {}
        for s in L:
            G = {d: b for d, b in gunluk(GD.get(s)).items() if d <= K[mk]}
            if G:
                break
        if not G:
            hatalar.append(anahtar)
            continue
        gunler = sorted(G)
        ozet.append("%s:%s" % (anahtar, gunler[0]))
        satirlar.append("#" + anahtar)
        satirlar.append("datetime;open;high;low;close;volume")
        for d in gunler:
            o, h, l, c, v = G[d]
            satirlar.append(";".join([d, sayi(o), sayi(h), sayi(l), sayi(c), str(v)]))
    print("varlik: %d/%d | hata: %s" % (len(ozet), len(istek), ",".join(hatalar) or "-"))
    if len(ozet) < 0.7 * len(istek):
        print("YETERSIZ VERI: dosya yazilmadi")
        sys.exit(1)
    ust = ["olusturma;" + simdi.strftime("%Y-%m-%d %H:%M UTC"), "baslangic;" + BAS, "hata;" + ",".join(hatalar),
           "ilk_gun;" + ",".join(ozet)]
    with gzip.open(cikti, "wt") as f:
        f.write("\n".join(ust + satirlar) + "\n")
    print("Yazildi:", cikti)


if __name__ == "__main__":
    main()
