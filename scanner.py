import socket

hedef = input("Hedef IP adresini girin: ")
for port in range(1, 100):
    soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soket.settimeout(1)
    sonuc = soket.connect_ex((hedef, port))
    if sonuc == 0:
        print(f"[+] Port {port} açık")
    soket.close()
