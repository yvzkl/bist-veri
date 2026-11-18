#!/usr/bin/env python3
# Piyasa günlük veri çekici v3 — Yatırım Ajanı için
# Havuz: BIST 100 (1 Ekim–31 Aralık 2026 dönemi) + 30 ABD hissesi + 15 kripto.
# Kaynak: Yahoo Finance (yfinance), günlük OHLCV; motor.py'nin okuduğu veri.txt biçiminde yazar.
#
# Yalnızca KAPANMIŞ günlerin çubukları yazılır (yarım gün çubuğu dosyaya hiç girmez):
#   BIST  : İstanbul saatiyle 18:30'dan sonra o gün kapanmış sayılır
#   ABD   : New York saatiyle 16:30'dan sonra
#   Kripto: UTC günü bitmiş olmalı (bugünün UTC çubuğu yazılmaz)
# BIST'te Yahoo'nun vermediği kapanmış gün, o günün saatlik çubuklarından kurulur ve "doldurulan;"
# satırında listelenir. Saatlik çubuklar kapanış seansını içermediği için bu kapanışlar kesin değildir;
# ajan sabah çalışırken son günü Google Finance ile karşılaştırıp düzeltir (gf_kontrol.py).
#
# Kullanım: python3 bist_cek.py /yol/bist-veri.txt   (pip install yfinance)
# '#' ile başlayan satır yalnızca blok başlığıdır (#BIST_KOD, #US_KOD, #KR_BTC-USD); motor her '#'
# satırını yeni varlık sayar, bu yüzden dosyaya başka yorum satırı yazılmaz.
# BIST 100 listesi her çeyrek değişir: bir sonraki dönem 1 Ocak 2027'de başlar, listeyi o zaman güncelle.
import sys
import time
import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

BIST = ("AEFES AGHOL AHGAZ AKBNK AKCNS AKFYE AKSA AKSEN ALARK ALBRK ALTNY ANHYT ANSGR ARCLK ASELS "
        "ASTOR AYGAZ BERA BIMAS BINHO BRSAN BRYAT BTCIM CANTE CCOLA CIMSA CVKMD CWENE DOAS DOHOL "
        "ECILC ECZYT EGEEN EGGUB EKGYO ENERY ENJSA ENKAI ENTRA EREGL EUREN FENER FROTO GARAN GLRMK "
        "GLYHO GRSEL GUBRF GWIND HALKB HEKTS ISCTR ISDMR ISMEN KARSN KATMR KCAER KCHOL KORDS KRDMD "
        "LMKDC MAVI MGROS MPARK OBAMS ODAS OTKAR OYAKC PAHOL PETKM PGSUS RGYAS RYSAS SAHOL SASA "
        "SISE SNGYO SOKM TABGD TAVHL TCELL TCKRC THYAO TKFEN TOASO TRALT TRENJ TRGYO TRMET TSKB "
        "TTKOM TTRAK TUKAS TUPRS TURSG ULKER VAKBN VESTL YKBNK ZOREN").split()
US = ("NVDA TSLA AMD PLTR COIN MSTR SMCI META AMZN MU HOOD SOFI AVGO NFLX ARM "
      "MRVL CRWD SHOP UBER RBLX AFRM RIVN MARA IONQ RKLB APP SNOW NET DKNG UPST").split()
# Kripto: motor anahtarı -> Yahoo sembol adayları (ilk veri veren kullanılır)
KR = [("BTC-USD", ["BTC-USD"]), ("ETH-USD", ["ETH-USD"]), ("BNB-USD", ["BNB-USD"]),
      ("XRP-USD", ["XRP-USD"]), ("SOL-USD", ["SOL-USD"]), ("TRX-USD", ["TRX-USD"]),
      ("HYPE-USD", ["HYPE32196-USD", "HYPE-USD"]), ("ZEC-USD", ["ZEC-USD"]),
      ("XMR-USD", ["XMR-USD"]), ("DOGE-USD", ["DOGE-USD"]), ("LINK-USD", ["LINK-USD"]),
      ("ADA-USD", ["ADA-USD"]), ("XLM-USD", ["XLM-USD"]), ("AVAX-USD", ["AVAX-USD"]),
      ("SUI-USD", ["SUI20947-USD", "SUI-USD"])]

IST = ZoneInfo("Europe/Istanbul")
NY = ZoneInfo("America/New_York")
GUN = datetime.timedelta(days=1)
ASGARI_ORAN = 0.7   # beklenen varlıkların %70'inden azı gelirse eski dosyaya dokunma


def sayi(x):
    return repr(round(float(x), 6))


def bos(x):
    return x is None or x != x  # None ya da NaN


def kesimler(simdi_utc):
    """Her piyasa için dosyaya yazılabilecek en yeni (kapanmış) gün."""
    i = simdi_utc.astimezone(IST)
    n = simdi_utc.astimezone(NY)
    return {
        "BIST": i.date() if i.time() >= datetime.time(18, 30) else i.date() - GUN,
        "US": n.date() if n.time() >= datetime.time(16, 30) else n.date() - GUN,
        "KR": simdi_utc.date() - GUN,
    }


