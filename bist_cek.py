#!/usr/bin/env python3
# BIST günlük veri çekici — Yatırım Ajanı için
# Yahoo Finance (.IS) üzerinden 14 hissenin günlük OHLCV verisini,
# motor.py'nin okuduğu veri.txt biçiminde yazar.
#
# Kurulum : pip install yfinance
# Kullanım: python3 bist_cek.py /yol/bist-veri.txt
#
# Notlar:
# - auto_adjust=False: ham fiyat (Twelve Data ile aynı mantık). Bölünme/bedelsiz
#   sıçramalarını motor zaten "fiyat duzeltmesi suphesi" ile yakalayıp atlıyor.
# - Her çalıştırmada ~4 aylık geçmiş yazılır; motor tarihe göre birleştirdiği için
#   tekrar eden günler sorun değil, yeni eklenen hisseler de yeterli geçmişle başlar.
# - '#' ile başlayan satır yalnızca blok başlığıdır (#BIST_KOD); başka yorum satırı yok,
#   çünkü motor her '#' satırını yeni varlık sayar.
import sys
import datetime
import yfinance as yf

KODLAR = ("THYAO ASELS GARAN AKBNK ISCTR YKBNK TUPRS EREGL "
          "PGSUS SASA KRDMD EKGYO ASTOR KONTR").split()


def sayi(x):
    return repr(round(float(x), 4))


def main():
    cikti = sys.argv[1] if len(sys.argv) > 1 else "bist-veri.txt"
    bloklar, hatalar = [], []
    for kod in KODLAR:
        try:
            df = yf.Ticker(kod + ".IS").history(
                period="4mo", interval="1d", auto_adjust=False, actions=False)
        except Exception:
            hatalar.append(kod)
            continue
        if df is None or df.empty:
            hatalar.append(kod)
            continue
        satirlar = ["#BIST_" + kod, "datetime;open;high;low;close;volume"]
        for ts, r in df.iloc[::-1].iterrows():  # en yeni gün üstte
            if r["Close"] != r["Close"]:  # NaN kapanışlı satırı atla
                continue
            hacim = int(r["Volume"]) if r["Volume"] == r["Volume"] else 0
            satirlar.append(";".join([
                ts.strftime("%Y-%m-%d"),
                sayi(r["Open"]), sayi(r["High"]), sayi(r["Low"]), sayi(r["Close"]),
                str(hacim)]))
        if len(satirlar) > 2:
            bloklar.append("\n".join(satirlar))
        else:
            hatalar.append(kod)

    damga = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Bu iki üst satır motor tarafından yok sayılır (ilk '#' başlığından önce geliyor).
    ust = ["olusturma;" + damga, "hata;" + ",".join(hatalar)]
    with open(cikti, "w") as f:
        f.write("\n".join(ust + bloklar) + "\n")
    print("Yazildi:", cikti, "| hisse:", len(bloklar), "| hata:", ",".join(hatalar) or "-")
    sys.exit(1 if not bloklar else 0)


if __name__ == "__main__":
    main()
