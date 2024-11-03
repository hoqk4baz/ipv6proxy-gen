import os
import shutil
import requests
import zipfile
import random
import subprocess

KULLANICI = "tarak"
SIFRE = "kurek"
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110

# Renk Tanımları
renkreset = '\033[0m'
yesil = '\033[1;92m'
kirmizi = '\033[1;91m'
sari = '\033[1;93m'
mor = '\033[0;35m'

def rastgele():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=5))

def ipv6_olustur():
    ipv6_k = '0123456789abcdef'
    return ':'.join(''.join(random.choices(ipv6_k, k=4)) for _ in range(4))

def veri_olustur(adet):
    with open('veri.txt', 'w') as f:
        for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + adet):
            f.write(f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{IP4}/{port}/{ipv6_olustur()}\n")

def iptable_olustur():
    with open('iptable_yapilandir.sh', 'w') as f:
        for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + 500):  # 500 proxy için örnek
            f.write(f"iptables -I INPUT -p tcp --dport {port} -m state --state NEW -j ACCEPT\n")

def ifconfig_olustur():
    return f"ifconfig eth0 inet {IP4}/24"

def config_3proxy():
    with open('/usr/local/etc/3proxy/3proxy.cfg', 'w') as f:
        f.write("daemon\n")
        f.write("maxconn 1000\n")
        f.write("nscache 65536\n")
        f.write("timeouts 1 5 30 60 180 1800 15 60\n")
        f.write("setgid 65535\n")
        f.write("setuid 65535\n")
        f.write("flush\n")
        f.write("auth strong\n")
        f.write("users {0}:{1}\n".format(KULLANICI, SIFRE))

def yukle_3proxy():
    print("\n\n\t{}3Proxy Yükleniyor..{}".format(yesil, renkreset))
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    os.system(f"wget -qO- {url} | tar -zxvf -")  # -z bayrağı eklendi
    os.chdir("3proxy-3proxy-0.8.6")
    os.system("make -f Makefile.Linux")
    os.makedirs("/usr/local/etc/3proxy/bin", exist_ok=True)
    os.system("cp -f src/3proxy /usr/local/etc/3proxy/bin/")
    os.system("cp -f ./scripts/rc.d/proxy.sh /etc/init.d/3proxy")
    os.system("chmod +x /etc/init.d/3proxy")
    os.system("chkconfig 3proxy on")
    os.chdir("..")
    os.system("rm -rf 3proxy-3proxy-0.8.6")

def squid_yukle():
    print("\n\n\t{}Squid Yükleniyor..{}".format(yesil, renkreset))
    os.system("yum install nano dos2unix squid httpd-tools -y")
    os.system(f"htpasswd -bc /etc/squid/passwd {KULLANICI} {SIFRE}")
    with open('/etc/squid/squid.conf', 'w') as f:
        f.write("auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/passwd\n")
        f.write("auth_param basic realm proxy\n")
        f.write("acl authenticated proxy_auth REQUIRED\n")
        f.write("http_access allow authenticated\n")
        f.write(f"http_port 0.0.0.0:{IPV4_PORT}\n")
        f.write("http_access deny all\n")
    os.system("systemctl restart squid.service && systemctl enable squid.service")
    os.system(f"iptables -I INPUT -p tcp --dport {IPV4_PORT} -j ACCEPT")

def socks5_yukle():
    print("\n\n\t{}Dante SOCKS5 Yükleniyor..{}".format(yesil, renkreset))
    os.system(f"wget -qO dante_socks.sh https://raw.githubusercontent.com/Lozy/danted/master/install_centos.sh")
    os.system("chmod +x dante_socks.sh")
    os.system(f"./dante_socks.sh --port={SOCKS5_PORT} --user={KULLANICI} --passwd={SIFRE}")
    os.system("rm -rf dante_socks.sh")
    os.system(f"iptables -I INPUT -p tcp --dport {SOCKS5_PORT} -j ACCEPT")

def jq_yukle():
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/jq-linux64"
    os.system(f"wget -qO jq {url}")
    os.system("chmod +x jq")
    if not os.path.exists("/usr/bin/jq"):
        shutil.move("jq", "/usr/bin")
    else:
        print("jq zaten mevcut.")

def file_io_yukle():
    print("\n\n\t{}Zip Yükleniyor..{}".format(yesil, renkreset))
    with zipfile.ZipFile('proxy.zip', 'w') as zf:
        zf.write('veri.txt', arcname='veri.txt')

    # URL'yi dosya.io üzerinden yüklemek için bir POST isteği gönder
    with open('proxy.zip', 'rb') as f:
        response = requests.post('https://file.io', files={'file': f})
        json_response = response.json()
        url = json_response['link']

    print(f"\n{mor}Proxyler Hazır!{renkreset}")
    print(f"\n{mor}Zip İndirme Bağlantısı:{yesil} {url}{renkreset}")

IP4 = os.popen("curl -4 -s icanhazip.com").read().strip()
IP6 = os.popen("curl -6 -s icanhazip.com").read().strip()


print(f"\n\t{sari}IPv4 »{yesil} {IP4}{sari} | IPv6 için Sub »{yesil} {IP6}{renkreset}")
print(f"\n\n\t{yesil}Gerekli Paketler Yükleniyor..{renkreset}\n")
os.system("yum -y install gcc net-tools zip")

# Ana akış
adet = int(input("\nMor Kaç adet IPv6 proxy oluşturmak istiyorsunuz? Örnek 500: "))
veri_olustur(adet)
iptable_olustur()
config_3proxy()
yukle_3proxy()
squid_yukle()
socks5_yukle()
jq_yukle()
file_io_yukle()

print(f"\n{sari}IPv4 Proxy »{yesil} {IP4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}{renkreset}")
print(f"{sari}SOCKS5 Proxy »{yesil} {IP4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}{renkreset}\n")
