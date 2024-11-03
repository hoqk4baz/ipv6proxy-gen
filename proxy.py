import os
import subprocess
import requests
import random
import string
import zipfile
import shutil

# Kullanıcı ve Şifre
KULLANICI = "tarak"
SIFRE = "kurek"

# Port ayarları
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110

# Renk kodları
renkreset = '\033[0m'
yesil = '\033[1;92m'
kirmizi = '\033[1;91m'
sari = '\033[1;93m'
mor = '\033[0;35m'

def renkli_yaz(yazi, renk):
    print(f"{renk}{yazi}{renkreset}")

def yukle_3proxy():
    renkli_yaz("3Proxy Yükleniyor..", yesil)
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    os.system(f"wget -qO- {url} | bsdtar -xvf-")
    os.chdir("3proxy-3proxy-0.8.6")
    os.system("make -f Makefile.Linux")
    os.makedirs("/usr/local/etc/3proxy/{bin,logs,stat}", exist_ok=True)
    shutil.copy("src/3proxy", "/usr/local/etc/3proxy/bin/")
    shutil.copy("./scripts/rc.d/proxy.sh", "/etc/init.d/3proxy")
    os.chmod("/etc/init.d/3proxy", 0o755)
    os.system("chkconfig 3proxy on")
    os.chdir("..")
    shutil.rmtree("3proxy-3proxy-0.8.6")

def rastgele():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def ipv6_olustur():
    ipv6_k = [str(i) for i in range(10)] + list('abcdef')
    return ":".join("".join(random.choices(ipv6_k, k=4)) for _ in range(8))

def veri_olustur(ip4):
    with open("veri.txt", "w") as f:
        for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + ADET):
            f.write(f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{ip4}/{port}/{ipv6_olustur()}\n")

def iptable_olustur():
    with open("iptable_yapilandir.sh", "w") as f:
        for line in open("veri.txt"):
            port = line.split("/")[3]
            f.write(f"iptables -I INPUT -p tcp --dport {port} -m state --state NEW -j ACCEPT\n")

def ifconfig_olustur():
    with open("ifconfig_yapilandir.sh", "w") as f:
        for line in open("veri.txt"):
            ip6 = line.split("/")[-1]
            f.write(f"ifconfig eth0 inet6 add {ip6}/64\n")

def config_3proxy():
    with open("/usr/local/etc/3proxy/3proxy.cfg", "w") as f:
        f.write("daemon\nmaxconn 1000\nnscache 65536\ntimeouts 1 5 30 60 180 1800 15 60\n")
        f.write("setgid 65535\nsetuid 65535\nflush\nauth strong\n")
        f.write("users " + " ".join(f"{line.split('/')[0]}:CL:{line.split('/')[1]}" for line in open("veri.txt")) + "\n")
        for line in open("veri.txt"):
            parts = line.strip().split("/")
            f.write(f"auth strong\nallow {parts[0]}\nproxy -6 -n -a -p{parts[3]} -i{parts[2]} -e{parts[4]}\nflush\n")

def squid_yukle():
    renkli_yaz("Squid Yükleniyor..", yesil)
    os.system("yum install nano dos2unix squid httpd-tools -y")
    os.system(f"htpasswd -bc /etc/squid/passwd {KULLANICI} {SIFRE}")
    
    squid_conf = """
auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic realm proxy
acl authenticated proxy_auth REQUIRED
acl smtp port 25
http_access allow authenticated
http_port 0.0.0.0:{}
http_access deny smtp
http_access deny all
forwarded_for delete
""".format(IPV4_PORT)
    
    with open("/etc/squid/squid.conf", "w") as f:
        f.write(squid_conf)

    os.system("systemctl restart squid.service && systemctl enable squid.service")
    os.system(f"iptables -I INPUT -p tcp --dport {IPV4_PORT} -j ACCEPT")

def proxy_txt():
    with open("proxy.txt", "w") as f:
        for line in open("veri.txt"):
            parts = line.strip().split("/")
            f.write(f"{parts[2]}:{parts[3]}:{parts[0]}:{parts[1]}\n")

def jq_yukle():
    os.system("wget -qO jq https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/jq-linux64")
    os.chmod("jq", 0o755)
    shutil.move("jq", "/usr/bin")

def zip_yukle():
    renkli_yaz("Zip Yükleniyor..", yesil)
    passw = rastgele()
    
    with zipfile.ZipFile("proxy.zip", 'w') as zipf:
        zipf.write("proxy.txt")
    
    files = {'file': open('proxy.zip', 'rb')}
    response = requests.post("https://file.io", files=files)
    url = response.json().get('link')

    renkli_yaz("Proxyler Hazır!", yesil)
    renkli_yaz(f"IPv6 Zip İndirme Bağlantısı: {url}", yesil)
    renkli_yaz(f"IPv6 Zip Şifresi: {passw}", yesil)

def socks5_yukle():
    renkli_yaz("Dante SOCKS5 Yükleniyor..", yesil)
    os.system(f"wget -qO dante_socks.sh https://raw.githubusercontent.com/Lozy/danted/master/install_centos.sh")
    os.chmod("dante_socks.sh", 0o755)
    os.system(f"./dante_socks.sh --port={SOCKS5_PORT} --user={KULLANICI} --passwd={SIFRE}")
    os.remove("dante_socks.sh")
    os.system(f"iptables -I INPUT -p tcp --dport {SOCKS5_PORT} -j ACCEPT")

# Ana program akışı
ip4 = requests.get("http://icanhazip.com").text.strip()
print(f"\n\t{sari}IPv4 » {yesil}{ip4}{renkreset}")

if requests.get("http://ipv6.icanhazip.com").status_code == 404:
    squid_yukle()
    socks5_yukle()
    renkli_yaz("Makinenizin IPv6 Desteği Bulunmamaktadır.", kirmizi)
    renkli_yaz(f"IPv4 Proxy » {ip4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}", yesil)
    renkli_yaz(f"SOCKS5 Proxy » {ip4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}", yesil)
    exit(0)

# IPv6 işlemleri
ADET = int(input("Kaç adet IPv6 proxy oluşturmak istiyorsunuz? (Örnek: 500): "))
veri_olustur(ip4)
iptable_olustur()
ifconfig_olustur()
config_3proxy()

with open("/etc/rc.local", "a") as f:
    f.write(f"""
bash /home/CentOS_Proxi_Yukle/iptable_yapilandir.sh >/dev/null
bash /home/CentOS_Proxi_Yukle/ifconfig_yapilandir.sh >/dev/null
ulimit -n 10048
service 3proxy start
""")

os.system("bash /etc/rc.local")
squid_yukle()
socks5_yukle()
proxy_txt()
jq_yukle()
zip_yukle()

renkli_yaz(f"IPv4 Proxy » {ip4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}", yesil)
renkli_yaz(f"SOCKS5 Proxy » {ip4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}", yesil)
