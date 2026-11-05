# serin-content

Serin uygulamasının içeriği. Uygulama `content.json` dosyasını ve görselleri buradan okur. Bu repoya gönderilen değişiklikler, uygulama güncellenmeden kullanıcılara ulaşır.

## Nasıl çalışır

- Uygulama her açılışta `content.json` dosyasını indirir ve son başarılı sürümü telefonda saklar.
- `image` alanları bu repodaki dosya yollarıdır (örn. `images/meditations/sleep.jpg`).
- İnternet yoksa uygulama en son indirdiği içeriği gösterir. Hiç indirmemişse kendi içindeki varsayılan görselleri gösterir.
- GitHub dosyaları yaklaşık 5 dakika önbellekte tuttuğu için değişikliklerin görünmesi birkaç dakika sürebilir.

## Diller

İçerik Türkçe ve İngilizce yazılır. Uygulama telefonun diline göre birini seçer; başka bir dilde İngilizce gösterir. `label`, `title`, `description` ve blog yazısının `body` alanı iki biçimde yazılabilir:

```json
"title": { "tr": "Kadife", "en": "Velvet" }
"body": { "tr": "posts/slow-breathing.md", "en": "posts/slow-breathing.en.md" }
```

Düz bir metin yazarsan her dilde aynı görünür. İstenen dil yoksa İngilizce, o da yoksa elindeki dil kullanılır. Görsel ve ses bütün diller için ortaktır.

**Bu biçim için uygulamanın "içeriği telefon dilinde oku" sürümü gerekir.** Eski bir sürüm `{ "tr": ..., "en": ... }` alanını okuyamaz ve içeriği yok sayar.

## Şimdiki içerik

Sesler `tools/audio/synth.py` ile sıfırdan üretilmiş 4 dakikalık döngülerdir (OGG). Her biri tam periyodik olduğu için uygulama seçilen süre boyunca dikişsiz tekrarlar. Görseller ve blog yazıları hakkında durum `provenance.json` içinde: yer tutucu olanlar yayın öncesi değiştirilmelidir.

## Görsel değiştirme

Uygulama indirdiği görselleri **dosya adına göre** önbellekte saklar. Aynı adla yeni bir görsel yüklersen telefonlar eskisini göstermeye devam eder. Bu yüzden:

1. Yeni görseli **farklı bir adla** ekle (örn. `images/meditations/sleep-2.jpg`).
2. `content.json` içinde ilgili `image` alanını bu yeni adla güncelle.
3. İstersen eski dosyayı sil.

Aynı kural sesler için de geçerli: yeni bir ses dosyası eklerken farklı bir ad kullan ve `audio` alanını güncelle.

Görseller kartlarda ortadan kırpılır. Meditasyon görselleri kare (en az 900×900 px), ana sayfa banner'ı yaklaşık 2.4:1 oranında olmalı.

## Köken ve lisans

`audio/`, `images/` ve `posts/` altındaki her dosyanın `provenance.json` içinde bir kaydı olmalı: nereden geldiği (`source`), hangi koşullarla kullanılabildiği (`license`), ne zaman üretildiği (`created`), yayına hazır olup olmadığı (`status`: `placeholder` ya da `final`) ve dosyanın `sha256` özeti. Yapay zekâ ile üretilenlerde hangi araç (`tool`) ve hangi plan (`plan`: `paid` ya da `free`) olduğu da yazılır. Ücretsiz planda üretilen görsellerin ticari kullanım hakkı olmayabilir, bu yüzden `free` kayıtlar yayın kontrolünde hata verir.

Yeni dosya eklediğinde ya da bir dosyayı değiştirdiğinde:

```
python -P tools/check_provenance.py --sync   # yeni dosyalara boş kayıt ekler, değişenlerin özetini yeniler
```

Sonra `provenance.json` içinde kaydı doldur ve ancak hakkından emin olunca `status` değerini `final` yap. Değişen bir dosya, kaydı gözden geçirilene kadar tekrar `placeholder` olur.

```
python -P tools/check_provenance.py            # yapı kontrolü; yer tutucuları uyarı olarak listeler
python -P tools/check_provenance.py --release  # yayına hazır olmayan her şeyde hata verir
```