def indir(semboller, **kw):
    """yfinance toplu indirme; 50'lik partiler, her parti 3 deneme. {sembol: DataFrame}"""
    out = {}
    for b in range(0, len(semboller), 50):
        parti = semboller[b:b + 50]
        df = None
        for deneme in range(3):
            try:
                df = yf.download(parti, group_by="ticker", auto_adjust=False, actions=False,
                                 threads=True, progress=False, **kw)
                break
            except Exception as e:  # ağ / hız sınırı
                print("indirme hatasi (deneme %d): %s" % (deneme + 1, e))
                time.sleep(20 * (deneme + 1))
        if df is None or df.empty:
            continue
        for s in parti:
            try:
                out[s] = df[s]
            except KeyError:
                pass
        time.sleep(2)
    return out


def gunluk(df):
    """Günlük çubuklar: {tarih: (o, h, l, c, v)}; kapanışı boş satırlar alınmaz."""
    out = {}
    if df is None:
        return out
    for ts, r in df.iterrows():
        o, h, l, c = r.get("Open"), r.get("High"), r.get("Low"), r.get("Close")
        if any(bos(x) for x in (o, h, l, c)) or c <= 0:
            continue
        v = r.get("Volume")
        out[ts.strftime("%Y-%m-%d")] = (o, h, l, c, 0 if bos(v) else int(v))
    return out


def saatlikten(df):
    """Saatlik çubuklardan gün gün çubuk kurar: {tarih: (o, h, l, c, v)}."""
    out = {}
    if df is None or df.empty:
        return out
    df = df[df["Close"] == df["Close"]]
    for d, g in df.groupby(df.index.strftime("%Y-%m-%d")):
        out[d] = (g["Open"].iloc[0], g["High"].max(), g["Low"].min(),
                  g["Close"].iloc[-1], int(g["Volume"].fillna(0).sum()))
    return out


def blok(anahtar, G, kesim):
    gunler = sorted((d for d in G if d <= kesim), reverse=True)  # en yeni gün üstte
    if not gunler:
        return None
    satirlar = ["#" + anahtar, "datetime;open;high;low;close;volume"]
    for d in gunler:
        o, h, l, c, v = G[d]
        satirlar.append(";".join([d, sayi(o), sayi(h), sayi(l), sayi(c), str(v)]))
    return "\n".join(satirlar)


def main():
    cikti = sys.argv[1] if len(sys.argv) > 1 else "bist-veri.txt"
    simdi = datetime.datetime.now(datetime.timezone.utc)
    K = {m: d.isoformat() for m, d in kesimler(simdi).items()}
    bloklar, hatalar, doldurulan = [], [], []

    # BIST: günlük + eksik kapanmış günler için saatlik
    yb = [k + ".IS" for k in BIST]
    GD = indir(yb, period="6mo", interval="1d")
    SD = indir(yb, period="5d", interval="1h")
    for kod in BIST:
        G = gunluk(GD.get(kod + ".IS"))
        for d, bar in saatlikten(SD.get(kod + ".IS")).items():
            if d <= K["BIST"] and d not in G:
                G[d] = bar
                doldurulan.append(kod + ":" + d)
        b = blok("BIST_" + kod, G, K["BIST"]) if G else None
        (bloklar.append(b) if b else hatalar.append("BIST_" + kod))

    # ABD
    GD = indir(US, period="6mo", interval="1d")
    for kod in US:
        G = gunluk(GD.get(kod))
        b = blok("US_" + kod, G, K["US"]) if G else None
        (bloklar.append(b) if b else hatalar.append("US_" + kod))

    # Kripto (sembol adayları)
    adaylar = sorted({s for _, L in KR for s in L})
    GD = indir(adaylar, period="6mo", interval="1d")
    for anahtar, L in KR:
        b = None
        for s in L:
            G = gunluk(GD.get(s))
            if G:
                b = blok("KR_" + anahtar, G, K["KR"])
                if b:
                    break
        (bloklar.append(b) if b else hatalar.append("KR_" + anahtar))

    beklenen = len(BIST) + len(US) + len(KR)
    print("Kesim gunleri:", K, "| varlik: %d/%d" % (len(bloklar), beklenen),
          "| hata:", ",".join(hatalar) or "-", "| saatlikten doldurulan:", ",".join(doldurulan) or "-")
    if len(bloklar) < ASGARI_ORAN * beklenen:
        print("YETERSIZ VERI: dosya yazilmadi, eski dosya korunuyor")
        sys.exit(1)

    damga = simdi.strftime("%Y-%m-%d %H:%M UTC")
    # Bu üst satırlar motor tarafından yok sayılır (ilk '#' başlığından önce geliyor).
    ust = ["olusturma;" + damga, "hata;" + ",".join(hatalar), "doldurulan;" + ",".join(doldurulan),
           "kesim;" + ",".join("%s=%s" % (m, K[m]) for m in ("BIST", "US", "KR"))]
    with open(cikti, "w") as f:
        f.write("\n".join(ust + bloklar) + "\n")
    print("Yazildi:", cikti)


if __name__ == "__main__":
    main()
