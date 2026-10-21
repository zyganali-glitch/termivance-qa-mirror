# TERMİVANCE — Operatör Çekim, Video ve Devpost Gönderim Rehberi (Türkçe)

**Kim için:** Teknik olmayan operatör için, denetmen (auditor) gözetiminde adım adım uygulanacak şekilde hazırlandı.
**Tarih hedefi:** 25 Ekim akşamı çekim → 26 Ekim video + YouTube + Devpost gönderimi. 27 Ekim 16:00 (Türkiye) son teslim tarihidir; 27 Ekim yalnızca yedek gündür.
**Altın kural:** Bu rehberdeki adımların dışına çıkmayın. Bir ekran açılmazsa "Güvenli Geri Dönüş" satırını uygulayın. Hiçbir adımda şifre, token veya kişisel bilgi göstermeyin.

---

## 0. Başlamadan önce (denetmen onayı şart)

1. **Checkpoint A onayı alınmadan hiçbir çekim yapmayın.** Onay, bağımsız denetmenden (auditor) gelir.
2. Bilgisayarda şu kurulumların yapıldığını denetmenle doğrulayın:
   - `python -m pip install -e ".[dev]"` kurulmuş (proje klasöründe).
   - `pytest -q` → **540 passed** yazıyor.
   - `control_room\index.html` tarayıcıda açılıyor (çift tıklama yeterli).
3. Ekran çözünürlüğünü **1920×1080** yapın: Windows Ayarlar → Sistem → Ekran → Çözünürlük.
4. Tarayıcı yakınlaştırması **%100** olsun (Ctrl+0 tuşu).
5. Kayıt programı: Windows'ta yerleşik **Xbox Game Bar** (Win+G) veya OBS Studio. MP4 kaydı yapabilsin.

## 1. Kullanacağınız bağlantılar (önceden tarayıcı sekmelerine açın)

| Sekme | Adres |
|---|---|
| Kontrol Odası (Control Room) | `control_room\index.html` dosyası (yerel dosya, internet gerekmez) |
| Kanonik depo | https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance |
| Issue #5 | https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/issues/5 |
| Duo oturumu | https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9710085 |
| Hedef Pages sitesi | https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/ |
| GitLab CI hatları | https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/pipelines |
| GitHub QA gözlemcisi | https://github.com/zyganali-glitch/termivance-qa-mirror/actions |

> **Gizlilik:** Tarayıcıda kişisel e-posta hesabına giriş görünmesin; gerekirse gizli (InPrivate) pencere kullanın — ancak GitLab sayfaları üye girişi gerektiriyorsa normal pencere kullanın ve ekranın sağ üst köşesindeki avatar/giriş bilgisi kısmını göstermemeye dikkat edin. Görev çubuğundaki kişisel bildirimleri kapatın.

## 2. Video sahne planı (hedef toplam 174 saniye, sınır 180 saniye)

Her sahne için: ekranda ne görünecek, ne yapacaksınız, sesli anlatım (İngilizce, hazır metin) ve altyazı metni aşağıdadır. Anlatımı **ses kaydederek ya da sonradan ekleyerek** yapabilirsiniz; metinler sahne sürelerine göre ayarlıdır.

### SC-01 · 0:00–0:13 (13 sn) — Sorun ve BLOCKED kararı
- **Ekran:** Control Room, Overview sekmesi.
- **Yapılacak:** Sayfayı açın; fareyle üstteki "What you are looking at" kartını ve kırmızı **RETIREMENT BLOCKED** başlığını yavaşça gezdirin. Tıklama gerekmez.
- **Beklenen görüntü:** Koyu tema, kırmızı BLOCKED karar kartı.
- **İngilizce sesli anlatım:** *"Retiring software isn't proving it's gone. A forgotten CI job can bring a dead service back. Termivance makes retirement a proof-bound protocol — and here, it's blocking an unsafe retirement on purpose."*
- **Altyazı:** `Deleting code is not retiring software. Termivance proves retirement within bounds.`
- **Güvenli geri dönüş:** Sayfa açılmazsa depoyu yeniden açın (`control_room\index.html`).
- **Geçiş:** Sekme çubuğuna kısa zoom.

### SC-02 · 0:13–0:30 (17 sn) — Üç bağımsız karar
- **Ekran:** Control Room, Overview (aşağı kaydırın): "Independent retirement claims" kartı.
- **Yapılacak:** `SAFE_TO_RETIRE: BLOCKED`, `OBSERVED_ABSENT: NOT_CLAIMED`, `RESURRECTION_CONTROLLED: NOT_CLAIMED` kutularını ve turuncu "REDEPLOYMENT MECHANISM" uyarısını gösterin.
- **İngilizce sesli anlatım:** *"Termivance separates three questions: is retirement safe, is absence actually observed, and can the resource come back? Each needs different proof. A GitLab Duo agent investigates — but deterministic Python alone decides, authorizes, and proves."*
- **Altyazı:** `Three independent claims. AI proposes — deterministic code decides.`
- **Geçiş:** GitLab sekmesine geçin.

