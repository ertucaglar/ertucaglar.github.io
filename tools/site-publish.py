#!/usr/bin/env python3
"""Kanzhook Games sitesinin ön denetimi, GitHub Pages ayarı ve canlı adres denetimi.

  python3 tools/site-publish.py prepare          GitHub'ın commit'ini alır, doldurulmamış alanı, app-ads.txt'yi, CNAME ve
                                                 .nojekyll'ı denetler; commit'ten ve push'tan önce koşulur
  python3 tools/site-publish.py pages [--apply]  GitHub Pages'in, alan adının, sertifikanın ve GitHub'ın DNS
                                                           denetiminin durumu; --apply Pages'i açar, gerekirse alan adını
                                                           (yeniden) bağlar, sertifika hazırsa HTTPS'i zorunlu yapar
  python3 tools/site-publish.py check            DNS kayıtlarını, yayındaki sayfaların kaynakla aynı olduğunu,
                                                           app-ads.txt'yi, http → https ve www → kök yönlendirmesini denetler

Site https://kanzhookgames.com/ (GitHub Pages + GoDaddy DNS, ADR-0096 eki 2026-11-16): kökte Kanzhook Games'in oyun
listesi ve app-ads.txt, her oyun kendi klasöründe (/<oyun>/, /<oyun>/privacy, /<oyun>/support; dil ?lang=EN|TR, site.js).
Kaynak ve yayın aynı depo: kanzhook-games/kanzhook-site (ertucaglar/ertucaglar.github.io, herkese açık kullanıcı sitesi).
2026-11-16'ya kadar kaynak the-adam-game deposunun docs/site'ıydı ve build adımı onu site-pages/'e kopyalıyordu.
Push'u ve --apply'ı Ertuğrul yapar ya da açıkça ister (the-adam-game ADR-0096). Kurulum: README.md.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = ROOT
OUTPUT = ROOT
# Adres tek yerden değişir: alan adı, deposu ve www'nun gösterdiği GitHub adresi.
DOMAIN = "kanzhookgames.com"
REPO = "ertucaglar/ertucaglar.github.io"
PAGES_HOST = "ertucaglar.github.io"
BASE_URL = f"https://{DOMAIN}"
# GitHub Pages'in kök alan adı adresleri (docs.github.com → Managing a custom domain, 2026-11-16).
GITHUB_A = {"185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"}
GITHUB_AAAA = {"2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153"}
# Yayıncı kimliğinin kaynağı the-adam-game'in reklam içeriği; oyunlar kanzhook-games altında bu deponun kardeşidir.
ADS_CONTENT = os.path.join(os.path.dirname(ROOT), "the-adam-game", "Assets", "Game", "Resources", "Game", "Content", "ads_admob.json")
# Sitenin sayfası olmayan dosyalar: denetimde yayındakiyle karşılaştırılmaz (depo herkese açık; yayında da durur).
SKIP = {"README.md", "CLAUDE.md", ".DS_Store", ".nojekyll", "CNAME", ".gitignore"}
SKIP_DIRS = {".git", "tools", ".claude"}
# GitHub'ın sertifikayı istemeye devam ettiği durumlar (REST API → Pages → https_certificate.state). Bunların dışındaki
# her durum (yok, errored, bad_authz, authorization_revoked, dns_changed, destroy_pending) beklemekle düzelmez.
PENDING_CERT = {"new", "authorization_created", "authorization_pending", "authorized", "issued", "uploaded"}


def fail(text):
    print(f"HATA: {text}")
    sys.exit(1)


def publisher_id():
    """ads_admob.json'daki uygulama kimliğinden yayıncı kimliği: ca-app-pub-1234~5 → pub-1234."""
    with open(ADS_CONTENT, encoding="utf-8") as handle:
        app_id = json.load(handle)["ios"]["appId"]
    return "pub-" + app_id.split("ca-app-pub-")[1].split("~")[0]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=OUTPUT)


