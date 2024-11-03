import os
import subprocess
import random
import requests
import zipfile
from getpass import getpass

# Kullanıcı bilgileri
KULLANICI = "tarak"
SIFRE = "kurek"

# Port ayarları
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110

# Renk ayarları
renkreset = '\033[0m'
yesil = '\033[1;92m'
kirmizi = '\033[1;91m'
sari = '\033[1;93m'
mor = '\033[0;35m'

def yukle_3proxy():
    print(f"\n\n\t{yesil}3Proxy Yükleniyor..{renkreset}\n")
    URL = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    
    # Dosyayı indir
    subprocess.run(['wget', '-q', URL])
    
    # Dosyayı aç
    subprocess.run(['bsdtar', '-xvf', '3proxy-3proxy-0.8.6.tar.gz'])
    
    # İndirilen dizine geç
    os.chdir("3proxy-3proxy-0.8.6")
    
    # Makefile ile derle
    subprocess.run(['make', '-f', 'Makefile.Linux'])
    
    # Gerekli dizinleri oluştur
    os.makedirs("/usr/local/etc/3proxy/bin", exist_ok=True)
    
    # Dosyaları kopyala
    subprocess.run(['cp', '-f', 'src/3proxy', '/usr/local/etc/3proxy/bin/'])
    subprocess.run(['cp', '-f', './scripts/rc.d/proxy.sh', '/etc/init.d/3proxy'])
    
    # İzinleri ayarla
    subprocess.run(['chmod', '+x', '/etc/init.d/3proxy'])
    subprocess.run(['chkconfig', '3proxy', 'on'])
    
    # Geçici dosyayı sil
    os.chdir("..")
    subprocess.run(['rm', '-rf', '3proxy-3proxy-0.8.6.tar.gz', '3proxy-3proxy-0.8.6'])
def rastgele():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=5))

def ipv6_olustur(prefix):
    ipv6_k = [str(i) for i in range(10)] + list('abcdef')
    return f"{prefix}:{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}:{''.join(random.choices(ipv6_k, k=4))}"

