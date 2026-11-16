# Kanzhook Games sitesi

Bütün Kanzhook oyunlarının gizlilik politikası, destek sayfası ve `app-ads.txt`'si tek statik sitede: <https://kanzhookgames.com/>. AdMob'un gizlilik mesajları, App Store ve Google Play bu adresleri ister (rehber: the-adam-game deposunda `docs/guides/ads-revenue.md`).

Bu depo hem kaynak hem yayın: dosyalar burada elle düzenlenir, `main`'e push edilince GitHub Pages yayınlar. **Depo herkese açıktır**: buraya gizli bilgi, iç not ya da taslak yazılmaz. 2026-11-16'ya kadar kaynak the-adam-game deposunun `docs/site/`'ıydı ve `site-publish.py build` onu `site-pages/`'e kopyalıyordu.

| Sayfa | Adres | Kaynak | Kim ister |
|---|---|---|---|
| Kanzhook Games (oyun listesi) | `https://kanzhookgames.com/` | `index.html` | Play (iletişim bilgilerinde web sitesi) |
| `app-ads.txt` | `https://kanzhookgames.com/app-ads.txt` | `app-ads.txt` | AdMob; mağazadaki web sitesinin kök alan adında arar |
| Oyunun sayfası | `https://kanzhookgames.com/the-adam-game/` | `the-adam-game/index.html` | App Store (Marketing URL) |
| Gizlilik politikası | `https://kanzhookgames.com/the-adam-game/privacy` | `the-adam-game/privacy.html` | App Store (Privacy Policy URL), Play (Gizlilik politikası beyanı), oyunun Ayarlar ekranı, AdMob gizlilik mesajları |
| Destek | `https://kanzhookgames.com/the-adam-game/support` | `the-adam-game/support.html` | App Store (Support URL), oyunun Ayarlar ekranı, Play Veri güvenliği (veri silme isteği) |
| Eski adresler | `/privacy/`, `/support/` | `privacy/index.html`, `support/index.html` | Yeni adrese yönlendirir: 2026-11-16'dan önceki build'lerin Ayarlar bağlantıları `ertucaglar.github.io/privacy/`'yi açar, GitHub o adresi `kanzhookgames.com`'a çevirir |

**Dil.** Her sayfa iki dili de taşır (`data-lang="en"` / `"tr"`). `site.js` birini seçer, `style.css` ötekini gizler; betik çalışmazsa ikisi de görünür. Seçim sırası:

1. Adresteki `?lang=EN` ya da `?lang=TR` (büyük / küçük harf fark etmez).
2. Tarayıcının dili.
3. İngilizce.

Mağazalara dil başına `?lang=` verilir (App Store'un en-US sayfasına `?lang=EN`, tr sayfasına `?lang=TR`). Oyunun içinden ve Play'in tek alanından parametresiz açılır; telefonun dili seçer.

**Barındırma ücretsiz.**
- GitHub Pages: herkese açık kullanıcı sitesi deposu `ertucaglar/ertucaglar.github.io`, `CNAME` dosyasıyla `kanzhookgames.com`'a bağlı. Eski `ertucaglar.github.io` adresi kendiliğinden buraya yönlenir.
- Alan adı GoDaddy'de (2026-11-16'da alındı).
- HTTPS sertifikasını GitHub ücretsiz verir ve yeniler.
- Sunucu ve aylık ücret yok; yalnızca alan adının yıllık yenilemesi.

Karar: the-adam-game deposunda `docs/adr/ADR-0096-store-release-readiness.md`, eki 2026-11-16.

Site alan adının KÖKÜNDE durur, alt alan adında (`games.kanzhookgames.com`) değil: AdMob `app-ads.txt`'yi mağazadaki web sitesinin kök alan adında arar.

## Yeni oyun eklemek

1. Klasör `<oyun>/`; adı oyunun `kanzhook-games/` altındaki klasörüyle aynı (the-adam-game'in `store-check.py`'si adresleri buna göre denetler). İçinde:
   - `index.html`: oyunun sayfası.
   - `privacy.html`: gizlilik.
   - `support.html`: destek.

   Sayfalar `/style.css` ve `/site.js`'yi kökten alır; iki dil `data-lang` ile. Örnek `the-adam-game/`.
2. Kökteki `index.html`'in oyun listesine satır eklenir.
3. Oyunun AdMob yayıncı kimliği farklıysa `app-ads.txt`'ye satırı eklenir. Bir hesapta bir satır yeter.
4. `prepare`, commit, push, `check` (aşağıda). `check` kaynaktaki her dosyayı yayındaki karşılığıyla karşılaştırır, yeni klasörü kendiliğinden kapsar.