Kontrol her pull request'te GitHub Actions ile çalışır. Yayın öncesi `--release` ile çalıştırılır ve sıfır hata vermelidir.

## Yeni meditasyon ya da blog yazısı ekleme

`meditations` ya da `blogPosts` listesine yeni bir öğe ekle. `id` benzersiz olmalı, küçük harf ve tire kullan (örn. `body-scan`).

- **Meditasyon:** `label` kartın üstündeki kısa yazı, `title` detay ekranındaki başlık, `audio` play butonuyla çalan ses (OGG, MP3, M4A ya da WAV). `audio` yazılmazsa play butonu pasif görünür.
  - `description` (isteğe bağlı): başlığın altında görünen kısa açıklama, en çok iki satır. Hem detay ekranında hem ana sayfadaki öneri kartında çıkar. Yazılmazsa hiçbir şey gösterilmez.
  - `breathing` (isteğe bağlı): `true` ise meditasyonda nefes ritmi seçici (Sakin, 4-7-8, Kutu) gösterilir. Yalnızca nefes meditasyonu için kullan.
- **Blog:** `title` kartta görünen başlık.
- **Ana sayfa:** `home.featuredPosts` ana sayfada gösterilecek iki blog yazısının `id`'leri. `home.banner` ana sayfadaki büyük görsel.

## Blog yazısı yazma

Her yazı `posts/` klasöründe bir Markdown dosyasıdır ve `content.json` içinde ilgili yazının `body` alanından bağlanır. İki dilli yazarken her dil için ayrı dosya yaz: `posts/body-scan.md` Türkçe, `posts/body-scan.en.md` İngilizce (örn. `"body": { "tr": "posts/body-scan.md", "en": "posts/body-scan.en.md" }`). `body` yazılmazsa uygulama "This post is coming soon." gösterir.

Başlık ve görsel `content.json`'dan gelir, dosyaya tekrar yazma. Desteklenen biçimler:

```markdown
Paragraflar arasında bir boş satır bırak.

## Bölüm başlığı (mor, italik)
### Alt başlık

**kalın**, *italik*, [bağlantı metni](https://...)

- madde işaretli liste
1. numaralı liste

## Sources
1. [Kaynağın adı](https://...)
```

Tablo, görsel ve alıntı bloğu (`>`) desteklenmez; düz metin olarak görünür. Bir yazıyı güncellemek için dosyayı değiştirmen yeterli, ad değiştirmene gerek yok.

JSON'da bir virgül ya da tırnak hatası olursa uygulama dosyayı yok sayar ve bir önceki içeriği göstermeye devam eder. Göndermeden önce [jsonlint.com](https://jsonlint.com) ile kontrol edebilirsin.

## Gizlilik politikası

`docs/index.html` uygulamanın gizlilik politikasıdır (tr + en, tek sayfa). GitHub Pages `main` dalının `/docs` klasöründen yayınlar: https://azraclk.github.io/serin-content/. Uygulama bir veri toplamaya ya da yeni bir izin istemeye başlarsa bu sayfayı da güncelle.

## Blog görselleri

`images/blog/*.webp` bir görüntü modeliyle değil, `tools/images/blog_visuals.py` ile kodla çizilir (160x80 piksel ızgarası, 10 kat büyütülmüş). Yeniden üretmek için: `pip install pillow numpy`, sonra `python -P tools/images/blog_visuals.py`. Çıktı dosyalarla bayt bayt aynıdır. Bir görseli değiştirirsen yeni bir dosya adı kullan (uygulama görselleri adına göre önbelleğe alır) ve `check_provenance.py --sync` çalıştır.

## Ses kartı görselleri

`images/meditations/*.webp` de kodla çizilir: `tools/images/card_visuals.py` (128x128 piksel ızgarası, 8 kat büyütülmüş, 1024x1024). `blog_visuals.py`'nin yardımcılarını kullanır. `python -P tools/images/card_visuals.py --preview` önizleme sayfası da yazar (hero, dikey kart ve daire kırpımlarını gösterir). Konu ortadaki ~86x72'lik alanda kalmalı; kenarlar kırpılıyor.
