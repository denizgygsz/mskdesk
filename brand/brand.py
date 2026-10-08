#!/usr/bin/env python3
"""RustDesk kaynağını MSKDesk'e çevirir (ad, sunucu, anahtar, dosya bilgileri, metinler, ikonlar).

RustDesk deposunun kökünde çalıştırılır:  python mskdesk/brand/brand.py
Her değişiklik eşleşme sayısını doğrular. RustDesk yeni sürümde bir yeri değiştirirse
derleme burada, anlaşılır bir hatayla durur; sessizce yarım markalı uygulama çıkmaz.
"""
import re
import shutil
import sys
from pathlib import Path

KOK = Path.cwd()
MSK = Path(__file__).resolve().parent.parent
AD = 'MSKDesk'
SUNUCU = 'destek.mskglobal.net'
ANAHTAR = 'pIrqc0NorXsGeBWZseBzZCj0SpD66seHBa5Y3WZ+W8s='
API = 'https://destek.mskglobal.net'
SIRKET = 'MSK Global Electronics'


def oku(yol):
    with open(KOK / yol, encoding='utf-8', newline='') as f:
        return f.read()


def yaz(yol, metin):
    with open(KOK / yol, 'w', encoding='utf-8', newline='') as f:
        f.write(metin)


def degistir(yol, eski, yeni, adet=None, regex=False):
    s = oku(yol)
    if regex:
        s2, n = re.subn(eski, yeni, s)
    else:
        n = s.count(eski)
        s2 = s.replace(eski, yeni)
    if n == 0 or (adet is not None and n != adet):
        sys.exit(f'HATA {yol}: beklenen {adet or "en az 1"} eşleşme, bulunan {n} -> {eski[:90]!r}')
    yaz(yol, s2)
    print(f'  {yol}: {n}')


print('Uygulama adı, sunucu ve anahtar')
cfg = 'libs/hbb_common/src/config.rs'
degistir(cfg, 'APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned())',
         f'APP_NAME: RwLock<String> = RwLock::new("{AD}".to_owned())', 1)
degistir(cfg, 'RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"]', f'RENDEZVOUS_SERVERS: &[&str] = &["{SUNUCU}"]', 1)
degistir(cfg, r'pub const RS_PUB_KEY: &str = "[^"]+";', f'pub const RS_PUB_KEY: &str = "{ANAHTAR}";', 1, regex=True)
degistir('src/common.rs', '"https://admin.rustdesk.com".to_owned()', f'"{API}".to_owned()', 1)

print('Windows dosya bilgileri')
for yol in ('Cargo.toml', 'libs/portable/Cargo.toml'):
    degistir(yol, 'description = "RustDesk Remote Desktop"', f'description = "{AD}"', 1)
    degistir(yol, 'ProductName = "RustDesk"', f'ProductName = "{AD}"', 1)
    degistir(yol, 'FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{AD}"', 1)
    degistir(yol, 'OriginalFilename = "rustdesk.exe"', f'OriginalFilename = "{AD}.exe"', 1)
rc = 'flutter/windows/runner/Runner.rc'
degistir(rc, 'VALUE "CompanyName", "Purslane Tech Pte. Ltd."', f'VALUE "CompanyName", "{SIRKET}"', 1)
degistir(rc, 'VALUE "FileDescription", "RustDesk Remote Desktop"', f'VALUE "FileDescription", "{AD}"', 1)
degistir(rc, 'VALUE "InternalName", "rustdesk"', f'VALUE "InternalName", "{AD.lower()}"', 1)
degistir(rc, 'VALUE "OriginalFilename", "rustdesk.exe"', f'VALUE "OriginalFilename", "{AD}.exe"', 1)
degistir(rc, 'VALUE "ProductName", "RustDesk"', f'VALUE "ProductName", "{AD}"', 1)
degistir('flutter/windows/runner/main.cpp', 'std::wstring app_name = L"RustDesk";', f'std::wstring app_name = L"{AD}";', 1)

print('Arayüz metinleri (yalnız çeviri değerleri; anahtarlar aynı kalır)')
satir = re.compile(r'^(\s*\("(?:[^"\\]|\\.)*",\s*")((?:[^"\\]|\\.)*)("\),?)', re.M)
toplam = 0
for p in sorted((KOK / 'src/lang').glob('*.rs')):
    yol = p.relative_to(KOK)
    s = oku(yol)
    toplam += sum(m[2].count('RustDesk') for m in satir.finditer(s))
    yaz(yol, satir.sub(lambda m: m[1] + m[2].replace('RustDesk', AD) + m[3], s))
if toplam == 0:
    sys.exit('HATA src/lang: hiç "RustDesk" metni bulunamadı')
print(f'  src/lang: {toplam}')

print('İkonlar ve logo')
v = MSK / 'brand/assets'
for kaynak, hedef in [
    ('mskdesk.ico', 'flutter/windows/runner/resources/app_icon.ico'),
    ('mskdesk.ico', 'res/icon.ico'),
    ('mskdesk-tray.ico', 'res/tray-icon.ico'),
    ('mskdesk-512.png', 'res/icon.png'),
    ('mskdesk-32.png', 'res/32x32.png'),
    ('mskdesk-64.png', 'res/64x64.png'),
    ('mskdesk-128.png', 'res/128x128.png'),
    ('mskdesk-256.png', 'res/128x128@2x.png'),
    ('mskdesk-256.png', 'flutter/assets/icon.png'),
    ('mskdesk.ico', 'flutter/assets/icon.ico'),
    ('logo_light.png', 'flutter/assets/logo_light.png'),
    ('logo_dark.png', 'flutter/assets/logo_dark.png'),
]:
    if not (KOK / hedef).parent.is_dir():
        sys.exit(f'HATA {hedef}: klasör yok')
    shutil.copy(v / kaynak, KOK / hedef)
    print(f'  {hedef}')

print(f'{AD} markalaması tamam.')
