#!/usr/bin/env python3
# BIST günlük veri çekici v2 — Yatırım Ajanı için
# Yahoo Finance (.IS) üzerinden 14 hissenin günlük OHLCV verisini,
# motor.py'nin okuduğu veri.txt biçiminde yazar.
#
# v2: Yahoo, BIST'te kapanmış son günün günlük satırını bazen hiç vermiyor ya da
#     kapanışı boş veriyor. Böyle bir gün, aynı günün saatlik çubuklarından
#     (açılış = ilk açılış, yüksek/düşük = en yüksek/en düşük, kapanış = son kapanış,
#     hacim = toplam) kurulur ve dosyanın başındaki "doldurulan;" satırında listelenir.
#
# Kullanım: python3 bist_cek.py /yol/bist-veri.txt   (pip install yfinance)
# '#' ile başlayan satır yalnızca blok başlığıdır (#BIST_KOD); motor her '#' satırını
# yeni varlık sayar, bu yüzden başka yorum satırı yazılmaz.
import sys
import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

KODLAR = ("THYAO ASELS GARAN AKBNK ISCTR YKBNK TUPRS EREGL "
          "PGSUS SASA KRDMD EKGYO ASTOR KONTR").split()
IST = ZoneInfo("Europe/Istanbul")
KAPANIS_SONRASI = datetime.time(18, 30)  # BIST kapanış seansı 18:10'da biter


def sayi(x):
    return repr(round(float(x), 4))


def bos(x):
    return x != x  # NaN


def gunluk(df):
    """Günlük çubuklar: {tarih: (o, h, l, c, v)}; kapanışı boş satırlar alınmaz."""
    out = {}
    for ts, r in df.iterrows():
        if bos(r["Close"]):
            continue
        v = 0 if bos(r["Volume"]) else int(r["Volume"])
        out[ts.strftime("%Y-%m-%d")] = (r["Open"], r["High"], r["Low"], r["Close"], v)
    return out


def saatlikten(df):
    """Saatlik çubuklardan gün gün çubuk kurar: {tarih: (o, h, l, c, v)}."""
    df = df[df["Close"] == df["Close"]]
    out = {}
    for d, g in df.groupby(df.index.strftime("%Y-%m-%d")):
        out[d] = (g["Open"].iloc[0], g["High"].max(), g["Low"].min(),
                  g["Close"].iloc[-1], int(g["Volume"].fillna(0).sum()))
    return out


def main():
    cikti = sys.argv[1] if len(sys.argv) > 1 else "bist-veri.txt"
    simdi = datetime.datetime.now(IST)
    # Kapanmış son gün: kapanış sonrasıysa bugün, değilse dün ve öncesi
    kesim = simdi.date() if simdi.time() >= KAPANIS_SONRASI else simdi.date() - datetime.timedelta(days=1)
    kesim = kesim.isoformat()
    bloklar, hatalar, doldurulan = [], [], []
    for kod in KODLAR:
        t = yf.Ticker(kod + ".IS")
        try:
            G = gunluk(t.history(period="4mo", interval="1d", auto_adjust=False, actions=False))
        except Exception:
            G = {}
        try:
            S = saatlikten(t.history(period="5d", interval="1h", auto_adjust=False, actions=False))
        except Exception:
            S = {}
        for d, bar in S.items():
            if d <= kesim and d not in G:
                G[d] = bar
                doldurulan.append(kod + ":" + d)
        if not G:
            hatalar.append(kod)
            continue
        satirlar = ["#BIST_" + kod, "datetime;open;high;low;close;volume"]
        for d in sorted(G, reverse=True):  # en yeni gün üstte
            o, h, l, c, v = G[d]
            satirlar.append(";".join([d, sayi(o), sayi(h), sayi(l), sayi(c), str(v)]))
        bloklar.append("\n".join(satirlar))

    damga = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Bu üst satırlar motor tarafından yok sayılır (ilk '#' başlığından önce geliyor).
    ust = ["olusturma;" + damga, "hata;" + ",".join(hatalar), "doldurulan;" + ",".join(doldurulan)]
    with open(cikti, "w") as f:
        f.write("\n".join(ust + bloklar) + "\n")
    print("Yazildi:", cikti, "| hisse:", len(bloklar), "| hata:", ",".join(hatalar) or "-",
          "| saatlikten doldurulan:", ",".join(doldurulan) or "-")
    sys.exit(1 if not bloklar else 0)


if __name__ == "__main__":
    main()