### SC-03 · 0:30–0:50 (20 sn) — Gerçek Duo incelemesi
- **Ekran:** GitLab tarayıcı — önce Issue #5, sonra Duo oturum sayfası.
- **Yapılacak:** Issue #5 açıklamasını gösterin; aşağı kaydırıp Duo servis hesabının notunu (agent note) gösterin. Sonra Duo oturum bağlantısını açıp inceleme adımlarını gösterin.
- **Beklenen:** `ai-termivance-retirement-analyst-...` hesabından gelen yapılandırılmış analiz notu.
- **İngilizce sesli anlatım:** *"A human asked for retirement on a neutral GitLab issue. A real Duo Custom Flow picked it up, read the target repository, and found a surviving create-pages job that could republish the site — posting its findings as non-authoritative candidates."*
- **Altyazı:** `Genuine GitLab Duo Custom Flow — Session 9710085, neutral Issue #5.`
- **Güvenli geri dönüş:** Duo oturum sayfası açılmazsa (404), Control Room → "Evidence & Audit" sekmesi → "Duo investigation" bölümünü gösterin; anlatı aynı kalır.
- **Geçiş:** Control Room → Evidence & Audit.

### SC-04 · 0:50–1:08 (18 sn) — Aday doğrulama
- **Ekran:** Control Room → **Evidence & Audit** sekmesi → "Candidate corroboration" alt bölümü.
- **Yapılacak:** Session `9710085` kartındaki **4 CORROBORATED / 2 UNRESOLVED / 1 CONTEXTUAL_ONLY** toplamlarını ve `duo-9710085-cand-01` satırını (`create-pages`, commit `54fcc9ff`) gösterin.
- **İngilizce sesli anlatım:** *"Termivance then checks every AI claim against separate GitLab provider facts. Four candidates were corroborated, two stayed unresolved, one was contextual. AI suggestions never become facts without deterministic verification."*
- **Altyazı:** `4 corroborated · 2 unresolved · 1 contextual. AI claims are never auto-promoted.`
- **Geçiş:** Terminal penceresi.

### SC-05 · 1:08–1:40 (32 sn) — CANLI otomatik değerlendirme (en önemli sahne)
- **Ekran:** Terminal (Komut İstemi / PowerShell), proje klasöründe.
- **Yapılacak:** Sırayla çalıştırın:
  1. `scripts\run_supervised_review.bat --no-pause` → canlı inceleme akışını ve son **BLOCKED** kararını gösterin.
  2. `termivance retire-pages --execute --project-id 87785099 --policy config/retirement_policy.b3_disposable.json` → **RED** çıktısını gösterin: "an independent operator trust policy is required for a real mutation" (gerçek bir değişiklik için bağımsız operatör güven politikası gerekir — yok, bu yüzden reddedildi).
- **Beklenen:** Yeşil onay satırları, `inv-...` yürütme kimliği, `EXECUTED_NOW` adımları, `SAFE_TO_RETIRE: BLOCKED` ve ikinci komutta güvenlik reddi (çıkış kodu 2).
- **İngilizce sesli anlatım:** *"Now the deterministic engine runs live. It re-reads the target, evaluates eight retirement obligations, and refuses: safe-to-retire is blocked. Watch the safety refusal: a real mutation demands an independent operator trust policy. AI recommendations cannot authorize deletion - and neither can stale evidence."*
- **Altyazı:** `Live deterministic evaluation — fail-closed, read-only, zero destructive calls.`
- **Güvenli geri dönüş:** Komut hata verirse denetmeni çağırın; videoya hatayı eklemeyin.
- **Geçiş:** Tarayıcı — hedef Pages sitesi.

### SC-06 · 1:40–1:56 (16 sn) — Gerçek yayında olan hedef site
- **Ekran:** Tarayıcı — https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/
- **Yapılacak:** Sayfada `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a` işaretini gösterin (Ctrl+F ile "MARKER" aratıp vurgulayabilirsiniz).
- **Beklenen:** Basit statik sayfa; benzersiz işaret satırı görünür.
- **İngilizce sesli anlatım:** *"The target is real: a GitLab Pages site, publicly serving its unique marker right now. Published by its own CI — which is exactly the resurrection risk. Presence is not retirement."*
- **Altyazı:** `Real target, really published — by the CI job that can bring it back.`
- **Güvenli geri dönüş:** Site açılmazsa Control Room → Evidence & Audit → "Pages publication" kartını gösterin (5 düzeyli kanıt kaydı) ve anlatıya devam edin.
- **Geçiş:** Control Room → Obligation Graph.

