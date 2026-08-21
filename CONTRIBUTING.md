# Katkıda bulunma

Katkılar güvenli, açıkça yetkilendirilmiş TCP connect taraması kapsamını korumalıdır.

## Geliştirme ortamı

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Pull request açmadan önce:

```bash
ruff check .
mypy
pytest
python -m compileall -q src tests scanner.py
python -m build
```

## Katkı ilkeleri

- Davranış değişikliklerine ağsız ve deterministik test ekleyin.
- Gerçek internet hedeflerini, kullanıcı verilerini veya gizli bilgileri fixture olarak eklemeyin.
- Testlerde sahte resolver ve socket nesneleri kullanın.
- Public API ve CLI değişikliklerini README ile CHANGELOG içinde açıklayın.
- Hataları sessizce yutmayın; kullanıcıya güvenli ve eyleme dönük mesaj gösterin.
- Bağımlılık eklemeden önce standart kütüphanenin yeterli olup olmadığını değerlendirin.

Stealth, IDS/WAF atlatma, kaynak adresi taklidi, parola denemesi, exploit, toplu hedef/CIDR taraması
ve izinsiz kullanımı kolaylaştıran değişiklikler proje kapsamı dışındadır.

## Commit ve PR

Küçük, odaklı commit'ler kullanın. PR açıklamasında değişikliğin amacı, güvenlik etkisi ve çalıştırılan
doğrulamaları belirtin. Güvenlik açığı bildirmek için herkese açık issue yerine
[SECURITY.md](SECURITY.md) sürecini kullanın.
