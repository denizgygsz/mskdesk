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

print('Kaldırma (uninstall) sırasında cmd penceresi gizlensin (kurumsal/temiz)')
degistir('src/platform/windows.rs',
         'run_cmds(get_uninstall(kill_self, true)?, true, "uninstall")',
         'run_cmds(get_uninstall(kill_self, true)?, false, "uninstall")', 1)

print('Oturum sonu müşteri bilgilendirme penceresi')
sm = 'flutter/lib/models/server_model.dart'
# bağlantı bitince (müşteri tarafı) özet penceresini tetikle
degistir(sm, "final close = (evt['close'] as String) == 'true';",
         "final close = (evt['close'] as String) == 'true';\n"
         "      try { if (close) { final _mi = _clients.indexWhere((c) => c.id == id); if (_mi >= 0 && _clients[_mi].authorized) _mskOturumOzeti(_clients[_mi]); } } catch (e) {}", 1)
# özet penceresi yöntemi (onClientRemove'dan hemen önce eklenir)
_msk_ozet = '''  // MSKDesk: bağlantı bitince müşteriye ne yapıldığını ve kayıt altına alındığını gösterir
  void _mskOturumOzeti(Client c) {
    try {
      final islemler = <String>[];
      if (c.keyboard) islemler.add('Uzaktan kontrol (klavye/fare)');
      if (c.file) islemler.add('Dosya aktarimi');
      if (c.audio) islemler.add('Ses dinleme');
      if (c.clipboard) islemler.add('Pano paylasimi');
      if (c.restart) islemler.add('Yeniden baslatma');
      Future.delayed(const Duration(milliseconds: 120), () { if (desktopType == DesktopType.cm) showCmWindow(); });
      parent.target?.dialogManager.show((setState, close, context) {
        kapat() { try { close(); } catch (e) {} Future.delayed(const Duration(milliseconds: 200), () { if (desktopType == DesktopType.cm && _clients.isEmpty) hideCmWindow(); }); }
        Timer(const Duration(seconds: 25), kapat);
        return CustomAlertDialog(
          title: Row(children: [const Icon(Icons.verified_user, color: Color(0xFFD71920)), const SizedBox(width: 8), Flexible(child: Text('MSK Destek - Oturum sona erdi'))]),
          content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Teknisyen: ' + (c.name.isEmpty ? c.peerId : c.name)),
            const SizedBox(height: 8),
            Text(islemler.isEmpty ? 'Bu oturumda ekraniniz goruntulendi.' : ('Yapilan islemler: ' + islemler.join(', ') + '.')),
            const SizedBox(height: 8),
            const Text('Bu oturum guvenlik icin kayit altina alinmistir.'),
            const SizedBox(height: 4),
            const Text('Sorulariniz icin: destek@mskglobal.net'),
          ]),
          actions: [dialogButton('Tamam', onPressed: kapat)],
        );
      });
    } catch (e) {}
  }

'''
degistir(sm, "  void onClientRemove(Map<String, dynamic> evt) {", _msk_ozet + "  void onClientRemove(Map<String, dynamic> evt) {", 1)

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
# hard-settings: is_disable_ab() gibi fonksiyonların okuduğu HARD_SETTINGS'e doğrudan yazılır
for k, val in (AYAR.get('hard-settings') or {}).items():
    if '"' in k or '"' in str(val):
        sys.exit('HATA hard-settings: tırnak olamaz')
    cagrilar += f'    config::HARD_SETTINGS.write().unwrap().insert("{k}".to_owned(), "{val}".to_owned());\n'
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

print('Hakkında sayfası (amaç, web, destek, KVKK)')
sp = 'flutter/lib/desktop/pages/desktop_setting_page.dart'
# web ve gizlilik bağlantıları MSK'ye
degistir(sp, "launchUrlString('https://rustdesk.com/privacy.html');", "launchUrlString('https://mskglobal.net');", 1)
degistir(sp, "launchUrlString('https://rustdesk.com');", "launchUrlString('https://mskglobal.net');", 1)
# Hakkında kutusundaki mavi şerit -> MSK kırmızısı
degistir(sp, 'const BoxDecoration(color: Color(0xFF2c8cff))', f'const BoxDecoration(color: Color(0xFF{KIRMIZI}))', 1)
# amaç + destek + KVKK aydınlatma metni (Sürüm satırının üstüne). CRLF'ye toleranslı.
about_anchor = ("              SelectionArea(\n"
                "                  child: Text('${translate('Version')}: $version')\n"
                "                      .marginSymmetric(vertical: 4.0)),")
about_blok = (
    "              SelectionArea(child: Text('MSKDesk, MSK Global Electronics IT destek ekibinin kurumsal uzaktan destek uygulamasıdır. Yalnızca yetkili teknisyenler tarafından, kayıt altında uzaktan destek amacıyla kullanılır.').marginSymmetric(vertical: 4.0)),\n"
    "              SelectionArea(child: Text('Destek: destek@mskglobal.net').marginSymmetric(vertical: 4.0)),\n"
    "              SelectionArea(child: Text('KVKK Aydınlatma: Uzak destek oturumlarında bağlantı kayıtları (kim, ne zaman, hangi cihaz), cihaz bilgileri ve oturum ekran kaydı; veri sorumlusu MSK Global Electronics tarafından, destek hizmetinin yürütülmesi ve güvenliği amacıyla işlenir ve mevzuatta öngörülen süre boyunca saklanır. Talepleriniz için: destek@mskglobal.net').marginSymmetric(vertical: 4.0)),\n")
pat = re.escape(about_anchor).replace('\\\n', r'\r?\n').replace('\n', r'\r?\n')
s = oku(sp)
s2, n = re.subn(pat, lambda m: about_blok + m.group(0), s, count=1)
if n != 1:
    sys.exit(f'HATA {sp}: Hakkında çıpası bulunamadı ({n})')
yaz(sp, s2)
print(f'  {sp} Hakkında: 1')

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
    ('logo_light.png', 'flutter/assets/logo.png'),   # yedek: in-app logo her durumda MSK logosu olsun
]:
    if not (KOK / hedef).parent.is_dir():
        sys.exit(f'HATA {hedef}: klasör yok')
    shutil.copy(v / kaynak, KOK / hedef)
    print(f'  {hedef}')

print(f'{AD} markalaması tamam.')