### SC-07 · 1:56–2:14 (18 sn) — Yükümlülük grafiği
- **Ekran:** Control Room → **Obligation Graph** sekmesi.
- **Yapılacak:** `resource:ci_redeployment:87785099` düğümüne tıklayın — kenarlar vurgulanır, sağ panelde kayıtlı kanıt görünür. Gerekirse "+ Zoom in" düğmesine basın.
- **İngilizce sesli anlatım:** *"The obligation graph shows what blocks retirement: Pages administration returns forty-three, the redeployment path is active, and no operator authorization exists. Clicking the CI node reveals the exact recorded evidence behind each edge."*
- **Altyazı:** `Retirement Obligation Graph — every blocked edge is evidence-bound.`
- **Geçiş:** What-if sekmesi.

### SC-08 · 2:14–2:30 (16 sn) — Varsayımsal simülasyon + onarım + tazelik
- **Ekran:** Control Room → **What-if** sekmesi; sonra **Evidence & Audit** → "Bounded repair sets" / "Proof freshness" kartları.
- **Yapılacak:** What-if açılır listesinden CI mekanizmasını seçin — `PROJECTED_NOT_OBSERVED` etiketini gösterin. Sonra onarım seti ve 900 saniye tazelik sınırı kartlarını gösterin.
- **İngilizce sesli anlatım:** *"Even hypothetically, projections are labeled projected-not-observed. Termivance proposes bounded repair steps — and evidence expires after fifteen minutes, so stale proof can never authorize anything."*
- **Altyazı:** `Projections never mint verdicts. Evidence expires in 900 seconds.`
- **Geçiş:** GitLab CI sekmesi.

### SC-09 · 2:30–2:46 (16 sn) — Bağımsız doğrulama
- **Ekran:** İki tarayıcı sekmesi: GitLab CI hatları (yeşil "passed") ve GitHub Actions gözlemci koşusu.
- **Yapılacak:** GitLab'ta en son hattın yeşil **passed** durumunu, GitHub'da son koşunun `PASS` / `IN_SYNC` etiketini gösterin.
- **İngilizce sesli anlatım:** *"Every push runs real GitLab CI: five hundred forty tests and forty safety assertions. An independent GitHub observer checks live GitLab APIs and confirms the exact source revision — pass, in sync."*
- **Altyazı:** `Canonical GitLab CI + independent GitHub QA bridge.`
- **Geçiş:** Control Room Overview'a dönün.

### SC-10 · 2:46–2:54 (8 sn) — Kapanış
- **Ekran:** Control Room, Overview — başlığa hafif zoom.
- **Yapılacak:** Ekranda `Termivance — Software retirement, proven within bounds.` yazısı görünsün; hiçbir şey tıklamayın.
- **İngilizce sesli anlatım:** *"Termivance: software retirement, proven within bounds."*
- **Altyazı:** `Termivance — Software retirement, proven within bounds.`
- **Bitiş:** 2:54'te siyaha karartın (180 sn sınırının 6 saniye içinde kalır).

**Toplam: 174 saniye.**

## 3. Ekran kaydı nasıl alınır

