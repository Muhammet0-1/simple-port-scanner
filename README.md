# Simple Port Scanner

[![CI](https://github.com/Muhammet0-1/simple-port-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/Muhammet0-1/simple-port-scanner/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10--3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Simple Port Scanner, sahibi olduğunuz veya açıkça test izni aldığınız sistemler için hazırlanmış,
sınırlı kaynak kullanan bir TCP connect tarayıcısıdır. Ham paket, SYN stealth, UDP taraması,
kimlik doğrulama denemesi, güvenlik kontrolü atlatma veya exploit özelliği içermez.

## Güvenlik yaklaşımı

- Her çalıştırmada `--acknowledge-authorization` ile yetki onayı gerekir.
- Public IP'ler varsayılan olarak reddedilir ve ayrıca `--allow-public-target` ister.
- 1024'ten fazla port varsayılan olarak reddedilir ve ayrıca `--allow-large-scan` ister.
- Eşzamanlı bağlantı sayısı 256 ile, DNS sonucu sayısı 8 ile sınırlandırılmıştır.
- Hedef DNS'i tarama başlamadan bir kez çözülür; sonuçlar tarama boyunca sabit tutulur.
- Banner alma kapalıdır. Açıldığında veri gönderilmez, yalnızca sınırlı sayıda bayt geçici olarak
  alınır; kontrol karakterleri terminal çıktısından temizlenir.
- Raporlar yalnızca standart çıktıya yazılır. Dosya yolu güvenliği ve sahipliği kabuğun yönlendirme
  kurallarına bırakılmaz; gerektiğinde kullanıcı bilinçli biçimde `>` ile yönlendirir.

Bu kontroller yetkilendirmenin yerine geçmez. Bir hedefin teknik olarak erişilebilir olması tarama
izni bulunduğu anlamına gelmez.

## Kurulum

Python 3.10 veya üzeri gerekir. Çalışma zamanında üçüncü taraf bağımlılık yoktur.

```bash
git clone https://github.com/Muhammet0-1/simple-port-scanner.git
cd simple-port-scanner
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Kullanım

Yerel veya özel ağdaki yetkili bir hedefte birkaç portu kontrol etme:

```bash
simple-port-scanner \
  --target 127.0.0.1 \
  --ports 22,80,443,8000-8010 \
  --acknowledge-authorization
```

Globally routable bir hedef için, yalnızca yazılı veya açık test yetkiniz varsa:

```bash
simple-port-scanner \
  --target authorized.example \
  --ports 80,443 \
  --acknowledge-authorization \
  --allow-public-target
```

Kapalı ve filtrelenmiş sonuçları da metin çıktısında gösterme:

```bash
simple-port-scanner \
  --target 192.0.2.10 \
  --ports 1-100 \
  --acknowledge-authorization \
  --show-all
```

> `192.0.2.0/24` belgelerde örnekleme için ayrılmış TEST-NET-1 bloğudur. Komutu gerçek bir hedefe
> uyarlamadan önce kapsam ve yetkinizi doğrulayın.

### Banner alma

Banner seçeneği yalnızca bağlantı sonrasında servisin kendiliğinden gönderdiği sınırlı veriyi alır;
uygulama protokolüne veri göndermez.

```bash
simple-port-scanner \
  --target 127.0.0.1 \
  --ports 22 \
  --acknowledge-authorization \
  --banner \
  --banner-bytes 128
```

Scapy veya paket yakalama kullanılmasa da banner etkinleştirildiğinde uygulama verisi kısa süreliğine
işlem belleğine alınabilir ve istenirse rapora eklenir. Hassas ortamlarda banner seçeneğini kapalı
tutun.

### Makine tarafından okunabilir çıktı

```bash
simple-port-scanner \
  --target 127.0.0.1 \
  --ports 22,80,443 \
  --acknowledge-authorization \
  --format json > scan.json

simple-port-scanner \
  --target 127.0.0.1 \
  --ports 22,80,443 \
  --acknowledge-authorization \
  --format jsonl > scan.jsonl
```

JSON şeması `schema_version: 1` ile sürümlenir. Sonuçlar IP sürümü, adres ve port sırasına göre
deterministik olarak sıralanır.

## Port durumları

| Durum | Anlamı |
| --- | --- |
| `open` | TCP bağlantısı başarıyla kuruldu. |
| `closed` | İşletim sistemi bağlantıyı açıkça reddetti. |
| `filtered` | Zaman aşımı, erişim engeli veya ağ erişilemezliği gözlendi. |
| `error` | Diğer bir soket hata kodu oluştu. |

Bu sınıflandırma bir güvenlik duvarının kesin yapılandırmasını kanıtlamaz. Ağ cihazları ve işletim
sistemleri aynı durumu farklı hata kodlarıyla ifade edebilir.

## Mimari

```text
CLI -> doğrulanmış yapılandırma -> tek seferlik DNS çözümü
    -> sınırlı ThreadPoolExecutor -> TCP connect probe
    -> deterministik text / JSON / JSONL raporu
```

Görev üretimi bütün taramayı belleğe yüklemez. En fazla eşzamanlılık değerinin iki katı görev aynı
anda beklemede tutulur. Soketler `finally` bloğunda kapatılır ve beklenmeyen worker hataları başarılı
sonuç gibi gösterilmez.

## Kapsam dışı özellikler

- UDP, raw socket veya SYN taraması
- Stealth, parçalama, kaynak adresi taklidi veya IDS/WAF atlatma
- CIDR, subnet veya hedef listesi taraması
- Parola denemesi, exploit veya güvenlik açığı doğrulama
- Otomatik servis etkileşimi ya da payload gönderimi

## Geliştirme

```bash
python -m pip install -e '.[dev]'
ruff check .
mypy
pytest
python -m compileall -q src tests scanner.py
python -m build
```

Testler sahte resolver ve soket nesneleri kullanır; gerçek DNS isteği veya ağ bağlantısı başlatmaz.
GitHub Actions, Python 3.10–3.13 sürümlerinde lint, strict type check, test, derleme ve kurulmuş wheel
üzerinden CLI smoke kontrolü çalıştırır.

## Sorumlu kullanım

Yalnızca sahibi olduğunuz veya açık test izni aldığınız sistemlerde kullanın. Kurumsal politika,
sözleşme, bug bounty scope'u ve yerel mevzuat teknik seçeneklerden önce gelir. Ayrıntılar için
[SECURITY.md](SECURITY.md) dosyasına bakın.

## Lisans

[MIT](LICENSE) © 2026 Muhammet0-1
