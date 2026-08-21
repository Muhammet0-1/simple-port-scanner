# Güvenlik Politikası

## Desteklenen sürümler

| Sürüm | Destek |
| --- | --- |
| 1.x | Evet |
| < 1.0 | Hayır |

## Güvenlik açığı bildirimi

Hassas bir güvenlik açığını herkese açık issue olarak yayımlamayın. GitHub deposundaki **Security →
Report a vulnerability** seçeneğini kullanın. Bu seçenek kullanılamıyorsa, yalnızca yeniden üretim
için gerekli en az bilgiyi içeren özel bir iletişim kanalı talep edin.

Bildirimde şunları paylaşın:

- Etkilenen sürüm veya commit
- Güvenli ve en küçük yeniden üretim adımları
- Beklenen ve gözlenen davranış
- Olası etki ve önerilen çözüm

Gerçek üçüncü taraf hedeflerini taramayın ve kullanıcı verisi, kimlik bilgisi, exploit çıktısı veya
zararlı payload eklemeyin.

## Güvenlik sınırı

Bu proje bir TCP bağlantı gözlem aracıdır; erişim kontrolü veya saldırı önleme sistemi değildir.
Yetkilendirme onay bayrakları operatör hatasını azaltır ancak teknik veya hukuki izin sağlamaz.
DNS yanıtları tarama öncesinde sabitlenir; buna rağmen DNS sahibi, ağ yolu ve hedef hizmetler tarama
sırasında değişebilir.

Bir portun `open`, `closed` veya `filtered` olarak raporlanması tek başına güvenlik açığı anlamına
gelmez. Banner içeriği güvenilmeyen girdidir ve yalnızca bilgi amaçlıdır.

## Operatör sorumluluğu

Taramadan önce hedefi, port kapsamını, zaman aralığını, hız sınırını ve veri saklama politikasını
yetki belgenizle karşılaştırın. Public hedef seçeneğini yalnızca açık izniniz varsa kullanın.
