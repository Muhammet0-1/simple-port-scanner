# 🛡️ Advanced Multi-Threaded Port Scanner

Bu proje, Python'un `socket` ve `threading` kütüphaneleri kullanılarak geliştirilmiş, yüksek performanslı bir ağ tarama aracıdır. Sıradan tarayıcıların aksine, **Producer-Consumer** tasarım desenini kullanarak hedef sistemi çoklu iş parçacıklarıyla (multi-threading) tarar.

## 🚀 Özellikler

* **Multi-Threading:** Varsayılan olarak 100 iş parçacığı (thread) ile aynı anda tarama yapar.
* **Queue & Lock Mekanizması:** Veri yarışını (race condition) önlemek için `threading.Lock` ve `queue` yapısı kullanır.
* **Banner Grabbing:** Açık portlarda çalışan servislerin versiyon bilgilerini (banner) çekmeye çalışır.
* **Socket Management:** Timeout yönetimi ile takılı kalan bağlantıları engeller.

## 🛠️ Kurulum ve Kullanım

Projeyi klonlayın ve doğrudan çalıştırın. Herhangi bir harici kütüphane gerektirmez (Standart kütüphaneler kullanılır).

```bash
git clone [https://github.com/Muhammet0-1/simple-port-scanner.git](https://github.com/Muhammet0-1/simple-port-scanner.git)
cd simple-port-scanner
python3 scanner.py

⚙️ Nasıl Çalışır?

 1)  Hedef Belirleme: Kullanıcıdan IP/Hostname ve port aralığı alınır.

 2)  Havuz Oluşturma: Belirlenen sayıda (default: 100) iş parçacığı oluşturulur ve daemon olarak başlatılır.

 3)  Kuyruğa Ekleme: Taranacak portlar bir Queue yapısına eklenir.

  4) Tarama: Boştaki iş parçacıkları kuyruktan port çeker, tarar ve sonucu ekrana thread-safe (güvenli) bir şekilde yazar.

⚠️ Yasal Uyarı

Bu araç sadece eğitim ve test amaçlı geliştirilmiştir. İzni olmayan ağlarda kullanılması yasa dışıdır. Geliştirici, oluşabilecek zararlardan sorumlu değildir.