def veri_olustur(son_port, ip4, ip6):
    veri = []
    for port in range(IPV6_ILK_PORT, son_port + 1):
        veri.append(f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{ip4}/{port}/{ipv6_olustur(ip6)}")
    return veri

def iptable_olustur(veri):
    return [f"iptables -I INPUT -p tcp --dport {line.split('/')[3]} -m state --state NEW -j ACCEPT" for line in veri]

def ifconfig_olustur(veri):
    return [f"ifconfig eth0 inet6 add {line.split('/')[4]}/64" for line in veri]

def config_3proxy(veri):
    users = ' '.join([f"{line.split('/')[0]}:CL:{line.split('/')[1]}" for line in veri])
    proxy_config = [
        "daemon",
        "maxconn 1000",
        "nscache 65536",
        "timeouts 1 5 30 60 180 1800 15 60",
        "setgid 65535",
        "setuid 65535",
        "flush",
        "auth strong",
        f"users {users}"
    ]
    for line in veri:
        parts = line.split('/')
        proxy_config.append(f"auth strong")
        proxy_config.append(f"allow {parts[0]}")
        proxy_config.append(f"proxy -6 -n -a -p{parts[3]} -i{parts[2]} -e{parts[4]}")
        proxy_config.append("flush")
    return "\n".join(proxy_config)

def squid_yukle(ipv4_port):
    print(f"\n\n\t{yesil}Squid Yükleniyor..{renkreset}\n")
    subprocess.run(['yum', 'install', 'nano', 'dos2unix', 'squid', 'httpd-tools', '-y'])
    subprocess.run(['htpasswd', '-bc', '/ etc/squid/passwd', KULLANICI, SIFRE])
    squid_config = [
        "auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/passwd",
        "auth_param basic realm proxy",
        "acl authenticated proxy_auth REQUIRED",
        "acl smtp port 25",
        "http_access allow authenticated",
        f"http_port 0.0.0.0:{ipv4_port}",
        "http_access deny smtp",
        "http_access deny all",
        "forwarded_for delete"
    ]
    with open('/etc/squid/squid.conf', 'w') as f:
        f.write("\n".join(squid_config))
    subprocess.run(['systemctl', 'restart', 'squid.service'])
    subprocess.run(['systemctl', 'enable', 'squid.service'])
    subprocess.run(['iptables', '-I', 'INPUT', '-p', 'tcp', '--dport', str(ipv4_port), '-j', 'ACCEPT'])
    subprocess.run(['iptables-save'])

def proxy_txt(veri):
    with open('proxy.txt', 'w') as f:
        f.write("\n".join([f"{line.split('/')[2]}:{line.split('/')[3]}:{line.split('/')[0]}:{line.split('/')[1]}" for line in veri]))

def jq_yukle():
    URL = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/jq-linux64"
    subprocess.run(['wget', '-qO', 'jq', URL])
    subprocess.run(['chmod', '+x', './jq'])
    subprocess.run(['mv', 'jq', '/usr/bin'])

def file_io_yukle(veri):
    print(f"\n\n\t{yesil}Zip Yükleniyor..{renkreset}\n")
    PASS = rastgele()
    with zipfile.ZipFile('proxy.zip', 'w') as zipf:
        zipf.write('proxy.txt')
    JSON = requests.post('https://file.io', files={'file': open('proxy.zip', 'rb')}).json()
    URL = JSON['link']
    print(f"\n\n\t{mor}Proxyler Hazır!{sari} Format »{yesil} IP:PORT:KULLANICI:SIFRE{renkreset}")
    print(f"\n{mor}IPv6 Zip İndirme Bağlantısı:{yesil} {URL}{renkreset}")
    print(f"\n{mor}IPv6 Zip Şifresi:{yesil} {PASS}{renkreset}")

def socks5_yukle(socks5_port):
    print(f"\n\n\t{yesil}Dante SOCKS5 Yükleniyor..{renkreset}\n")
    subprocess.run(['wget', '-qO', 'dante_socks.sh', 'https://raw.githubusercontent.com/Lozy/danted/master/install_centos.sh'])
    subprocess.run(['chmod', '+x', './dante_socks.sh'])
    subprocess.run(['./dante_socks.sh', '--port=' + str(socks5_port), '--user=' + KULLANICI, '--passwd=' + SIFRE])
    subprocess.run(['rm', '-rf', 'dante_socks.sh'])
    subprocess.run(['iptables', '-I', 'INPUT', '-p', 'tcp', '--dport', str(socks5_port), '-j', 'ACCEPT'])
    subprocess.run(['iptables-save'])

IP4 = os.popen("curl -4 -s icanhazip.com").read().strip()
IP6 = os.popen("curl -6 -s icanhazip.com | cut -f1-4 -d':'").read().strip()

print(f"\n\t{sari}IPv4 »{yesil} {IP4}{sari} | IPv6 için Sub »{yesil} {IP6}{renkreset}")
print(f"\n\n\t{yesil}Gerekli Paketler Yükleniyor..{renkreset}\n")
subprocess.run(['yum', 'install', 'gcc', 'net-tools', 'bsdtar', 'zip', '-y'])

if IP6 == "":
    squid_yukle(IPV4_PORT)
    socks5_yukle(SOCKS5_PORT)
    print(f"\n\n\t{kirmizi}Makinenizin IPv6 Desteği Bulunmamaktadır..{renkreset}\n")
    print(f"\n{sari}IPv4   Proxy »{yesil} {IP4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}{renkreset}")
    print(f"\n{sari}SOCKS5 Proxy »{yesil} {IP4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}{renkreset}\n")
    exit(0)

yukle_3proxy()

print(f"\n \n{sari}Çalışma Dizini » /home/CentOS_Proxi_Yukle{renkreset}")
YOL = "/home/CentOS_Proxi_Yukle"
VERI = f"{YOL}/veri.txt"
os.makedirs(YOL, exist_ok=True)
os.chdir(YOL)

print(f"\n{mor}Kaç adet IPv6 proxy oluşturmak istiyorsunuz?{kirmizi} Örnek 500 : {renkreset}")
ADET = int(input())
print(f"\n\n")

SON_PORT = IPV6_ILK_PORT + ADET

veri = veri_olustur(SON_PORT, IP4, IP6)
with open(VERI, 'w') as f:
    f.write("\n".join(veri))

iptable_yapilandir = iptable_olustur(veri)
with open(f"{YOL}/iptable_yapilandir.sh", 'w') as f:
    f.write("\n".join(iptable_yapilandir))

ifconfig_yapilandir = ifconfig_olustur(veri)
with open(f"{YOL}/ifconfig_yapilandir.sh", 'w') as f:
    f.write("\n".join(ifconfig_yapilandir))

config_3proxy(veri)

with open('/etc/rc.local', 'a') as f:
    f.write(f"bash {YOL}/iptable_yapilandir.sh >/dev/null\n")
    f.write(f"bash {YOL}/ifconfig_yapilandir.sh >/dev/null\n")
    f.write("ulimit -n 10048\n")
    f.write("service 3proxy start\n")

subprocess.run(['bash', '/etc/rc.local'])

squid_yukle(IPV4_PORT)
socks5_yukle(SOCKS5_PORT)
proxy_txt(veri)
jq_yukle()
file_io_yukle(veri)

print(f"\n{sari}IPv4   Proxy »{yesil} {IP4}:{IPV4_PORT}:{KULLANICI}:{SIFRE}{renkreset}")
print(f"\n{sari}SOCKS5 Proxy »{yesil} {IP4}:{SOCKS5_PORT}:{KULLANICI}:{SIFRE}{renkreset}\n")