1. **Xbox Game Bar:** `Win + G` → "Kaydet" düğmesi (veya `Win + Alt + R`). Her sahneyi ayrı ayrı kaydedebilirsiniz.
2. Kayıttan önce: masaüstünü temizleyin, bildirimleri kapatın (`Win + N` → Odak yardımı).
3. Her sahne kaydı ayrı MP4 dosyası olsun: `sc01.mp4`, `sc02.mp4` … `sc10.mp4`. Bunları `submission_media\raw\clips\` klasörüne kaydedin (bu klasör depoya gitmez).
4. Sesli anlatımı ayrı kaydetmek isterseniz: Windows'ta Ses Kaydedici uygulaması ile her sahnenin metnini yavaş ve net okuyun; dosyaları `submission_media\narration\` klasörüne koyun.

## 4. Video birleştirme ve ses/altyazı ekleme

1. Ücretsiz bir araç kullanın: **Clipchamp** (Windows 11'de hazır) önerilir.
2. Sahne kliplerini sırayla (SC-01 → SC-10) zaman çizgisine sürükleyin.
3. Her sahnenin süresini yukarıdaki plana göre ayarlayın (toplam **174 saniyeyi aşmayın**).
4. Sesli anlatımı (İngilizce) her sahnenin üzerine yerleştirin; metinler sahne süreleriyle uyumludur.
5. Altyazıları ekleyin: Clipchamp → "Captions" → yukarıdaki altyazı metinlerini elle girin (İngilizce).
6. **Müzik eklemeyin** (telif riski). Sadece sesli anlatım.
7. Dışa aktar: 1080p MP4. Dosyayı `submission_media\exports\termivance_demo.mp4` konumuna kaydedin.
8. Süreyi kontrol edin: **180 saniyeden kısa** olmalı (hedef 174).

## 5. YouTube'a yükleme (herkese açık)

1. YouTube'a giriş yapın → sağ üstteki kamera simgesi → **Video yükle**.
2. Dosyayı seçin: `termivance_demo.mp4`.
3. Başlık: `Termivance — Software retirement, proven within bounds (GitLab Transcend 2026)`
4. Açıklamaya şunu yazın (kopyala-yapıştır):
   `Termivance is a Proof-Bounded Software Retirement Protocol for GitLab. One GitLab Duo Custom Flow agent investigates; deterministic Python alone decides, authorizes, and proves. Demo of the real BLOCKED retirement decision, the real disposable GitLab Pages target, and the fail-closed safety refusals. Repository: https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance`
5. **Görünürlük: Herkese Açık (Public)** seçin — "Listelenmemiş/Unlisted" veya "Gizli/Private" KULLANMAYIN.
6. Yükleme bitince video bağlantısını kopyalayın.
7. **Doğrulama:** Gizli/temiz bir tarayıcı penceresi açın (Ctrl+Shift+N), video bağlantısını yapıştırın — video oturum açmadan izlenebiliyor olmalı. İzleyemiyorsanız görünürlük ayarını düzeltin.

## 6. Ekran görüntüleri (Devpost için ~5 görsel)

Aşağıdaki 5 görüntüyü 1920×1080, %100 yakınlaştırma ile alın (`Win + Shift + S` yerine tam ekran kaydı için `PrtScn` veya Xbox Game Bar'ın ekran görüntüsü düğmesini kullanın). Dosyaları `assets\demo\screenshots\` klasörüne, belirtilen adlarla kaydedin:

1. `01_overview_retirement_blocked.png` — Control Room, Overview (BLOCKED kararı görünür).
2. `02_duo_issue5_discovery.png` — GitLab, Issue #5 veya Duo oturumu (ajan notu görünür).
3. `03_candidate_corroboration.png` — Control Room, Evidence & Audit → Candidate corroboration.
4. `04_obligation_graph_focused.png` — Control Room, Graph — `resource:ci_redeployment:87785099` seçili.
5. `05_real_ci_qa_binding.png` — İki pencere yan yana: GitLab CI (yeşil) + GitHub Actions (PASS/IN_SYNC).

**Her görüntüyü yüklemeden önce kontrol edin:** token, şifre, `C:\Users\...` gibi kişisel yol, e-posta adresi veya avatar/giriş bilgisi görünmesin.

## 7. Devpost gönderim sırası

1. https://gitlab-transcend.devpost.com/ → hesabınıza giriş → **Submit a project** (proje gönder).
2. Alanları Master Plan Bölüm 13'teki hazır İngilizce metinlerle doldurun (başlık, kısa açıklama, hikâye, teknolojiler).
3. **Path:** A — Start Fresh. **Autonomy:** Supervised.
4. **DevSecOps aşamaları:** Plan, Verify, Secure, Govern işaretleyin; Create, Package, Configure, Monitor'ı denetmen onayıyla (açıklamalı) işaretleyin; **Release'i işaretlemeyin.**
5. Repository URL: `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance`
6. Video URL: YouTube herkese açık bağlantısı.
7. "Try It Out" bağlantısı: kanonik depo adresi (README'deki Try It Out talimatları).
8. Göndermeden önce denetmene son kontrol için gösterin (Checkpoint B), sonra **Submit** deyin.
9. Gönderimden sonra depoya **hiçbir commit atmayın** (dondurma kuralı).

## 8. Sorun olursa

- Bir site açılmıyorsa → sahne planındaki "Güvenli geri dönüş" satırını uygulayın.
- Terminal hatası → videoya eklemeyin, denetmeni çağırın.
- Süre taşarsa → SC-05'teki ikinci komutu (korunan hedef reddi) kesin değilse kısaltın; asla anlatım hızını artırıp anlaşılırlığı bozmayın.
- YouTube herkese açık değilse → kontrolü 5. adımdaki temiz pencere testiyle doğrulayın.
- Son çare: 27 Ekim sabahı yedek günüdür; panik yapmayın, denetmeni arayın.
