import os
import random
import string
import subprocess
import requests
import zipfile

# Kullanıcı ve şifre bilgileri
KULLANICI = "tarak"
SIFRE = "kurek"
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110
YOL = "/home/CentOS_Proxi_Yukle"
VERI = os.path.join(YOL, "veri.txt")

# Renk ayarları
renkreset = '\033[0m'
yesil = '\033[1;92m'
sari = '\033[1;93m'
kirmizi = '\033[1;91m'
mor = '\033[0;35m'

def rastgele():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def ipv6_olustur():
    ipv6_k = '0123456789abcdef'
    return f"{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}"

def veri_olustur(adet):
    with open(VERI, "w") as f:
        for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + adet):
            f.write(f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{IP4}/{port}/{ipv6_olustur()}\n")

def iptable_olustur():
    with open(os.path.join(YOL, "iptable_yapilandir.sh"), "w") as f:
        for line in open(VERI):
            parts = line.strip().split("/")
            f.write(f"iptables -I INPUT -p tcp --dport {parts[3]} -m state --state NEW -j ACCEPT\n")

def ifconfig_olustur():
    with open(os.path.join(YOL, "ifconfig_yapilandir.sh"), "w") as f:
        for line in open(VERI):
            parts = line.strip().split("/")
            f.write(f"ifconfig eth0 inet6 add {parts[4]}/64\n")

def config_3proxy():
    config_lines = [
        "daemon",
        "maxconn 1000",
        "nscache 65536",
        "timeouts 1 5 30 60 180 1800 15 60",
        "setgid 65535",
        "setuid 65535",
        "flush",
        "auth strong",
        f"users {' '.join(f'{line.split('/')[0]}:CL:{line.split('/')[1]}' for line in open(VERI))}",
    ]
    for line in open(VERI):
        parts = line.strip().split("/")
        config_lines.append(f"auth strong\nallow {parts[0]}\nproxy -6 -n -a -p{parts[3]} -i{IP4} -e{parts[4]}\nflush\n")
    with open("/usr/local/etc/3proxy/3proxy.cfg", "w") as f:
        f.write("\n".join(config_lines))

def yukle_3proxy():
    print(f"\n\n\t{yesil}3Proxy Yükleniyor..\n{renkreset}\n")
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    subprocess.run(["wget", "-qO-", url], stdout=subprocess.PIPE, check=True).stdout
    subprocess.run(["bsdtar", "-xvf-", "-"], input=url, check=True)
    os.chdir("3proxy-3proxy-0.8.6")
    subprocess.run(["make", "-f", "Makefile.Linux"], check=True)
    os.makedirs("/usr/local/etc/3proxy/{bin,logs,stat}", exist_ok=True)
    subprocess.run(["cp", "-f", "src/3proxy", "/usr/local/etc/3proxy/bin/"], check=True)
    subprocess.run(["cp", "-f", "./scripts/rc.d/proxy.sh", "/etc/init.d/3proxy"], check=True)
    subprocess.run(["chmod", "+x", "/etc/init.d/3proxy"], check=True)
    subprocess.run(["chkconfig", "3proxy", "on"], check=True)
    os.chdir("..")
    subprocess.run(["rm", "-rf", "3proxy-3proxy-0.8.6"], check=True)

def zip_yukle():
    print(f"\n\n\t{yesil}Zip Yükleniyor..\n{renkreset}\n")
    password = rastgele()
    with zipfile.ZipFile("proxy.zip", "w") as zipf:
        zipf.setpassword(password.encode())
        zipf.write("proxy.txt")
    response = requests.post("https://file.io", files={"file": open("proxy.zip", "rb")})
    url = response.json().get("link")
    print(f"\n\n\t{yesil}Proxyler Hazır!{mor} Format »{sari} IP:PORT:KULLANICI:SIFRE{renkreset}")
    print(f"\n{mor}IPv6 Zip İndirme Bağlantısı:{yesil} {url}{renkreset}")
    print(f"{mor}IPv6 Zip Şifresi:{yesil} {password}{renkreset}")

def main():
    global IP4
    IP4 = os.popen("curl -4 -s icanhazip.com").read().strip()
    
    # IPv6 kontrolü
    try:
        IP6 = os.popen("curl -6 -s icanhazip.com | cut -f1-4 -d':'").read().strip()
    except requests.RequestException:
        IP6 = None

    print(f"\n\t{sari}IPv4 »{yesil} {IP4}{sari} | IPv6 için Sub »{yesil} {IP6 if IP6 else 'Bulunamadı'}{renkreset}")
    
    # Gerekli paketlerin yüklenmesi
    subprocess.run(["yum", "-y", "install", "gcc", "net-tools", "bsdtar", "zip"], check=True)

    if not IP6:
        print(f"\n\n\t{kirmizi}Makinenizin IPv6 Desteği Bulunmamaktadır..{renkreset}\n")
        print(f"\n{sari}IPv4   Proxy »{yesil} {IP4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}{renkreset}")
        print(f"{sari}SOCKS5 Proxy »{yesil} {IP4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}{renkreset}\n")
        return

    os.makedirs(YOL, exist_ok=True)
    os.chdir(YOL)

    adet = int(input(f"\n\n\t{mor}Kaç adet IPv6 proxy oluşturmak istiyorsunuz?{kirmizi} Örnek 500 : {renkreset}"))
    veri_olustur(adet)
    iptable_olustur()
    ifconfig_olustur()
    config_3proxy()

    # rc.local dosyasına ekleme
    with open("/etc/rc.local", "a") as f:
        f.write(f"bash {os.path.join(YOL, 'iptable_yapilandir.sh')} >/dev/null\n")
        f.write(f"bash {os.path.join(YOL, 'ifconfig_yapilandir.sh')} >/dev/null\n")
        f.write("ulimit -n 10048\n")
        f.write("service 3proxy start\n")

    subprocess.run(["bash", "/etc/rc.local"], check=True)
    
    yukle_3proxy()
    zip_yukle()

    print(f"\n{sari}IPv4   Proxy »{yesil} {IP4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}{renkreset}")
    print(f"{sari}SOCKS5 Proxy »{yesil} {IP4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}{renkreset}\n")

if __name__ == "__main__":
    main()
