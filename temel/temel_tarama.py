# Yatirim Ajani - uzun vadeli aday taramasi (temel veriler Yahoo'dan, yfinance ile). 21.11.2026.
# Kullanim: python3 temel/temel_tarama.py <kesif|tarama|derin|izle|kohort|kohort-test> <cikti_klasoru>
import sys, os, json, time, traceback, collections, glob, datetime as dt
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

def tarama(klasor, hedef="sonuc/temel-tarama.json", bist_dahil=True):
    L = ["yfinance " + getattr(yf, "__version__", "?"), "zaman " + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")]
    ev = evren_abd(L)
    L.append("ABD evreni: %d hisse" % len(ev))
    sys.path.insert(0, os.getcwd())
    bist = []
    if bist_dahil:
        try:
            import bist_cek
            bist = [k + ".IS" for k in bist_cek.BIST]
        except Exception as e:
            L.append("BIST listesi alinamadi: %r" % e)
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
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as f:
        json.dump(K, f, ensure_ascii=False)
    yaz(klasor, "tarama.txt", "\n".join(L) + "\n")
    print("\n".join(L))
    return K

# --- derin: secilen hisselerin yillik/ceyreklik tablolari + kayit gunu kapanis fiyatlari ---
KAYIT_GUNU = "2026-11-20"
KIYAS = ["IWM", "RSP", "SPY", "QQQ"]
SATIR_GELIR = ("Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Research And Development",
               "Diluted Average Shares", "Basic Average Shares")
SATIR_NAKIT = ("Free Cash Flow", "Operating Cash Flow", "Capital Expenditure", "Stock Based Compensation",
               "Repurchase Of Capital Stock")

def _sayi(v):
    try:
        v = float(v)
    except Exception:
        return None
    return None if v != v else v

def _tablo(df, satirlar):
    out = {}
    if df is None or getattr(df, "empty", True):
        return out
    for r in satirlar:
        if r in df.index:
            out[r] = {str(k.date() if hasattr(k, "date") else k): _sayi(v) for k, v in df.loc[r].items()}
    return out

def _df(df):
    if df is None or getattr(df, "empty", True):
        return None
    return json.loads(df.to_json(orient="split", date_format="iso", default_handler=str))

def derin_bir(s):
    t = yf.Ticker(s)
    d = {"sembol": s}
    isler = (("yillik_gelir", lambda: _tablo(t.income_stmt, SATIR_GELIR)),
             ("yillik_nakit", lambda: _tablo(t.cashflow, SATIR_NAKIT)),
             ("ceyrek_gelir", lambda: _tablo(t.quarterly_income_stmt, SATIR_GELIR)),
             ("ceyrek_nakit", lambda: _tablo(t.quarterly_cashflow, SATIR_NAKIT)),
             ("gelir_tahmini", lambda: _df(t.revenue_estimate)),
             ("iceriden_alim", lambda: _df(t.insider_purchases)))
    for ad, fn in isler:
        for k in range(2):
            try:
                d[ad] = fn()
                d.pop(ad + "_hata", None)
                break
            except Exception as e:
                d[ad + "_hata"] = repr(e)[:200]
                time.sleep(2 + 3 * k)
    return d

def _indir(semboller, bas, son=None):
    return yf.download(semboller, start=bas, end=son, auto_adjust=False, progress=False, threads=True, group_by="column")

def kayit_fiyatlari(semboller, gun):
    g = dt.date.fromisoformat(gun)
    bas, son = (g - dt.timedelta(days=6)).isoformat(), (g + dt.timedelta(days=1)).isoformat()
    def oku(df, s):
        c, a = df["Close"], df["Adj Close"]
        if hasattr(c, "columns"):
            c = c[s] if s in c.columns else c.iloc[:, 0]
            a = a[s] if s in a.columns else a.iloc[:, 0]
        c = c.dropna(); a = a.dropna()
        c = c[c.index.date <= g]; a = a[a.index.date <= g]
        return {"tarih": str(c.index[-1].date()), "kapanis": round(float(c.iloc[-1]), 4), "duz_kapanis": round(float(a.iloc[-1]), 4)}
    df = _indir(semboller, bas, son)
    F = {}
    for s in semboller:
        try:
            F[s] = oku(df, s)
        except Exception as e:
            F[s] = {"hata": repr(e)[:120]}
    for s in [s for s in semboller if F[s].get("tarih") != gun]:
        for k in range(2):  # toplu indirmede gecici hata: tek tek, iplik olmadan yeniden dene
            try:
                F[s] = oku(yf.download(s, start=bas, end=son, auto_adjust=False, progress=False, threads=False), s)
            except Exception as e:
                F[s] = {"hata": repr(e)[:120]}
            if F[s].get("tarih") == gun:
                break
            time.sleep(2 + 2 * k)
    return F

def derin(klasor, liste=None, evren=None, gun=KAYIT_GUNU, hedef="sonuc/temel-derin.json"):
    L = ["yfinance " + getattr(yf, "__version__", "?"), "zaman " + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")]
    if liste is None:
        liste = [x.strip() for x in open("temel/derin_liste.txt") if x.strip()]
    if evren is None:
        evren = [x.strip() for x in open("temel/evren_liste.txt") if x.strip()]
    K = {"zaman": L[1][6:], "kayit_gunu": gun,
         "fiyat": kayit_fiyatlari(sorted(set(evren + liste + KIYAS)), gun), "tablo": {}}
    for n, s in enumerate(liste):
        K["tablo"][s] = derin_bir(s)
        time.sleep(0.3)
        if n % 25 == 0:
            print("derin", n, "/", len(liste), flush=True)
    eksik_f = [s for s, v in K["fiyat"].items() if "hata" in v]
    eksik_t = [s for s, v in K["tablo"].items() if not v.get("yillik_gelir")]
    L.append("fiyat alinamayan: %d %s" % (len(eksik_f), ",".join(eksik_f[:30])))
    L.append("yillik tablo alinamayan: %d %s" % (len(eksik_t), ",".join(eksik_t[:30])))
    L.append("fiyat tarihleri: %s" % dict(collections.Counter(v.get("tarih") for v in K["fiyat"].values())))
    hatalar = collections.Counter(k for v in K["tablo"].values() for k in v if k.endswith("_hata"))
    L.append("tablo hatalari: %s" % dict(hatalar))
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as f:
        json.dump(K, f, ensure_ascii=False)
    yaz(klasor, "derin.txt", "\n".join(L) + "\n")
    print("\n".join(L))
    return K

# --- izle: kayitli sepetlerin kayit gununden bugune toplam getirisi (temettu duzeltmeli, ayni seriden) ---
def _seri(df, s):
    try:
        a = df["Adj Close"]
        if hasattr(a, "columns"):
            a = a[s] if s in a.columns else a.iloc[:, 0]
        return a.dropna()
    except Exception:
        return None

def _gecerli(a, gun):
    return a is not None and not a.empty and str(a.index[0].date()) == gun

def izle(klasor):
    L = ["zaman " + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")]
    for yol in sorted(glob.glob("temel/kayit/uzun-vade-kayit-*.json")):
        R = json.load(open(yol, encoding="utf-8"))
        kid, gun = R["kayit_id"], R["kayit_fiyati_tarihi"]
        hedef = "sonuc/uzun-vade-izleme-%s.json" % kid
        onceki = json.load(open(hedef, encoding="utf-8")) if os.path.exists(hedef) else {"getiri": {}}
        semboller = sorted(set(s for v in R["sepetler"].values() for s in v) | set(R["kiyas"]))
        df = _indir(semboller, gun)
        seriler = {s: _seri(df, s) for s in semboller}
        for s in [s for s in semboller if not _gecerli(seriler[s], gun)]:
            for k in range(2):  # toplu indirmede gecici hata (or. onbellek kilidi): tek tek, iplik olmadan yeniden dene
                try:
                    a = _seri(yf.download(s, start=gun, auto_adjust=False, progress=False, threads=False), s)
                except Exception:
                    a = None
                if _gecerli(a, gun):
                    seriler[s] = a
                    break
                time.sleep(2 + 2 * k)
        G = {}
        for s in semboller:
            try:
                a = seriler[s]
                if not _gecerli(a, gun):
                    raise ValueError("kayit gunu verisi yok")
                G[s] = {"getiri": round(float(a.iloc[-1] / a.iloc[0] - 1), 5), "son_tarih": str(a.index[-1].date()), "kaynak": "yahoo"}
            except Exception as e:
                o = onceki["getiri"].get(s)
                G[s] = dict(o, kaynak="onceki_izleme (" + repr(e)[:60] + ")") if o else {"getiri": None, "kaynak": "yok (" + repr(e)[:60] + ")"}
        S = {}
        for ad, liste in R["sepetler"].items():
            x = sorted(G[s]["getiri"] for s in liste if G[s]["getiri"] is not None)
            if x:
                S[ad] = {"n": len(x), "eksik": len(liste) - len(x), "esit_agirlik": round(sum(x) / len(x), 5),
                         "medyan": round(x[len(x) // 2] if len(x) % 2 else (x[len(x) // 2 - 1] + x[len(x) // 2]) / 2, 5),
                         "kat3_ustu": sum(1 for v in x if v >= 2.0), "yari_kayip": sum(1 for v in x if v <= -0.5)}
        son = max((v["son_tarih"] for v in G.values() if v.get("son_tarih")), default=None)
        Z = {"kayit_id": kid, "kayit_fiyati_tarihi": gun, "guncelleme": L[0][6:], "son_gun": son,
             "sepet": S, "kiyas": {s: G[s]["getiri"] for s in R["kiyas"]}, "getiri": G}
        os.makedirs("sonuc", exist_ok=True)
        with open(hedef, "w", encoding="utf-8") as f:
            json.dump(Z, f, ensure_ascii=False, indent=1)
        L.append("%s son gun %s | %s | kiyas %s" % (kid, son, {k: v["esit_agirlik"] for k, v in S.items()}, Z["kiyas"]))
    yaz(klasor, "izle.txt", "\n".join(L) + "\n")
    print("\n".join(L))

# --- kohort: 6 ayda bir ayni yontemle yeni mekanik kayit (B + C + kiyas). A sepeti Claude tarafindan Drive'a ayrica kaydedilir ---
def son_islem_gunu():
    df = yf.download("SPY", period="10d", auto_adjust=False, progress=False, threads=False)
    return str(df.dropna(how="all").index[-1].date())

def ay_ekle(gun, n):
    import calendar
    d = dt.date.fromisoformat(gun)
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1])).isoformat()

def kohort(klasor, test=False):
    from zoneinfo import ZoneInfo
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "analiz"))
    import puanla, derin_olc, sepet_b
    simdi = dt.datetime.now(dt.timezone.utc)
    kid = ("TEST-" if test else "") + "UV-" + simdi.astimezone(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d")
    hedef = ("sonuc/kohort-test/" if test else "temel/kayit/") + "uzun-vade-kayit-%s.json" % kid
    if os.path.exists(hedef):
        print("KOHORT YOK: bu donemin kaydi zaten var, dosya degistirilmez:", hedef, flush=True)
        return
    gun = son_islem_gunu()
    klas = "sonuc/kohort-test" if test else "sonuc/kohort-%s" % kid
    print("kohort", kid, "kayit fiyati gunu", gun, flush=True)
    K = tarama(klasor, hedef=klas + "/temel-tarama.json", bist_dahil=False)
    U, ele1 = puanla.hazirla(K)
    liste = sorted(d["sembol"] for d in U)
    C0 = sorted(d["sembol"] for d in K["abd"] if "hata" not in d)
    D = derin(klasor, liste=liste, evren=C0, gun=gun, hedef=klas + "/temel-derin.json")
    F = D["fiyat"]
    gecerli = lambda x: F.get(x, {}).get("tarih") == gun
    fiyatsiz = sorted(x for x in set(C0 + KIYAS) if not gecerli(x))
    C = [x for x in C0 if gecerli(x)]
    M, _ = derin_olc.hepsi(K, D)
    M = {x: m for x, m in M.items() if gecerli(x)}
    ilk20, sira, G, Kal = sepet_b.sec(M)
    f = lambda v: None if v is None else round(v, 4)
    R = {
     "kayit_id": kid,
     "kayit_fiyati_tarihi": gun,
     "olusturma": simdi.strftime("%Y-%m-%d %H:%M UTC") + " (GitHub Actions, otomatik kohort; kayit fiyati ABD normal seans kapanisi)",
     "olusturan": "GitHub Actions 'Temel tarama' is akisi, kohort modu (mekanik; yargi yok)",
     "amac": "UV-2026-11-21 ile ayni yontemle 6 ayda bir yeni kohort. Bu dosya B (sistematik) ve C (ekran evreni) sepetlerini kaydeder. A sepeti (Claude'un secimi) yalnizca a_aday_listesi'nden 10 hisse olarak secilir ve Drive Tahmin defterine 'uzun-vade-kayit-%s-A.json' adiyla kaydedilir; A'nin getirisi bu kohortun izleme dosyasindaki hisse getirilerinden hesaplanir (A, C'nin alt kumesidir). Yatirim tavsiyesi degildir." % kid,
     "yontem": "Yahoo ekrani (ABD borsalari, piyasa degeri 0,3-40 milyar $, fiyat >=3 $, hacim >=200 bin, gelir buyumesi >=%15, brut marj >=%40, kaldiracli FCF >0); temel/analiz/puanla.py ilk eleme; derin_olc.py olcutler; sepet_b.py kapilar ve agirliklar (UV-2026-11-21 ile ayni).",
     "huni": {"ekran": len(C0), "ilk_eleme_sonrasi": len(liste), "ilk_eleme_nedenleri": ele1,
              "b_kapilarindan_gecen": len(G), "b_kapisi_eleme_nedenleri": dict(collections.Counter(Kal.values())),
              "kayit_fiyati_olmayan": fiyatsiz},
     "a_aday_listesi": liste,
     "sepetler": {"B_sistematik": ilk20, "C_ekran_evreni": C},
     "kiyas": KIYAS,
     "B_detay": [{"sembol": x, "ad": M[x]["info"].get("shortName"), "puan": M[x]["puan_b"], "kayit_kapanis": F[x]["kapanis"],
                  "piyasa_degeri_mn": round(M[x]["mcap"] / 1e6), "fcf_eksi_sbc_getirisi": f(M[x]["fcf_sbc_getiri"]),
                  "gelir_bilesik_buyume": f(M[x]["cagr"]), "brut_marj": f(M[x]["brut_son"])} for x in ilk20],
     "hipotezler": [
      {"id": "H1", "ana": True, "metin": "36. ayda (%s kapanisi) A sepetinin esit agirlikli toplam getirisi IWM'in toplam getirisinden yuksek olur." % ay_ekle(gun, 36)},
      {"id": "H2", "metin": "36. ayda A sepeti B sepetini gecer."},
      {"id": "H3", "metin": "36. ayda B sepeti C evrenini gecer."},
      {"id": "H4", "metin": "36. ayda A sepetinde 3 kat (>= +%200) yapan hisselerin orani C evrenindeki orandan yuksek olur."}],
     "degerlendirme": {"yontem": "Esit agirlik, kayit kapanisinda al-tut, yeniden dengeleme yok; getiri ayni temettu duzeltmeli seride degerlendirme gunu / kayit gunu - 1.",
                       "kote_olmayan_hisse": "Satin alma ya da borsadan cikma: son islem fiyati ile kapanir, sonrasi %0; iflas: -%100.",
                       "ara_kontroller": [ay_ekle(gun, 6), ay_ekle(gun, 12), ay_ekle(gun, 24)], "nihai": ay_ekle(gun, 36),
                       "ara_kontrol_kurali": "Ara kontrollerde hukum verilmez."},
     "fiyatlar": {x: {"kapanis": F[x]["kapanis"], "duz_kapanis": F[x]["duz_kapanis"]} for x in sorted(set(C + KIYAS) - set(fiyatsiz))},
    }
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    print("KOHORT YAZILDI", hedef, "| gun", gun, "| C", len(C), "| A aday", len(liste), "| B kapisi", len(G),
          "| fiyatsiz", fiyatsiz[:10], "| B:", ",".join(ilk20), flush=True)
    if not test:
        izle(klasor)

# --- evds-test: EVDS3 anahtarinin calistigini dogrular (anahtari asla yazdirmaz) ---
def evds_cek(seriler, bas, son, anahtar):
    import urllib.request, ssl
    url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/series=%s&startDate=%s&endDate=%s&type=json" % ("-".join(seriler), bas, son)
    son_hata = None
    for eski_ssl in (False, True):
        ctx = ssl.create_default_context()
        if eski_ssl:
            ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        try:
            req = urllib.request.Request(url, headers={"key": anahtar, "User-Agent": "bist-veri/1.0"})
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return r.status, r.read().decode("utf-8", "replace"), eski_ssl
        except Exception as e:
            son_hata = e
            kod = getattr(e, "code", None)
            if kod is not None:
                return kod, (e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""), eski_ssl
    return None, repr(son_hata)[:300], True

def evds_test(klasor):
    anahtar = os.environ.get("EVDS_API_KEY", "").strip()
    print("anahtar tanimli:", bool(anahtar), "| uzunluk:", len(anahtar), flush=True)
    bugun = dt.date.today()
    bas, son = (bugun - dt.timedelta(days=500)).strftime("%d-%m-%Y"), bugun.strftime("%d-%m-%Y")
    for seri in ("TP.DK.USD.A.YTL", "TP.FG.J0"):
        kod, govde, eski = evds_cek([seri], bas, son, anahtar)
        alan = seri.replace(".", "_")
        try:
            J = json.loads(govde)
            items = J.get("items", [])
            dolu = [x for x in items if x.get(alan) not in (None, "", "null")]
            print("%s | HTTP %s | eski SSL %s | anahtarlar %s | gozlem %d | dolu %d | son %s" % (
                seri, kod, eski, sorted(J.keys())[:5], len(items), len(dolu),
                [(x.get("Tarih"), x.get(alan)) for x in dolu[-3:]]), flush=True)
        except Exception:
            print("%s | HTTP %s | eski SSL %s | yanit JSON degil: %s" % (seri, kod, eski, govde[:200].replace(anahtar or "@@", "***")), flush=True)

if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else "kesif"
    klasor = sys.argv[2] if len(sys.argv) > 2 else "cikti"
    if mod == "kesif":
        kesif(klasor)
    elif mod == "tarama":
        tarama(klasor)
    elif mod == "derin":
        derin(klasor)
    elif mod == "izle":
        izle(klasor)
    elif mod == "kohort":
        kohort(klasor)
    elif mod == "kohort-test":
        kohort(klasor, test=True)
    elif mod == "evds-test":
        evds_test(klasor)
    else:
        print("bilinmeyen mod", mod); sys.exit(2)
