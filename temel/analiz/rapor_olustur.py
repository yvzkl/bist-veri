# Kayit JSON'undan okunur Turkce rapor (Drive Raporlar icin duz metin). Kullanim: python3 rapor_olustur.py <kayit.json> <sha256> <cikti.txt>
import json, sys

def yuzde(x, n=0):
    if x is None:
        return "-"
    t = ("%." + str(n) + "f") % (100 * abs(x))
    return ("−" if x < 0 else "") + "%" + t.replace(".", ",")

ETIKET = {
 "finans/gayrimenkul": "finans/gayrimenkul", "emtia/dongusel sektor": "emtia/döngüsel sektör (enerji, maden, kamu hizmeti, denizcilik)",
 "FCF getirisi > %25 (veri supheli)": "FCF getirisi %25'in üstünde (veri şüpheli)", "son ceyrek buyume < %10": "son çeyrek büyümesi %10'un altında",
 "faaliyet zarari": "faaliyet zararı", "buyume > %150 (tek seferlik/birlesme supheli)": "büyüme %150'nin üstünde (tek seferlik ya da birleşme şüphesi)",
 "raporlama para birimi farkli": "raporlama para birimi farklı", "gunluk islem < 5 milyon $": "günlük işlem 5 milyon $'ın altında",
 "eksik veri": "eksik veri", "piyasa degeri > 40 milyar $": "piyasa değeri 40 milyar $'ın üstünde",
 "piyasa degeri <= 20 milyar $": "piyasa değeri ≤20 milyar $", "gelir bilesik buyume (3 yil; yoksa 2) >= %15": "gelir bileşik büyümesi (3 yıl; yoksa 2) ≥%15",
 "FCF - SBC (son 4 ceyrek) > 0": "FCF − hisse bazlı ödeme (son 4 çeyrek) > 0",
 "FCF - SBC getirisi <= %15 (ustu: veri supheli, ornegin musteri fonu nakit akisina karisiyor)": "FCF − SBC getirisi ≤%15 (üstü veri şüphesi: ör. müşteri fonu nakit akışına karışıyor)",
 "hisse sayisi artisi (3 yil) <= %20": "hisse sayısı artışı (3 yıl) ≤%20",
 "analist gelecek yil gelir buyumesi >= %10 (tahmin yoksa gecer)": "analistlerin gelecek yıl gelir büyümesi beklentisi ≥%10 (tahmin yoksa geçer)",
 "fcf_sbc_getiri": "FCF − SBC getirisi", "cagr": "gelir bileşik büyümesi", "tahmin_gelecek_yil": "gelecek yıl analist büyümesi",
 "brut_son": "brüt marj", "faal_marj_ttm": "faaliyet marjı", "mcap": "küçüklük (düşük piyasa değeri)"}
e = lambda k: ETIKET.get(k, k)

