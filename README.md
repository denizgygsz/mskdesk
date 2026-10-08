# MSKDesk

MSK Global Electronics IT destek ekibinin uzak masaüstü uygulaması. [RustDesk](https://github.com/rustdesk/rustdesk) üzerine kuruludur ve şirketin kendi sunucusunu (`destek.mskglobal.net`) kullanır.

## Bu depoda ne var?

RustDesk'in kaynak kodu burada tutulmaz. Derleme sırasında RustDesk'in etiketli sürümü indirilir ve aşağıdaki değişiklikler uygulanır:

| Dosya | Ne yapar |
|---|---|
| `brand/brand.py` | Uygulama adı (MSKDesk), sunucu adresi, sunucu anahtarı, API adresi, Windows dosya bilgileri, arayüz metinleri ve ikonlar |
| `brand/assets/` | MSKDesk ikonları ve MSK logosu |
| `.github/workflows/build-windows.yml` | RustDesk'in resmi Windows derleme adımları + markalama |

Uygulama adı "MSKDesk" olduğu için kurulum klasörü (`C:\Program Files\MSKDesk`), Windows servisi ve bağlantı linki (`mskdesk://`) de bu adı alır.

## Derleme

GitHub'da **Actions → MSKDesk Windows → Run workflow**. Derleme yaklaşık 1 saat sürer. Sonuç **Releases** sayfasına `MSKDesk-setup.exe` olarak yüklenir.

RustDesk sürümünü yükseltmek için çalıştırırken yeni etiketi girin (örn. `1.5.1`). `brand.py` her değişikliğin yerini bulduğunu doğrular; RustDesk bir dosyayı değiştirdiyse derleme anlaşılır bir hatayla durur. Bu durumda `build-windows.yml` içindeki araç sürümleri de RustDesk'in `.github/workflows/flutter-build.yml` dosyasından güncellenmelidir.

Yerelde markalamayı denemek için RustDesk kaynağının kökünde:

```
python <bu depo>/brand/brand.py
```

## Lisans

RustDesk, [GNU AGPL-3.0](LICENSE) lisanslıdır; MSKDesk de aynı lisansla dağıtılır. Bu depo, dağıtılan uygulamanın karşılık gelen kaynak kodunu (RustDesk etiketi + bu depodaki değişiklikler) herkese açık olarak sunar. RustDesk'in telif hakkı bildirimleri korunmuştur.

RustDesk © Purslane Tech Pte. Ltd. ve katkıda bulunanlar.
