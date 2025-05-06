# Temel TCP Port Tarayıcı (Çoklu İş Parçacığı Destekli ve Basit Banner Tespiti)

import socket
import sys
import threading
from queue import Queue # İş parçacıkları arasında veri paylaşımı için kuyruk yapısı

# Çoklu iş parçacığı için kuyruk ve kilit nesneleri
print_lock = threading.Lock() # Konsola yazdırma işlemleri için kilit
q = Queue() # Taranacak portları tutacak kuyruk

#-------------------------------------------------------------------------------
# Port Tarama İşini Yapan Fonksiyon (Her İş Parçacığı Bu Fonksiyonu Çalıştırır)
#-------------------------------------------------------------------------------
def portscan(port):
    """Belirtilen portu tarar ve açık ise bilgi yazdırır."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP soketi oluştur
    s.settimeout(1) # Bağlantı zaman aşımı (1 saniye)

    try:
        # Hedefe belirtilen porta bağlanmayı dene
        conn = s.connect_ex((target, port))

        if conn == 0: # Bağlantı başarılı ise (port açık)
            service = "Bilinmiyor"
            try:
                # Basit banner (servis bilgisi) almaya çalış
                # Alma işlemi için daha kısa bir timeout belirlemek iyi olabilir
                s.settimeout(0.5)
                banner = s.recv(1024).decode().strip()
                # Banner'dan servis bilgisini çıkar (çok temel bir yaklaşım)
                # Bu kısım servise göre çok değişir, genel bir banner almak daha kolaydır
                if banner:
                    service = f"Servis: {banner[:50]}..." # İlk 50 karakteri al
                else:
                     service = "Servis: Yanıt Yok"

            except socket.timeout:
                 service = "Servis: Zaman Aşımı (Banner)"
            except Exception as e:
                service = f"Servis: Hata ({e})" # Banner alırken oluşan diğer hatalar

            # Açık port bilgisini güvenli bir şekilde yazdır
            with print_lock:
                print(f"[+] Port {port} açık - {service}")

        #else: # Bağlantı başarısız ise (port kapalı veya filtrelenmiş)
            # Kapalı portları yazdırmak istemiyorsak bu kısmı boş bırakırız
            # with print_lock:
            #     print(f"[-] Port {port} kapalı veya filtrelenmiş.")

    except socket.gaierror:
        # Geçersiz ana bilgisayar adı/IP adresi hatası
        with print_lock:
            print(f"[-] Ana bilgisayar adı çözümlenemedi.")
            sys.exit() # Hata durumunda çık
    except socket.error as e:
        # Diğer soket hataları
        with print_lock:
             # print(f"[-] Port {port} taranırken hata oluştu: {e}") # Çok fazla çıktı olabilir
             pass # Hata durumunda bir şey yazdırma
    finally:
        s.close() # Soketi kapat

#-------------------------------------------------------------------------------
# İş Parçacığı İşleyicisi
# Kuyruktan portları alıp portscan fonksiyonunu çağıran döngü
#-------------------------------------------------------------------------------
def worker():
    """Kuyruktan port alır ve tarar, kuyruğa tamamlandığını bildirir."""
    while True:
        port = q.get() # Kuyruktan bir port numarası al (bloklar eğer kuyruk boşsa)
        portscan(port) # Port tarama fonksiyonunu çağır
        q.task_done() # Kuyruğa bu portun işlendiğini bildir

#-------------------------------------------------------------------------------
# Ana Program Başlangıcı
# Hedef ve port aralığını al, iş parçacıklarını başlat, portları kuyruğa ekle
#-------------------------------------------------------------------------------
print("-" * 60)
print("Basit Çoklu İş Parçacıklı TCP Port Tarayıcı")
print("-" * 60)

# Hedef IP veya ana bilgisayar adını al
target_input = input("Hedef IP adresi veya ana bilgisayar adını girin: ")

# Hedef adı/IP'yi çözmeye çalış (geçersizse hata verir)
try:
    target = socket.gethostbyname(target_input)
    print(f"Hedef: {target} taranıyor...")
except socket.gaierror:
    print("[-] Ana bilgisayar adı çözümlenemedi veya geçersiz IP adresi.")
    sys.exit() # Hata durumunda betikten çık

# Taranacak port aralığını al
try:
    start_port = int(input("Başlangıç portunu girin: "))
    end_port = int(input("Bitiş portunu girin: "))
    if start_port <= 0 or end_port <= 0 or start_port > end_port or end_port > 65535:
         print("[-] Geçersiz port aralığı. Portlar 1-65535 arasında olmalı ve başlangıç bitişten küçük veya eşit olmalı.")
         sys.exit()

except ValueError:
    print("[-] Geçersiz giriş. Port numaraları sayı olmalı.")
    sys.exit()


# Kaç tane iş parçacığı kullanacağımızı belirle (örn: 100 veya 200 yaygın değerlerdir)
num_threads = 100 # Ayarlanabilir iş parçacığı sayısı

# İş parçacıklarını oluştur ve başlat
# Her iş parçacığı 'worker' fonksiyonunu çalıştıracak
for i in range(num_threads):
    thread = threading.Thread(target=worker, daemon=True) # Daemon=True: Ana program çıkarsa iş parçacıkları da çıkar
    thread.start() # İş parçacığını başlat

# Taranacak portları kuyruğa ekle
# range(başlangıç, bitiş + 1) bitiş portunu dahil etmek için
for port in range(start_port, end_port + 1):
    q.put(port) # Port numarasını kuyruğa ekle

# Kuyruktaki tüm görevler tamamlanana kadar bekle
q.join() # Tüm portlar taranana kadar ana iş parçacığını burada bekletir

print("-" * 60)
print(f"Hedef {target} için tarama tamamlandı.")
print("-" * 60)