def checked(cmd):
    done = run(cmd)
    if done.returncode != 0:
        fail(f"{' '.join(cmd)}: {(done.stderr or done.stdout).strip()[:300]}")
    return done


def sync_remote():
    """GitHub alan adını ayarlardan bağlarken dala kendi CNAME commit'ini atabilir: uzak dal ilerideyse önce o alınır,
    yoksa sonraki push reddedilirdi. Yerel ile uzak ayrışmışsa durur."""
    if not run(["git", "remote"]).stdout.strip():
        return
    checked(["git", "fetch", "origin"])
    if run(["git", "rev-parse", "--verify", "--quiet", "origin/main"]).returncode != 0:
        return
    if run(["git", "merge", "--ff-only", "origin/main"]).returncode != 0:
        fail(f"kanzhook-site ile GitHub'daki main ayrışmış (ikisinde de öbüründe olmayan commit var); "
             f"bak: git -C {OUTPUT} log --oneline --graph main origin/main")


def prepare(_args):
    expected = publisher_id()
    sync_remote()
    for folder, dirs, files in os.walk(SOURCE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith((".html", ".txt", ".css")):
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                if "{{" in handle.read():
                    fail(f"doldurulmamış alan: {os.path.join(folder, name)}")
    with open(os.path.join(SOURCE, "app-ads.txt"), encoding="utf-8") as handle:
        if expected not in handle.read():
            fail(f"app-ads.txt yayıncı kimliğini ({expected}) taşımıyor")
    # Jekyll kapalı: dosyalar olduğu gibi sunulur. Daldan yayında özel alan adı kökteki CNAME'dir; GitHub'ın ayarlardan
    # yazdığıyla aynı biçimde (satır sonu yok).
    if not os.path.exists(os.path.join(OUTPUT, ".nojekyll")):
        fail(".nojekyll yok: Jekyll açılır, dosyalar olduğu gibi sunulmaz")
    with open(os.path.join(OUTPUT, "CNAME"), encoding="utf-8") as handle:
        if handle.read() != DOMAIN:
            fail(f"CNAME {DOMAIN} değil")
    print("Site hazır. Yayınlamak için:")
    print("  git add -A && git commit -m \"…\"   (Türkçe, emir kipi)")
    print("  git push origin main")
    print("  python3 tools/site-publish.py check")


# --- GitHub Pages ---------------------------------------------------------------------------------------------------

def gh_api(*args):
    """`gh api` çağrısı: (başarılı mı, JSON ya da hata metni). 202 / 204'ün boş gövdesi {}."""
    try:
        done = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    except FileNotFoundError:
        fail("gh yok (GitHub CLI): brew install gh, sonra gh auth login")
    if done.returncode != 0:
        return False, (done.stdout + done.stderr).strip()
    return True, json.loads(done.stdout) if done.stdout.strip() else {}


def gh_write(what, *args):
    ok, answer = gh_api("-X", "PUT", f"repos/{REPO}/pages", *args)
    if not ok:
        fail(f"{what} olmadı: {answer[:300]}")


def read_pages():
    ok, site = gh_api(f"repos/{REPO}/pages")
    if not ok:
        fail(f"Pages'in durumu okunamadı: {site[:300]}")
    return site


def certificate_of(site):
    certificate = site.get("https_certificate") or {}
    return certificate.get("state"), set(certificate.get("domains") or [])


def dns_health():
    """GitHub'ın DNS denetimi (ayarlardaki "Check again"). İlk çağrı 202 döner ve denetimi başlatır, sonuç sonraki
    çağrıda: o zamana kadar None."""
    ok, answer = gh_api(f"repos/{REPO}/pages/health")
    return answer if ok and answer else None


def eligible(health):
    """Kök alan adı ve (GitHub raporluyorsa) www, GitHub'ın gözünden sertifikaya hazır mı."""
    domain, alt = health.get("domain") or {}, health.get("alt_domain")
    return bool(domain.get("is_https_eligible")) and (alt is None or bool(alt.get("is_https_eligible")))


def pages(args):
    ok, site = gh_api(f"repos/{REPO}/pages")
    if not ok:
        if "Not Found" not in site and "404" not in site:
            fail(f"GitHub'a sorulamadı: {site[:300]}")
        if not gh_api(f"repos/{REPO}")[0]:
            fail(f"{REPO} deposu yok: önce `gh repo create {REPO} --public --source=. --remote=origin --push`")
        if not args.apply:
            print(f"GitHub Pages {REPO} deposunda kapalı. Açmak için: site-publish.py pages --apply")
            sys.exit(1)
        ok, answer = gh_api("-X", "POST", f"repos/{REPO}/pages", "-f", "build_type=legacy",
                            "-f", "source[branch]=main", "-f", "source[path]=/")
        if not ok:
            fail(f"Pages açılamadı: {answer[:300]}")
        print(f"GitHub Pages açıldı: main dalının kökü yayınlanıyor ({REPO}).")
        print("İlk derleme daldaki CNAME dosyasını okuyup alan adını bağlar. Bir dakika sonra yeniden: "
              "site-publish.py pages --apply")
        sys.exit(1)

    # Derleme bittiği hâlde alan adı bağlanmadıysa ayardan yazılır (dalda CNAME varken olmaması beklenir).
    if args.apply and site.get("cname") != DOMAIN and site.get("status") == "built":
        gh_write("alan adını bağlamak", "-f", f"cname={DOMAIN}")
        print(f"Alan adı ayardan bağlandı: {DOMAIN}")
        site = read_pages()

    www = f"www.{DOMAIN}"
    state, domains = certificate_of(site)
    needs_certificate = state != "approved" or www not in domains
    health = dns_health() if site.get("cname") == DOMAIN and needs_certificate else None

    # Alan adı DNS'ten önce bağlandığı için (README'deki sıra) GitHub sertifikayı ilk denemede alamaz; DNS sonradan
    # düzelince sertifika ancak alan adı yeniden bağlanınca istenir (GitHub'ın sorun giderme belgesi). Yalnızca GitHub
    # DNS'i hazır gördüğünde ve sertifika beklemede değilken: sürüp giden isteği bozmamak için.
    if args.apply and health and eligible(health) and needs_certificate and state not in PENDING_CERT:
        gh_write("alan adını kaldırmak", "-F", "cname=null")
        gh_write("alan adını yeniden bağlamak", "-f", f"cname={DOMAIN}")
        print("Alan adı yeniden bağlandı: GitHub sertifikayı kök ve www için yeniden istiyor. Bir sonraki build GitHub'ın "
              "CNAME commit'lerini kendisi alır.")
        site = read_pages()
        state, domains = certificate_of(site)
        needs_certificate = state != "approved" or www not in domains

    if args.apply and not needs_certificate and not site.get("https_enforced"):
        gh_write("HTTPS'i zorunlu yapmak", "-F", "https_enforced=true")
        print("HTTPS zorunlu yapıldı: http:// adresleri https:// adresine yönlenir")
        site = read_pages()
        state, domains = certificate_of(site)

    print(f"Pages:         {site.get('html_url') or '-'} (derleme: {site.get('status') or '-'})")
    print(f"Alan adı:      {site.get('cname') or 'bağlı değil'}")
    print(f"Sertifika:     {state or 'yok'} ({', '.join(sorted(domains)) or '-'})")
    print(f"HTTPS zorunlu: {'evet' if site.get('https_enforced') else 'hayır'}")
    if health:
        for key, name in (("domain", DOMAIN), ("alt_domain", www)):
            part = health.get(key) or {}
            if part:
                verdict = "hazır" if part.get("is_https_eligible") else f"hazır değil ({part.get('reason') or 'DNS'})"
                print(f"GitHub'ın DNS denetimi, {name}: {verdict}")

    complete = site.get("cname") == DOMAIN and not needs_certificate and site.get("https_enforced")
    if not complete:
        if site.get("cname") != DOMAIN:
            print("Alan adı bağlanmadı: derleme bitince yeniden `pages --apply`.")
        elif needs_certificate and state in PENDING_CERT:
            print("GitHub sertifikayı istiyor: dakikalar, en çok 24 saat. Sonra yeniden `pages --apply`.")
        elif needs_certificate and not health:
            print("GitHub'ın DNS denetimi başladı ya da okunamadı: bir dakika sonra yeniden `pages --apply`.")
        elif needs_certificate and eligible(health):
            print("GitHub DNS'i hazır görüyor: sertifikayı istemek için `pages --apply` (alan adını yeniden bağlar).")
        elif needs_certificate:
            print("GitHub DNS'i henüz hazır görmüyor: GoDaddy kayıtları için `site-publish.py check`.")
    sys.exit(0 if complete else 1)


# --- Denetim --------------------------------------------------------------------------------------------------------

def dig(name, kind, server=None):
    """`dig +short` → (kayıtlar, hata). Kayıtlar sondaki noktasız ve küçük harfli; dig yoksa (None, None)."""
    cmd = ["dig", "+short", "+time=5", "+tries=2", name, kind] + ([f"@{server}"] if server else [])
    try:
        done = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return None, None
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    errors = [line for line in lines if line.startswith(";")]
    if done.returncode != 0 or errors:
        return [], (errors[0] if errors else (done.stderr.strip() or f"dig çıkış kodu {done.returncode}"))[:160]
    return [line.rstrip(".").lower() for line in lines], None


def check_dns():
    """Kayıtlar alan adının kendi ad sunucusunda (GoDaddy'de ne yazılı) ve olağan çözücüde (dünya ne görüyor) ölçülür."""
    names, error = dig(DOMAIN, "NS")
    if names is None:
        print("bilgi  dig yok: DNS denetimi atlandı")
        return 0
    server = names[0] if names else None
    answers = {}
    for key, name, kind in (("a", DOMAIN, "A"), ("aaaa", DOMAIN, "AAAA"), ("www", f"www.{DOMAIN}", "CNAME")):
        records, error = dig(name, kind, server) if not error else ([], error)
        answers[key] = records
    if error or not server:
        # Sorgu yapılamadıysa kayıtlar hakkında hüküm verilmez ("eksik" demek GoDaddy'de boş yere kurcalatırdı).
        print(f"DÜŞTÜ  DNS sorgusu yapılamadı · {error or 'ad sunucusu bulunamadı'}")
        return 1
    bad = 0

    a, aaaa = set(answers["a"]), set(answers["aaaa"])
    extra, missing = sorted(a - GITHUB_A), sorted(GITHUB_A - a)
    detail = [f"silinecek: {', '.join(extra)}"] * bool(extra) + [f"eklenecek: {', '.join(missing)}"] * bool(missing)
    ok = not detail
    print(f"{'tamam ' if ok else 'DÜŞTÜ '} DNS {DOMAIN} A kayıtları ({server}){' · ' + '; '.join(detail) if detail else ''}")
    bad += 0 if ok else 1
    stray = sorted(aaaa - GITHUB_AAAA)
    print(f"{'tamam ' if not stray else 'DÜŞTÜ '} DNS {DOMAIN} AAAA kayıtları (isteğe bağlı)"
          f"{' · silinecek: ' + ', '.join(stray) if stray else ''}")
    bad += 1 if stray else 0
    ok = answers["www"] == [PAGES_HOST]
    print(f"{'tamam ' if ok else 'DÜŞTÜ '} DNS www.{DOMAIN} CNAME → {PAGES_HOST}"
          f"{'' if ok else ' · şu an: ' + (', '.join(answers['www']) or 'yok')}")
    bad += 0 if ok else 1

    public, _ = dig(DOMAIN, "A")
    if a and set(public or []) != a:
        print(f"bilgi  dünyadaki çözücüler henüz eski kayıtları görüyor ({', '.join(sorted(public or [])) or '-'}): "
              "kaydın süresi (TTL) dolunca yayılır, genelde bir saat içinde")
    return bad


def site_files():
    """Kaynağın her dosyası ve yayındaki adresi: x/index.html → /x/, x.html → /x (GitHub Pages uzantısız sunar),
    öteki dosyalar kendi yolunda. Yeni bir oyunun klasörü eklenince denetim onu da kendiliğinden kapsar."""
    for folder, dirs, files in os.walk(SOURCE):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name in SKIP:
                continue
            rel = os.path.relpath(os.path.join(folder, name), SOURCE).replace(os.sep, "/")
            if rel == "index.html" or rel.endswith("/index.html"):
                path = "/" + rel[:-len("index.html")]
            elif rel.endswith(".html"):
                path = "/" + rel[:-len(".html")]
            else:
                path = "/" + rel
            yield path, rel


def source_text(rel):
    with open(os.path.join(SOURCE, rel), encoding="utf-8") as handle:
        return handle.read()


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "navras-site-check"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", "replace")
        return response.status, body, response.headers.get("Content-Type", ""), response.geturl()


def check_url(text, url, test):
    """Adresi çeker, `test(status, body, kind, final)` → (geçti mi, ayrıntı). Ağ ve SSL hataları düşer."""
    try:
        ok, detail = test(*fetch(url))
    except OSError as error:  # URLError, HTTPError (404), SSL, zaman aşımı
        ok, detail = False, str(getattr(error, "reason", error))
    print(f"{'tamam ' if ok else 'DÜŞTÜ '} {text}{' · ' + detail if detail else ''}")
    return 0 if ok else 1


def published(rel, extra=None):
    """Yayındaki dosya bizim site mi ve kaynakla bayt bayt aynı mı (park sayfası, eski sürüm ya da yönlendirme düşer)."""
    expected = source_text(rel)

    def test(status, body, kind, final):
        host = urllib.parse.urlsplit(final).hostname
        if status != 200 or host != DOMAIN:
            return False, f"{status}, varılan: {final}"
        if body != expected:
            return False, "yayındaki dosya kaynakla aynı değil (park sayfası, eski sürüm ya da push edilmemiş değişiklik)"
        return extra(kind) if extra else (True, "")
    return test


def check(_args):
    bad = check_dns()
    line = f"google.com, {publisher_id()}, DIRECT, f08c47fec0942fa0"
    if line not in source_text("app-ads.txt"):
        fail(f"app-ads.txt yayıncı satırını taşımıyor: {line}")
    for path, rel in site_files():
        extra = (lambda kind: (kind.startswith("text/plain"), kind)) if rel == "app-ads.txt" else None
        bad += check_url(BASE_URL + path, BASE_URL + path, published(rel, extra))

    def lands_on_base(_status, _body, _kind, final):
        parsed = urllib.parse.urlsplit(final)
        return parsed.scheme == "https" and parsed.hostname == DOMAIN, f"varılan: {final}"

    bad += check_url("http:// → https:// (HTTPS zorunlu)", f"http://{DOMAIN}/", lands_on_base)
    bad += check_url(f"www.{DOMAIN} → {DOMAIN}", f"https://www.{DOMAIN}/", lands_on_base)
    bad += check_url(f"{PAGES_HOST} → {DOMAIN}", f"https://{PAGES_HOST}/", lands_on_base)
    if bad:
        print(f"\n{bad} madde düştü. Kurulum adımları: README.md → Yayınlamak")
    sys.exit(1 if bad else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare").set_defaults(func=prepare)
    pages_parser = sub.add_parser("pages")
    pages_parser.add_argument("--apply", action="store_true",
                              help="Pages'i aç, gerekirse alan adını (yeniden) bağla, sertifika hazırsa HTTPS'i zorunlu yap")
    pages_parser.set_defaults(func=pages)
    sub.add_parser("check").set_defaults(func=check)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
