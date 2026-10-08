#!/usr/bin/env python3
"""RustDesk kaynağını MSKDesk'e çevirir (ad, sunucu, anahtar, dosya bilgileri, metinler, ikonlar).

RustDesk deposunun kökünde çalıştırılır:  python mskdesk/brand/brand.py
Her değişiklik eşleşme sayısını doğrular. RustDesk yeni sürümde bir yeri değiştirirse
derleme burada, anlaşılır bir hatayla durur; sessizce yarım markalı uygulama çıkmaz.
"""
import json
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
KIRMIZI = 'D71920'       # MSK kırmızısı; RustDesk'in mavi vurgusunun (0071FF) yerine
KIRMIZI_ACIK = 'E23A40'  # buton/ikincil için biraz daha açık ton (mavi 2C8CFF yerine)


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

print('Tema renkleri (mavi vurgu -> MSK kırmızısı)')
cd = 'flutter/lib/common.dart'
degistir(cd, 'static const Color accent = Color(0xFF0071FF);', f'static const Color accent = Color(0xFF{KIRMIZI});', 1)
degistir(cd, 'static const Color accent50 = Color(0x770071FF);', f'static const Color accent50 = Color(0x77{KIRMIZI});', 1)
degistir(cd, 'static const Color accent80 = Color(0xAA0071FF);', f'static const Color accent80 = Color(0xAA{KIRMIZI});', 1)
degistir(cd, 'static const Color idColor = Color(0xFF00B6F0);', f'static const Color idColor = Color(0xFF{KIRMIZI});', 1)
degistir(cd, 'static const Color button = Color(0xFF2C8CFF);', f'static const Color button = Color(0xFF{KIRMIZI_ACIK});', 1)
degistir(cd, 'return Color(0xFF2C8CFF);', f'return Color(0xFF{KIRMIZI_ACIK});', 1)   # bildirim rengi (buton tonuyla aynı)
degistir(cd, 'primary: Colors.blue,', 'primary: Colors.red,', 2)   # açık + koyu tema ColorScheme; "blue": etiket renk haritası dokunulmaz

print('Gömülü kilitli ayarlar (mskdesk.json)')
# load_custom_client gövdesi yeniden yazılır: imzalı custom.txt doğrulaması (read_custom_client)
# ve onun KEY sabiti OLDUĞU GİBİ KORUNUR; biz yalnız override-settings'i doğrudan uygularız.
AYAR = json.loads((MSK / 'mskdesk.json').read_text(encoding='utf-8'))
cagrilar = ''
for anahtar, override in (('default-settings', 'false'), ('override-settings', 'true')):
    if AYAR.get(anahtar):
        jstr = json.dumps(AYAR[anahtar], ensure_ascii=False)
        if '"#' in jstr:
            sys.exit(f'HATA mskdesk.json {anahtar}: değer içinde \'"#\' olamaz')
        cagrilar += (
            f'    if let Ok(ayar) = serde_json::from_str::<serde_json::Value>(\n'
            f'        r#"{jstr}"#,\n'
            f'    ) {{\n'
            f'        read_custom_client_advanced_settings(ayar, &md, &ml, &ms, &mb, {override});\n'
            f'    }}\n'
        )
yeni_fn = (
    'pub fn load_custom_client() {\n'
    '    // MSKDesk: kilitli kurumsal ayarlar derlemeye gömülüdür (gözetimsiz erişim:\n'
    '    // doğru kalıcı şifreyle, uzaktaki kullanıcı onay vermeden bağlanır).\n'
    '    // RustDesk\'in imzalı custom.txt doğrulaması (read_custom_client) ve KEY sabiti\n'
    '    // olduğu gibi korunur; burada yalnız gömülü ayarlar uygulanır, dışarıdan custom.txt okunmaz.\n'
    '    let mut md = HashMap::new();\n'
    '    for s in keys::KEYS_DISPLAY_SETTINGS { md.insert(s.replace("_", "-"), s); }\n'
    '    let mut ml = HashMap::new();\n'
    '    for s in keys::KEYS_LOCAL_SETTINGS { ml.insert(s.replace("_", "-"), s); }\n'
    '    let mut ms = HashMap::new();\n'
    '    for s in keys::KEYS_SETTINGS { ms.insert(s.replace("_", "-"), s); }\n'
    '    let mut mb = HashMap::new();\n'
    '    for s in keys::KEYS_BUILDIN_SETTINGS { mb.insert(s.replace("_", "-"), s); }\n'
    f'{cagrilar}'
    '}'
)
s = oku('src/common.rs')
# .*? kapanış süslü parantezine kadar; satır sonu CRLF olabilir (Windows checkout)
s2, n = re.subn(r'pub fn load_custom_client\(\) \{.*?\r?\n\}', lambda _: yeni_fn, s, count=1, flags=re.S)
if n != 1:
    sys.exit('HATA src/common.rs: load_custom_client bulunamadı')
yaz('src/common.rs', s2)
print(f'  src/common.rs load_custom_client: 1')

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
