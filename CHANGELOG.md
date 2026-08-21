# Changelog

Bu proje [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) biçimini ve
[Semantic Versioning](https://semver.org/) yaklaşımını izler.

## [Unreleased]

## [1.0.0] - 2026-08-20

### Added

- Kurulabilir `src` tabanlı Python paketi ve `simple-port-scanner` CLI komutu.
- Tek hedefli, IPv4/IPv6 uyumlu ve sınırlı TCP connect tarama motoru.
- Public hedef, büyük port aralığı ve genel yetkilendirme için açık onay bayrakları.
- Tek seferlik DNS çözümü, adres sabitleme ve DNS sonucu sınırı.
- Varsayılan olarak kapalı, pasif ve boyutu sınırlı banner alma.
- Sürümlü JSON ve JSONL raporları.
- Sahte soket/resolver kullanan ağsız test paketi.
- Ruff, strict mypy, pytest, build ve wheel smoke kontrolleri içeren CI matrisi.
- MIT lisansı, katkı rehberi ve güvenlik politikası.

### Changed

- Global kuyruk, sabit 100 daemon thread ve import sırasında çalışan etkileşimli kod kaldırıldı.
- Soket hatalarının sessizce yutulması yerine açık ve sınırlı durum sınıflandırması getirildi.
- Eski `scanner.py`, paketlenmiş CLI için uyumluluk giriş noktası hâline getirildi.

[Unreleased]: https://github.com/Muhammet0-1/simple-port-scanner/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Muhammet0-1/simple-port-scanner/releases/tag/v1.0.0
