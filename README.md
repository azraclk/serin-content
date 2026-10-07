# serin-content

Serin uygulamasının içeriği. Uygulama `content.json` dosyasını ve görselleri buradan okur. Bu repoya gönderilen değişiklikler, uygulama güncellenmeden kullanıcılara ulaşır.

## Nasıl çalışır

- Uygulama her açılışta `content.json` dosyasını indirir ve son başarılı sürümü telefonda saklar.
- `image` alanları bu repodaki dosya yollarıdır (örn. `images/meditations/sleep.jpg`).
- İnternet yoksa uygulama en son indirdiği içeriği gösterir. Hiç indirmemişse kendi içindeki varsayılan görselleri gösterir.
- GitHub dosyaları yaklaşık 5 dakika önbellekte tuttuğu için değişikliklerin görünmesi birkaç dakika sürebilir.

## Görsel değiştirme

Uygulama indirdiği görselleri **dosya adına göre** önbellekte saklar. Aynı adla yeni bir görsel yüklersen telefonlar eskisini göstermeye devam eder. Bu yüzden:

1. Yeni görseli **farklı bir adla** ekle (örn. `images/meditations/sleep-2.jpg`).
2. `content.json` içinde ilgili `image` alanını bu yeni adla güncelle.
3. İstersen eski dosyayı sil.

Görseller kartlarda ortadan kırpılır. Meditasyon görselleri kare (en az 900×900 px), ana sayfa banner'ı yaklaşık 2.4:1 oranında olmalı.

## Yeni meditasyon ya da blog yazısı ekleme

`meditations` ya da `blogPosts` listesine yeni bir öğe ekle. `id` benzersiz olmalı, küçük harf ve tire kullan (örn. `body-scan`).

- **Meditasyon:** `label` kartın üstündeki kısa yazı, `title` detay ekranındaki başlık.
- **Blog:** `title` kartta görünen başlık.
- **Ana sayfa:** `home.featuredPosts` ana sayfada gösterilecek iki blog yazısının `id`'leri. `home.banner` ana sayfadaki büyük görsel.

JSON'da bir virgül ya da tırnak hatası olursa uygulama dosyayı yok sayar ve bir önceki içeriği göstermeye devam eder. Göndermeden önce [jsonlint.com](https://jsonlint.com) ile kontrol edebilirsin.
