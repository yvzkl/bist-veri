# Uzun vadeli aday kaydi UV-2026-11-21: veri dosyalarindan + nitel tezlerden degismez kayit (JSON) ve okunur rapor (TXT) uretir.
# Kullanim: python3 kayit_olustur.py <cikti_klasoru>
import json, sys, os, collections
from derin_olc import hepsi
from sepet_b import sec, KAPILAR, AGIRLIK
from puanla import hazirla

KAYIT_ID = "UV-2026-11-21"
GUN = "2026-11-20"
KIYAS = ["IWM", "RSP", "SPY", "QQQ"]

A = [
 ("CRDO", "Yapay zekâ veri merkezi bağlantısı",
  "Yapay zekâ kümelerinde darboğaz hesaplamadan bağlantıya kayıyor. Credo aktif elektrik kablosu (AEC) kategorisini yaratan şirket; optik DSP ile ikinci büyüme motorunu kuruyor. FY2026 geliri üç katına çıktı (1,34 milyar $), FY2027 için %85+ büyüme rehberi var, düzeltilmiş brüt marj ~%68. Kasım satışıyla fiyat 52 haftalık zirvenin üçte birine indi; şirkete özgü kötü haber yok.",
  "Gelirin büyük kısmı birkaç hiper ölçekliden. Yapay zekâ yatırım döngüsü dönerse (Nvidia'daki yönetim krizi, veri merkezi politikası) ilk vurulanlardan olur. Broadcom, Marvell ve MaxLinear rekabeti. Hisse bazlı ödeme gelirin %15'i; hisse sayısı 3 yılda %28 arttı.",
  ["FY2028 bitmeden art arda 2 çeyrek yıllık gelir büyümesi %20'nin altında", "Düzeltilmiş brüt marj 2 çeyrek üst üste %60'ın altında", "En büyük müşteri kaybının açıklanması"],
  ["https://www.sec.gov/Archives/edgar/data/0001807794/000162828026059795/credoq12027ex-991.htm",
   "https://www.trefis.com/stock/crdo/articles/625288/why-did-credo-technology-stock-fall/2026-11-16"]),
 ("DOCN", "Yapay zekâ çıkarım (inference) bulutu",
  "Geliştiricilere ve yapay zekâ yerlisi şirketlere yönelik bulut. Büyüme beş çeyrektir hızlanıyor (Q3 2026: %40), yapay zekâ müşteri ARR'ı yıllık %288 artışla 376 milyon $'a çıktı, yönetim 2027 için %60+ büyüme bekliyor. Çıkarım talebi eğitimden daha geniş ve kalıcı olabilir: Nvidia'nın 'kürek satıcısı' mantığının bulut katmanı.",
  "GPU yatırımı serbest nakit akışını sıfırladı (Q3 FCF marjı ~%0) ve net borç var. Hiper ölçekliler ve neocloud'larla fiyat rekabeti. Talep yavaşlarsa kapasite atıl kalır.",
  ["2027 yıllık gelir büyümesi %35'in altında", "2028'de hâlâ negatif serbest nakit akışı ve artan net borç", "Yapay zekâ müşteri ARR'ında çeyreklik düşüş"],
  ["https://www.sec.gov/Archives/edgar/data/0001582961/000162828026069125/a2026-q3dopressrelease.htm"]),
 ("NVMI", "Yarı iletken ölçüm (metroloji)",
  "Her yeni üretim düğümü, HBM ve gelişmiş paketleme ölçüm ihtiyacını artırıyor; Nova bu alanda KLA'nın yanındaki birkaç oyuncudan biri. Q3 2026 geliri yıllık %28 artışla rekor (287,8 milyon $), GAAP faaliyet marjı %32. Fiyat 52 haftalık zirvenin yarısının altında.",
  "Yarı iletken ekipman döngüsü; dört müşteri gelirin en az %10'unu tek başına veriyor; İsrail merkezli (jeopolitik); Çin'e ihracat kısıtları.",
  ["2 çeyrek üst üste yıllık gelir düşüşü %15'ten fazla", "Brüt marjın %50'nin altına inmesi", "Gelişmiş paketlemede pazar payı kaybının açıklanması"],
  ["https://www.prnewswire.com/il/news-releases/nova-reports-record-third-quarter-2026-financial-results-302930609.html",
   "https://www.marketbeat.com/instant-alerts/transcript-nova-q3-earnings-call-highlights-2026-11-06/"]),
 ("RMBS", "Bellek arayüz çipleri ve patentler",
  "Yapay zekâ sunucularında bellek bant genişliği darboğazı büyüyor; Rambus DDR5 RCD, MRDIMM ve CXL arayüz çiplerinde güçlü, ayrıca patent geliri var. Q3 2026'da ürün geliri rekor (yıllık +%22), ~777 milyon $ nakit, borç yok denecek kadar az, hisse sayısı artmıyor.",
  "Montage ve Renesas rekabeti; bellek döngüsü; lisans gelirinde dalgalanma. On kat için çok büyük yeni bir pazar gerekir: daha çok kaliteli bileşik büyüyen profili.",
  ["Bir yıl boyunca ürün geliri büyümesi %5'in altında", "DDR5/MRDIMM'de pay kaybının açıklanması"],
  ["https://finviz.com/news/408070/rambus-reports-third-quarter-2026-financial-results"]),
 ("RDDT", "İnsan sohbeti ağı ve yapay zekâ veri lisansı",
  "İnternetin en büyük insan üretimi tartışma arşivi; yapay zekâ modelleri için benzersiz veri (Google ve OpenAI lisansları). Q3 2026'da gelir +%53, reklam geliri +%54, serbest nakit akışı marjı %40; kurucu (Steve Huffman) yönetimde. Sonuç sonrası %30 düşüş ve yapay zekâ satışıyla fiyat zirvenin üçte biri.",
  "Google'ın AI Overviews/AI Mode özellikleri arama trafiğini kesiyor; yönetim Q4'te günlük kullanıcıda düşük çift haneli düşüş bekliyor. Bu, tezin merkezine vuran gerçek bir risk. ABD günlük kullanıcısı yıllık %2 düştü.",
  ["Oturum açmış günlük kullanıcıda 2 çeyrek üst üste yıllık düşüş", "2027 içinde yıllık gelir büyümesinin %15'in altına inmesi"],
  ["https://www.trefis.com/stock/rddt/articles/622319/what-did-reddits-quarter-change-for-its-stock/2026-11-03",
   "https://stockstory.org/us/stocks/nyse/rddt/news/earnings/reddit-nyserddt-surprises-with-q3-2026-sales-but-stock-drops-126percent"]),
 ("GLBE", "Sınır ötesi e-ticaret altyapısı",
  "Markaların yurt dışına doğrudan satışını (vergi, gümrük, ödeme, iade) kayıtlı satıcı olarak üstlenen platform; Shopify ortaklığı; kurucular yönetimde. Q3 2026'da gelir +%42, düzeltilmiş FAVÖK marjı %20,3; net nakit ve 500 milyon $'lık geri alım programı.",
  "Organik büyüme soğuyor (GMV +%35, önceki çeyrek %44; çeyreklik GMV geriledi). Shopify'a bağımlılık; ABD gümrük/tarife politikası; kur.",
  ["2 çeyrek üst üste GMV büyümesi %20'nin altında", "Shopify ortaklığının sona ermesi ya da daralması"],
  ["https://www.sec.gov/Archives/edgar/data/0001835963/000117891326005272/exhibit_99-1.htm",
   "https://finviz.com/news/424750/global-e-beats-on-profit-and-raises-again-but-acquired-growth-masks-cooling-organic-momentum"]),
 ("HNGE", "Dijital kas-iskelet bakım platformu",
  "Yazılım ekonomisiyle çalışan sağlık hizmeti: Q3 2026'da gelir +%52, brüt marj %87, serbest nakit akışı marjı %48; 2026 geliri ~880 milyon $ (+%50). İşverenlerin sağlık maliyetini düşürüyor; migren ve sindirim (GI) bakımına genişliyor. Kurucu (Daniel Perez) CEO.",
  "İşveren bütçeleri; rekabet (Sword Health); 2027 için analist beklentisi %27'ye yavaşlama; hisse 52 haftada +%135, beklenti yüksek.",
  ["2027 yıllık gelir büyümesi %20'nin altında", "Serbest nakit akışı marjının %20'nin altına inmesi", "Büyük müşteri ya da sağlık planı kaybı"],
  ["https://www.sec.gov/Archives/edgar/data/0001673743/000162828026068872/hnge-q32026112xex991.htm",
   "https://www.fiercehealthcare.com/digital-health/hinge-health-posted-52-revenue-growth-q3-it-ramps-expansion-migraine-gi-care"]),
 ("TMDX", "Organ nakli platformu",
  "Organı vücut dışında çalışır hâlde tutan OCS cihazı ve kendi uçak filosuyla lojistik: nakil sürecini uçtan uca yeniden kuran, kurucunun (Waleed Hassanein) yönettiği neredeyse tekel. Q3 2026'da gelir +%41 (organik %35), 2026 rehberi 764–774 milyon $. Kalp ve akciğer yeni denemeleri, böbrekte 2027 ikinci yarı ilk insan çalışmasıyla pazar genişliyor. Piyasa değeri ~3 milyar $.",
  "Uçak filosu sermaye yoğun; FDA deneme sonuçları; donör sayısı sınırı; 2025'te açığa satıcı raporu; hisse sayısı 3 yılda %37 arttı.",
  ["Yıllık gelir büyümesinin %15'in altına inmesi", "ENHANCE Heart ya da DENOVO Lung denemesinde başarısızlık", "2 çeyrek üst üste OCS vaka hacminde yıllık düşüş"],
  ["https://www.sec.gov/Archives/edgar/data/0001756262/000119312526449729/tmdx-ex99_1.htm"]),
 ("ALNY", "RNAi ilaç platformu",
  "RNA girişimi (RNAi) platformunun öncüsü: Nvidia'nın CUDA'sı gibi tek teknoloji, çok pazar. Amvuttra ile ATTR kardiyomiyopati pazarında; boru hattı hipertansiyon, obezite ve nörolojiye uzanıyor (obezite ve HHT verileri Şubat 2027). İki rehber hayal kırıklığıyla hisse zirvesinden %70 düştü; değer ~4 kat satış.",
  "ATTR'de sert rekabet (Pfizer, BridgeBio, AstraZeneca/Ionis); 2027'den itibaren Medicare geri ödeme değişikliği; yeni hasta başlangıçları beklenenden yavaş; boru hattı gecikmeleri.",
  ["2027 TTR gelirinin 2026'nın altında kalması", "Zilebesiran ya da nucresiran Faz 3 başarısızlığı"],
  ["https://www.fiercepharma.com/pharma/alnylam-shares-tank-27-amvuttra-disappoints-attr-outlook-cut-2026",
   "https://www.trefis.com/articles/621578/what-just-happened-to-alnylam-stock/2026-10-30"]),
 ("KRYS", "Tekrar dozlanabilir gen tedavisi platformu",
  "HSV-1 vektörüyle cilde, göze ve akciğere tekrar uygulanabilen gen tedavisi. İlk ürün Vyjuvek kârlı (Q3 2026: 127,3 milyon $, +%30, brüt marj %94); 1,2 milyar $ nakit ve yatırım, 400 milyon $ geri alım; kurucular yönetimde. Platform yeni endikasyonlarda (kistik fibroz KB407, göz KB803) tutarsa çok katlanma potansiyeli var.",
  "Değerleme yüksek (~18 kat satış); boru hattı sonuçları 2027'ye kaydı; tek ürün.",
  ["KB407 ya da KB803'te başarısızlık", "Vyjuvek yıllık büyümesinin %10'un altına inmesi"],
  ["https://www.sec.gov/Archives/edgar/data/0001711279/000171127926000072/exhibit991-3q26pressrelease.htm",
   "https://finviz.com/news/413384/krystal-biotech-beats-on-vyjuvek-strength-and-adds-a-400-million-buyback-but-pipeline-timelines-slip-into-2027"]),
]

