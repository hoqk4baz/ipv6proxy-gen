import os
import subprocess
import random
import string
import requests
import shutil

# Kullanıcı bilgileri ve portlar
KULLANICI = "tarak"
SIFRE = "kurek"
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110
YOL = "/home/CentOS_Proxi_Yukle"
VERI = f"{YOL}/veri.txt"

# Rastgele şifre oluşturma
def rastgele():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

# IPv6 adresi oluşturma
def ipv6_olustur(ip6_subnet):
    ipv6_segments = [f"{random.choice('0123456789abcdef')}{random.choice('0123456789abcdef')}" for _ in range(4)]
    return f"{ip6_subnet}:{':'.join(ipv6_segments)}"

# 3Proxy yükleme
def yukle_3proxy():
    print("3Proxy Yükleniyor...")
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    subprocess.run(["wget", "-qO-", url], stdout=subprocess.PIPE)
    subprocess.run(["bsdtar", "-xvf-", "3proxy-3proxy-0.8.6.tar.gz"])
    os.chdir("3proxy-3proxy-0.8.6")
    subprocess.run(["make", "-f", "Makefile.Linux"])
    os.makedirs("/usr/local/etc/3proxy/bin", exist_ok=True)
    shutil.copy("src/3proxy", "/usr/local/etc/3proxy/bin/")
    shutil.copy("./scripts/rc.d/proxy.sh", "/etc/init.d/3proxy")
    os.chmod("/etc/init.d/3proxy", 0o755)
    subprocess.run(["chkconfig", "3proxy", "on"])
    os.chdir("..")
    shutil.rmtree("3proxy-3proxy-0.8.6")

# Veriyi oluşturma
def veri_olustur(ip4, ip6_subnet, adet):
    with open(VERI, "w") as f:
        for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + adet):
            ip6_address = ipv6_olustur(ip6_subnet)
            f.write(f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{ip4}/{port}/{ip6_address}\n")

# iptables yapılandırma
def iptable_olustur():
    with open(f"{YOL}/iptable_yapilandir.sh", "w") as f:
        with open(VERI, "r") as veri_file:
            for line in veri_file:
                port = line.split("/")[3]
                f.write(f"iptables -I INPUT -p tcp --dport {port} -m state --state NEW -j ACCEPT\n")

# ifconfig yapılandırma
def ifconfig_olustur():
    with open(f"{YOL}/ifconfig_yapilandir.sh", "w") as f:
        with open(VERI, "r") as veri_file:
            for line in veri_file:
                ipv6 = line.split("/")[4].strip()
                f.write(f"ifconfig eth0 inet6 add {ipv6}/64\n")

# 3Proxy config oluşturma
def config_3proxy():
    with open("/usr/local/etc/3proxy/3proxy.cfg", "w") as f:
        f.write("daemon\nmaxconn 1000\nnscache 65536\ntimeouts 1 5 30 60 180 1800 15 60\n")
        f.write("setgid 65535\nsetuid 65535\nflush\nauth strong\n\n")
        f.write(f"users {KULLANICI}:CL:{SIFRE}\n\n")
        with open(VERI, "r") as veri_file:
            for line in veri_file:
                parts = line.strip().split("/")
                f.write(f"auth strong\nallow {parts[0]}\n")
                f.write(f"proxy -6 -n -a -p{parts[3]} -i{parts[2]} -e{parts[4]}\nflush\n\n")

# Proxy listesini oluşturma
def proxy_txt():
    with open("proxy.txt", "w") as f:
        with open(VERI, "r") as veri_file:
            for line in veri_file:
                parts = line.strip().split("/")
                f.write(f"{parts[2]}:{parts[3]}:{parts[0]}:{parts[1]}\n")

# İndirme linkini oluşturma
def file_io_yukle():
    print("Zip Dosyası Oluşturuluyor...")
    zip_password = rastgele()
    subprocess.run(["zip", "--password", zip_password, "proxy.zip", "proxy.txt"])
    with open("proxy.zip", "rb") as f:
        response = requests.post("https://file.io", files={"file": f})
    url = response.json().get("link", "")
    print(f"Proxyler hazır! İndirme Bağlantısı: {url}")
    print(f"Zip Şifresi: {zip_password}")

# Ana işlemler
def main():
    os.makedirs(YOL, exist_ok=True)
    ip4 = subprocess.getoutput("curl -4 -s icanhazip.com")
    ip6_subnet = subprocess.getoutput("curl -6 -s icanhazip.com | cut -f1-4 -d':'")
    adet = int(input("Kaç adet IPv6 proxy oluşturmak istiyorsunuz? (Örnek 500): "))

    yukle_3proxy()
    veri_olustur(ip4, ip6_subnet, adet)
    iptable_olustur()
    ifconfig_olustur()
    config_3proxy()
    proxy_txt()
    file_io_yukle()

if __name__ == "__main__":
    main()