def sayi(x, n=2):
    s = ("{:,.%df}" % n).format(x)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def main(yol, ozet, cikti):
    R = json.load(open(yol, encoding="utf-8"))
    h = R["huni"]
    L = []
    L += ["UZUN VADELİ ADAY KAYDI — %s" % R["kayit_id"], "",
          "Bu kayıt, Nvidia benzeri potansiyel taşıyan şirketleri seçme yeteneğimin ileriye dönük testidir. Fiyatlar 20.11.2026 Cuma normal seans kapanışıdır; kayıt ABD seansı kapandıktan sonra (İstanbul 21.11.2026 00:30) yapıldı ve değiştirilmez. Sonucu benim sözüm değil, 6, 12, 24 ve 36 ay sonraki getiriler gösterecek. Yatırım tavsiyesi değildir.", "",
          "Değişmezlik: kayıt dosyası uzun-vade-kayit-%s.json (Drive › Tahmin defteri ve GitHub yvzkl/bist-veri ana dalı, temel/kayit/). SHA-256: %s" % (R["kayit_id"], ozet), "",
          "1) YÖNTEM",
          "• Taban: %s — %s hisse." % (h["taban_tanimi"], sayi(h["abd_taban"], 0)),
          "• Ekran: %s → %d hisse (C evreni)." % (h["ekran_tanimi"], h["ekran"]),
          "• İlk eleme → %d hisse. Elenenler: %s." % (h["ilk_eleme_sonrasi"], ", ".join("%s %d" % (e(k), v) for k, v in h["ilk_eleme_nedenleri"].items())),
          "• Derin veri (4 yıllık tablolar, hisse bazlı ödeme, hisse sayısı, analist tahmini) ve B kapıları → %d hisse. Kapılar: %s." % (h["b_kapilarindan_gecen"], "; ".join(e(k) for k in h["b_kapilari"])),
          "• B puanı (yüzdelik): " + ", ".join("%s %%%d" % (e(k), round(100 * v)) for k, v in h["b_agirliklari"].items()) + ". İlk 20 → B sepeti.",
          "• A sepeti: 128 hisse içinden benim nitel seçimim. Ölçütler: " + "; ".join(R["A_secim_olcutleri"]) + ".", "",
          "2) A SEPETİ — CLAUDE'UN SEÇİMİ (10)",
          "Sembol | Şirket | Tema | Kayıt fiyatı $ | Piyasa değeri mlr $ | Gelir büyümesi (3 yıl, yıllık) | Brüt marj | FCF−SBC getirisi | Gelecek yıl analist büyümesi | EV/Satış"]
    for a in R["A_detay"]:
        o = a["olcutler"]
        L.append("%s | %s | %s | %s | %s | %s | %s | %s | %s | %s" % (a["sembol"], a["ad"], a["tema"], sayi(a["kayit_kapanis"]), sayi(o["piyasa_degeri_mn"] / 1000, 1),
                 yuzde(o["gelir_bilesik_buyume"]) + ("" if o["gelir_buyume_yil"] == 3 else " (%d yıl)" % o["gelir_buyume_yil"]), yuzde(o["brut_marj"]), yuzde(o["fcf_eksi_sbc_getirisi"], 1), yuzde(o["analist_gelecek_yil_buyume"]),
                 "-" if o["ev_satis_ttm"] is None else sayi(o["ev_satis_ttm"], 1)))
    L.append("")
    for a in R["A_detay"]:
        L += ["%s — %s" % (a["sembol"], a["ad"]),
              "Tez: " + a["tez"],
              "Riskler: " + a["riskler"],
              "Ölüm kriterleri (biri gerçekleşirse tez çökmüş sayılır): " + "; ".join(a["olum_kriterleri"]) + ".",
              "Kaynak: " + " , ".join(a["kaynaklar"]), ""]
    L += ["3) B SEPETİ — SİSTEMATİK (mekanik, yargı yok)"]
    L.append(", ".join("%s (%s; %s $)" % (b["sembol"], sayi(b["puan"], 1), sayi(b["kayit_kapanis"])) for b in R["B_detay"]))
    ortak = sorted(set(R["sepetler"]["A_claude"]) & set(R["sepetler"]["B_sistematik"]))
    L += ["A ile ortak: " + ", ".join(ortak) + ". A'da olup B'de olmayanlar B kapılarına takıldı (hisse sayısı artışı, FCF−SBC ya da büyüme kapısı); bunları gerekçemle bilerek aldım.", "",
          "4) KIYAS VE HİPOTEZLER",
          "Kıyaslar: " + ", ".join("%s %s $" % (k, sayi(R["fiyatlar"][k]["kapanis"])) for k in R["kiyas"]) + "; ayrıca C evreni (ekrandan geçen %d hissenin eşit ağırlıklı ortalaması)." % len(R["sepetler"]["C_ekran_evreni"])]
    for x in R["hipotezler"]:
        L.append("%s%s: %s" % (x["id"], " (ana)" if x.get("ana") else "", x["metin"]))
    d = R["degerlendirme"]
    L += ["", "5) DEĞERLENDİRME",
          "• " + d["yontem"], "• " + d["kote_olmayan_hisse"],
          "• Ara kontroller: %s. Nihai hüküm: %s. %s" % (", ".join(d["ara_kontroller"]), d["nihai"], d["ara_kontrol_kurali"]),
          "• " + d["izleme"], "",
          "6) PİYASA BAĞLAMI", R["piyasa_baglami"], "",
          "7) DÜRÜST NOTLAR"] + ["• " + x for x in R["durust_notlar"]] + ["", "8) BIST NOTU", R["bist_notu"], "",
          "9) TEKNİK İZ",
          "• Fiyat: " + R["fiyat_notu"],
          "• Veri: " + "; ".join("%s: %s" % (k, v) for k, v in R["veri_kaynagi"].items()), ""]
    open(cikti, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("rapor", cikti, len("\n".join(L)), "karakter")

if __name__ == "__main__":
    main(*sys.argv[1:4])