SECIM_OLCUTLERI = [
 "Platform ya da hendek: kopyalanması zor teknoloji, ağ etkisi ya da ekosistem; brüt marj tercihen %55+",
 "Seküler talep: yapay zekâ hesaplama/çıkarım, dijital sağlık, genetik ilaçlar, küresel e-ticaret",
 "Büyüme pisti: bugün %25+ büyüme ve gelecek yıl için %15+ beklenti",
 "Kendini finanse etme: pozitif serbest nakit akışı ya da gerekçeli yatırım dönemi",
 "Kurucu ya da ortak çıkarı tercih edilir",
 "Piyasa değeri 20 milyar $ ve altı (on kat için alan)",
 "Tema yoğunlaşması sınırı: yapay zekâ altyapısında en fazla dört şirket",
]

def yuvarla(x, n=4):
    return None if x is None else round(x, n)

def main(klasor):
    os.makedirs(klasor, exist_ok=True)
    K = json.load(open("temel-tarama.json")); D = json.load(open("temel-derin.json"))
    _, ele1 = hazirla(K)
    M, _ = hepsi()
    ilk20, sira, G, Kal = sec(M)
    F = D["fiyat"]
    C = sorted(d["sembol"] for d in K["abd"] if "hata" not in d)
    a_sem = [x[0] for x in A]
    assert all(s in M for s in a_sem), "A sepetindeki her hisse 128'lik listede olmali"
    assert all(F[s].get("tarih") == GUN for s in set(a_sem + ilk20 + C + KIYAS)), "kayit fiyat tarihi"
    def olcut(s):
        m = M[s]
        ev = m["mcap"] * (1 - m["net_nakit"])
        return {"piyasa_degeri_mn": round(m["mcap"] / 1e6), "gelir_ttm_mn": round((m["gelir_ttm"] or 0) / 1e6),
                "ev_satis_ttm": round(ev / m["gelir_ttm"], 1) if m["gelir_ttm"] else None,
                "gelir_bilesik_buyume": yuvarla(m["cagr"]), "gelir_buyume_yil": m["cagr_yil"],
                "brut_marj": yuvarla(m["brut_son"]), "faaliyet_marji_ttm": yuvarla(m["faal_marj_ttm"]),
                "fcf_eksi_sbc_getirisi": yuvarla(m["fcf_sbc_getiri"]), "sbc_gelir": yuvarla(m["sbc_gelir"]),
                "hisse_sayisi_artisi": yuvarla(m["seyrelme"]), "net_nakit_piyasa_degeri": yuvarla(m["net_nakit"]),
                "analist_bu_yil_buyume": yuvarla(m["tahmin_bu_yil"]), "analist_gelecek_yil_buyume": yuvarla(m["tahmin_gelecek_yil"]),
                "iceriden_sahiplik": yuvarla(m["info"].get("heldPercentInsiders")), "degisim_52h": yuvarla(m["info"].get("52WeekChange")),
                "zirve_52h": m["info"].get("fiftyTwoWeekHigh"), "dip_52h": m["info"].get("fiftyTwoWeekLow")}
    R = {
     "kayit_id": KAYIT_ID,
     "kayit_fiyati_tarihi": GUN,
     "olusturma": "2026-11-21 00:30 İstanbul (20.11.2026 21:30 UTC): BIST kapalı, ABD normal seansı kapanmış; kayıt fiyatı normal seans kapanışıdır, seans sonrası işlemler dahil değildir",
     "olusturan": "Claude (Opus 5.5), Yavuz'un Yatırım Ajanı oturumu",
     "amac": "Nvidia benzeri potansiyel taşıyan şirketleri seçme yeteneğinin ileriye dönük, önceden kayıtlı testi. Yatırım tavsiyesi değildir; pozisyon büyüklüğü önerilmez.",
     "fiyat_notu": "Fiyatlar 20.11.2026 Cuma resmi kapanışlarıdır (Yahoo, temettü düzeltmesiz 'kapanis' ve düzeltilmiş 'duz_kapanis'). Twelve Data ile çapraz denetim: CRDO 99,86 = 99,86; HNGE 105,72 = 105,72; TMDX 85,25 / 85,33 (%0,09 fark).",
     "piyasa_baglami": "Kayıt yapay zekâ ağırlıklı bir düzeltmenin ortasında yapıldı: 5 Kasım'da Nasdaq 100 2020'den beri en kötü gününü yaşadı; 12 Kasım'da Nvidia CEO'su Jensen Huang istifa etti; seçim sonrası veri merkezi politikası kaygıları ve yeni çip ihracat kısıtları; 2026 başından beri yazılım hisselerinde yapay zekâ kaynaklı sert satış; VIX 19.11'de 28,4; kayıt günü 20.11'de SPY −%3,6, QQQ −%5,7 (Yahoo kapanışları). Kıyas fonları aynı günden başladığı için göreli karşılaştırma adildir; mutlak getiriler bu başlangıçtan etkilenir.",
     "veri_kaynagi": {"temel_ve_fiyat": "Yahoo Finance, yfinance 1.8.x, GitHub Actions (yvzkl/bist-veri, temel-tarama dalı)",
                      "tarama_calismasi": "44816960014 (commit 6ae221b, 2026-11-20 21:04 UTC)",
                      "derin_calisma": "44818593795 (commit 092abdb)",
                      "son_ceyrek_bilgileri": "Şirket açıklamaları ve haber kaynakları; A_detay içinde bağlantılar"},
     "huni": {"abd_taban": 2425, "taban_tanimi": "ABD borsaları (NMS, NGM, NCM, NYQ, ASE), piyasa değeri 0,3–40 milyar $, fiyat ≥3 $, 3 aylık ortalama hacim ≥200 bin",
              "ekran": len(C), "ekran_tanimi": "Yıllık gelir büyümesi ≥%15, brüt marj ≥%40, kaldıraçlı serbest nakit akışı >0",
              "ilk_eleme_sonrasi": len(M), "ilk_eleme_nedenleri": ele1,
              "b_kapilarindan_gecen": len(G), "b_kapilari": [ad for ad, _ in KAPILAR],
              "b_agirliklari": {a: w for a, w, _ in AGIRLIK}, "b_kapisi_eleme_nedenleri": dict(collections.Counter(Kal.values()))},
     "sepetler": {"A_claude": a_sem, "B_sistematik": ilk20, "C_ekran_evreni": C},
     "kiyas": KIYAS,
     "A_secim_olcutleri": SECIM_OLCUTLERI,
     "A_detay": [{"sembol": s, "ad": M[s]["info"].get("longName") or M[s]["info"].get("shortName"), "tema": tema,
                  "kayit_kapanis": F[s]["kapanis"], "tez": tez, "riskler": risk, "olum_kriterleri": olum, "kaynaklar": kay,
                  "olcutler": olcut(s)} for s, tema, tez, risk, olum, kay in A],
     "B_detay": [{"sembol": s, "ad": M[s]["info"].get("shortName"), "puan": M[s]["puan_b"], "kayit_kapanis": F[s]["kapanis"],
                  "olcutler": olcut(s)} for s in ilk20],
     "hipotezler": [
      {"id": "H1", "ana": True, "metin": "36. ayda (20.11.2029 kapanışı) A sepetinin eşit ağırlıklı toplam getirisi IWM'in toplam getirisinden yüksek olur."},
      {"id": "H2", "metin": "36. ayda A sepeti B sepetini geçer (nitel yargının mekanik puanlamaya katkısı)."},
      {"id": "H3", "metin": "36. ayda B sepeti C evrenini geçer (puanlamanın ekranın kendisine katkısı)."},
      {"id": "H4", "metin": "36. ayda A sepetinde 3 kat (≥ +%200) yapan hisselerin oranı C evrenindeki orandan yüksek olur."}],
     "degerlendirme": {
      "yontem": "Eşit ağırlık, 20.11.2026 kapanışında al-tut, yeniden dengeleme yok. Getiri: aynı temettü düzeltmeli seride değerlendirme günü / kayıt günü − 1. Ölüm kriterleri tezin doğruluğunu ölçer, getiri hesabını değiştirmez (sonradan bilgiyle satış yok).",
      "kote_olmayan_hisse": "Satın alma ya da borsadan çıkma: son işlem fiyatı (ya da nakit satın alma bedeli) ile kapanır ve sonrası %0 sayılır; iflas: −%100.",
      "ara_kontroller": ["2027-05-20", "2027-11-20", "2028-11-20"],
      "nihai": "2029-11-20",
      "ara_kontrol_kurali": "Ara kontrollerde hüküm verilmez; yalnızca durum ve tetiklenen ölüm kriterleri raporlanır.",
      "izleme": "GitHub yvzkl/bist-veri ana dalında 'Temel tarama' iş akışı her ayın 20'sinde sonuc/uzun-vade-izleme-UV-2026-11-21.json dosyasını günceller."},
     "durust_notlar": [
      "Tek sepet tek gözlemdir: 10 hisse ve 3 yılda şans payı büyüktür. A'nın IWM'i geçmesi tek başına beceri kanıtı sayılmaz, geçememesi de becerisizlik kanıtı sayılmaz. Anlamlı kanıt için her 6 ayda yeni bir kohort kaydı gerekir.",
      "A sepetinin dört şirketi yapay zekâ altyapı döngüsüne doğrudan bağlı, Reddit dolaylı olarak bağlı; döngü dönerse birlikte düşerler. Bu bilinçli bir risktir.",
      "Temel veriler denetlenmiş tablolar değil, Yahoo özetleridir; bazı alanlar hatalı olabilir (ör. Wise'ta müşteri fonları serbest nakit akışını şişiriyor: kapıyla dışlandı). Son çeyrek bilgileri web kaynaklarından okundu; yönetimlerle görüşme ya da saha araştırması yok.",
      "Haziran 2026 sonrasını eğitimimden değil, yalnızca web aramasından biliyorum.",
      "Çıkar çatışması: Claude bir Anthropic modelidir ve 2026 yazılım satışının tetikleyicilerinden biri Anthropic ürünleriydi. Klasik koltuk bazlı yazılım şirketlerine karşı önyargım olabilir. B sepeti bu şirketleri (MNDY, FRSH, APPF, DUOL) mekanik olarak içeriyor, A içermiyor; A ile B farkı bu önyargıyı da sınar.",
      "BIST bu kayda girmedi: Yahoo'nun BIST temel verisi bu iş için güvenilir değil ve BIST 100'de bu profile uyan şirket neredeyse yok (bkz. BIST notu)."],
     "bist_notu": "BIST 100 için Yahoo temel verisi bu iş için güvenilir değil: 13 şirkette raporlama para birimi boş; THY ve Enka dolar, TAV avro ile raporluyor; enflasyon muhasebesi (TMS 29) dönemler arası büyüme oranlarını karıştırıyor; bazı oranlar karşılaştırılamaz (ör. Alarko Holding gelir büyümesi +%733). BIST 100'de yüksek marjlı teknoloji platformu profiline en yakın şirket ASELSAN (savunma elektroniği) ve 52 haftada zaten +%86. Doğru yol, KAP mali tablolarıyla tüm BIST'i taramak; bu ayrı bir iştir.",
     "fiyatlar": {s: {"kapanis": F[s]["kapanis"], "duz_kapanis": F[s]["duz_kapanis"]} for s in sorted(set(a_sem + ilk20 + C + KIYAS))},
    }
    yol = os.path.join(klasor, "uzun-vade-kayit-%s.json" % KAYIT_ID)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print("yazildi", yol, os.path.getsize(yol), "bayt | A", len(a_sem), "| B", len(ilk20), "| C", len(C), "| fiyat", len(R["fiyatlar"]))
    print("A-B ortak:", sorted(set(a_sem) & set(ilk20)))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kayit")
