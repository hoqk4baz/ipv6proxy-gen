import os
import subprocess
import random
import string
import requests

# Kullanıcı bilgileri
KULLANICI = "tarak"
SIFRE = "kurek"

# Port bilgileri
IPV4_PORT = 3310
IPV6_ILK_PORT = 10000
SOCKS5_PORT = 5110

def yukle_3proxy():
    print("3Proxy Yükleniyor...")
    url = "https://github.com/keyiflerolsun/CentOS_Proxi/raw/main/Paketler/3proxy-3proxy-0.8.6.tar.gz"
    subprocess.run(f"wget -qO- {url} | tar -zxvf -", shell=True)
    os.chdir("3proxy-3proxy-0.8.6")
    subprocess.run("make -f Makefile.Linux", shell=True)
    os.makedirs("/usr/local/etc/3proxy/{bin,logs,stat}", exist_ok=True)
    subprocess.run("cp -f src/3proxy /usr/local/etc/3proxy/bin/", shell=True)
    subprocess.run("cp -f ./scripts/rc.d/proxy.sh /etc/init.d/3proxy", shell=True)
    subprocess.run("chmod +x /etc/init.d/3proxy", shell=True)
    subprocess.run("chkconfig 3proxy on", shell=True)
    os.chdir("..")
    subprocess.run("rm -rf 3proxy-3proxy-0.8.6", shell=True)

def rastgele():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

ipv6_k = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

def ipv6_olustur(ipv6_subnet):
    def ipv64_ver():
        return ''.join(random.choice(ipv6_k) for _ in range(4))
    return f"{ipv6_subnet}:{ipv64_ver()}:{ipv64_ver()}:{ipv64_ver()}:{ipv64_ver()}"

def veri_olustur(adet, ipv4, ipv6_subnet):
    entries = []
    for port in range(IPV6_ILK_PORT, IPV6_ILK_PORT + adet):
        ip6 = ipv6_olustur(ipv6_subnet)
        entry = f"{KULLANICI}{rastgele()}/{SIFRE}{rastgele()}/{ipv4}/{port}/{ip6}"
        entries.append(entry)
    return entries

def iptable_olustur(entries):
    rules = [f"iptables -I INPUT -p tcp --dport {entry.split('/')[3]} -m state --state NEW -j ACCEPT" for entry in entries]
    return "\n".join(rules)

def ifconfig_olustur(entries):
    configs = [f"ifconfig eth0 inet6 add {entry.split('/')[4]}/64" for entry in entries]
    return "\n".join(configs)

def config_3proxy(entries):
    user_configs = [f"{entry.split('/')[0]}:CL:{entry.split('/')[1]}" for entry in entries]
    proxy_configs = [f"auth strong\nallow {entry.split('/')[0]}\nproxy -6 -n -a -p{entry.split('/')[3]} -i{entry.split('/')[2]} -e{entry.split('/')[4]}\nflush\n" for entry in entries]
    return f"daemon\nmaxconn 1000\nnscache 65536\ntimeouts 1 5 30 60 180 1800 15 60\nsetgid 65535\nsetuid 65535\nflush\nauth strong\nusers {' '.join(user_configs)}\n{''.join(proxy_configs)}"

def squid_yukle():
    print("Squid Yükleniyor...")
    subprocess.run("yum install nano dos2unix squid httpd-tools -y", shell=True)
    subprocess.run(f"htpasswd -bc /etc/squid/passwd {KULLANICI} {SIFRE}", shell=True)
    with open("/etc/squid/squid.conf", "w") as f:
        f.write(f"""\
auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic realm proxy
acl authenticated proxy_auth REQUIRED
acl smtp port 25
http_access allow authenticated
http_port 0.0.0.0:{IPV4_PORT}
http_access deny smtp
http_access deny all
forwarded_for delete
""")
    subprocess.run("systemctl restart squid.service", shell=True)
    subprocess.run("systemctl enable squid.service", shell=True)
    subprocess.run(f"iptables -I INPUT -p tcp --dport {IPV4_PORT} -j ACCEPT", shell=True)
    subprocess.run("iptables-save", shell=True)

def socks5_yukle():
    print("Dante SOCKS5 Yükleniyor...")
    subprocess.run("wget -qO dante_socks.sh https://raw.githubusercontent.com/Lozy/danted/master/install_centos.sh", shell=True)
    subprocess.run(f"./dante_socks.sh --port={SOCKS5_PORT} --user={KULLANICI} --passwd={SIFRE}", shell=True)
    subprocess.run("iptables -I INPUT -p tcp --dport SOCKS5_PORT -j ACCEPT", shell=True)
    subprocess.run("iptables-save", shell=True)

def proxy_txt(entries):
    with open("proxy.txt", "w") as f:
        for entry in entries:
            ip, port, user, passwd = entry.split('/')[2], entry.split('/')[3], entry.split('/')[0], entry.split('/')[1]
            f.write(f"{ip}:{port}:{user}:{passwd}\n")

def file_io_yukle():
    print("Zip Yükleniyor...")
    password = "enza"
    subprocess.run(f"zip --password {password} proxy.zip proxy.txt", shell=True)
    response = requests.post("https://file.io", files={"file": open("proxy.zip", "rb")})
    url = response.json().get("link")
    print(f"IPv6 Zip İndirme Bağlantısı: {url}")
    print(f"IPv6 Zip Şifresi: {password}")

# IPv4 ve IPv6 adreslerini alın
IP4 = os.popen("curl -4 -s icanhazip.com").read().strip()
IP6 = os.popen("curl -6 -s icanhazip.com | cut -f1-4 -d':'").read().strip()

print(f"IPv4 » {IP4} | IPv6 için Sub » {IP6}")
adet = int(input("Kaç adet IPv6 proxy oluşturmak istiyorsunuz? Örnek 500 : "))

# Verileri oluşturun
entries = veri_olustur(adet, IP4, IP6)
with open("veri.txt", "w") as f:
    f.write("\n".join(entries))

# 3proxy yapılandırmalarını ve diğer ayarları oluşturun
print(iptable_olustur(entries))
print(ifconfig_olustur(entries))
print(config_3proxy(entries))

# Hizmetleri yükle
yukle_3proxy()
squid_yukle()
socks5_yukle()
proxy_txt(entries)
file_io_yukle()