## Yayınlamak

Kaynak ve yayın bu depo (`ertucaglar/ertucaglar.github.io`). Push canlı siteyi değiştirir: Ertuğrul yapar ya da açıkça ister.

```bash
python3 tools/site-publish.py prepare    # GitHub'ın kendi commit'i varsa önce onu alır; boş alan, app-ads.txt, CNAME, .nojekyll
git add -A && git commit -m "…"
git push origin main
python3 tools/site-publish.py pages --apply
python3 tools/site-publish.py check
```

**`pages --apply`** her koşuda yalnızca eksik olanı yapar ve sonraki adımı yazar:
- Pages'i açar.
- Derleme bittiği hâlde alan adı bağlanmamışsa ayardan bağlar.
- GitHub'ın DNS denetimi (`pages/health`) kök ve `www`'yu hazır gördüğü hâlde sertifika yoksa ya da `www`'yu kapsamıyorsa alan adını yeniden bağlar. Sertifika istenirken (`new` … `uploaded`) dokunmaz.
- Sertifika iki adı kapsayınca HTTPS'i zorunlu yapar.

Sertifika dakikalar içinde, en çok 24 saatte gelir.

**`check`** her maddeyi tek satırda yazar ve düşen yoksa 0 ile çıkar:
- GoDaddy'deki kayıtlar, alan adının kendi ad sunucusundan (yazılanı hemen gösterir).
- Dünyanın gördüğü kayıt.
- Depodaki her sayfa dosyasının (README, CLAUDE.md, `tools/` hariç) yayındaki karşılığı bayt bayt aynı mı. Park sayfası, eski sürüm ya da push edilmemiş değişiklik düşer.
- `http://` → `https://`, `www` → kök ve `ertucaglar.github.io` → `kanzhookgames.com` yönlendirmeleri.

DNS sorgusu yapılamazsa kayıtlar hakkında hüküm vermez.

**GoDaddy DNS (2026-11-16'da kuruldu):**
- `A @` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; park kayıtları silindi.
- `CNAME www` → `ertucaglar.github.io`.
- IPv6 isteğe bağlı: `AAAA @` → `2606:50c0:8000::153` … `2606:50c0:8003::153`.
- NS, SOA ve `_domainconnect`'e dokunulmaz.

**Alan adı doğrulaması (bir kez, Ertuğrul; önerilir).** Doğrulanmış alan adını başka bir GitHub hesabı kendi sitesine bağlayamaz.
1. GitHub → sağ üst profil → Settings → (sol menü, Code, planning, and automation) Pages → **Add a domain** → `kanzhookgames.com` → Add domain.
2. GitHub bir TXT kaydı gösterir. Adı `_github-pages-challenge-ertucaglar`, değeri uzun bir kod.
3. GoDaddy'de DNS Records → Add New Record → Type `TXT`, Name `_github-pages-challenge-ertucaglar`, Value GitHub'ın kodu → Save.
4. Birkaç dakika sonra GitHub'da **Verify**.

## Metin kuralı

- Oyunun kullandığı veriler değişirse (yeni SDK, yeni analitik olayı) `<oyun>/privacy.html` aynı turda güncellenir; App Store App Privacy ve Google Play Data safety beyanları da (the-adam-game: `docs/guides/store-declarations.md`).
- Gizlilik metni Claude'un taslağıdır, hukuki görüş değildir. Ertuğrul ayrıca kontrol ettirecek.
- Google Play gizlilik politikasında ya mağaza sayfasındaki geliştirici adını ya da uygulamanın adını ister. Metin "The Adam Game"i ve veri sorumlusu Ertuğrul Çağlar'ı adıyla anar. Play'deki geliştirici adı ileride "Kanzhook Games"e dönerse gizlilik metninin ilk paragrafı ona göre güncellenir (bugün sitenin kökü Kanzhook Games adını taşır, veri sorumlusu kişi olarak Ertuğrul Çağlar).
- Alan adı değişirse tek yer `tools/site-publish.py`'deki `DOMAIN`. Oyundaki adresler (`game.json`, `Store/app-store.json`, `Store/play-store.json`) oyunun klasöründeki sayfalar olmalı (isteğe bağlı `?lang=EN|TR`): `store-check.py` bunu denetler.
