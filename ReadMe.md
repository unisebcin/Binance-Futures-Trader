# BINANCE TRADER PROGRAMI

## Çalıştırma Öncesi Yapılması Gerekenler

- Bütün dosyalar aynı klasör içerisinde bulunmalıdır.
- Python projesi içerisine requirements.txt dosyasındaki paketler yüklenmiş olmalıdır.
- .env dosyası içerisinde api_key ve api_secret değerleri Binance API'dan aldığınız değerlerle değiştirilmiş olmalıdır.
- Telegram chat group'a katılımınız sağlanmış olmalıdır.
- İlk çalıştırma Test Modda yapılmalıdır. 
  - config.py dosyası içerisinde yer alan MODE değişkeni 0 olmalıdır. 
  - Test başarılı mesajı Telegram üzerinen alındığında bu değişken 1 yapılarak normal çalıştırma yapılabilir.

## Programın Çalışma Mantığı
- Binance Trader programı 15 dakikalık periodu baz alarak verilen strateji doğrultusunda işlem yapar.
- Telegram ile entegre olarak çalışır ve hergün saat 12.00 de Telegram chat grubuna çalışma bilgisi gönderir.
- Program ilk çalıştığında öncelikle başlangıç düzenlemeleri yapar.
  - Bakiye kontrolü yapar ve işlem yapacak bakiye yetersiz ise bilgi verir.
  - Fiyat ve ema10 karşılaştırması yaparak mevcut durumu (long/short) not eder.
  - Terste olan açık pozisyonlar varsa kapatılır. 
  - Bir sonraki periodun başlamasına kadar uyku moduna geçer.
- İlk çalıştırmada alım satımların başlaması için fiyat kırılımı gerçekleşmelidir. Fiyat kırılımı gerçekleştikten sonra devamlı olarak BUY veya SELL durumunda pozisyon alacaktır.
- Fiyat kırılımı gerçekleştiğinde 
  - Açık pozisyon kapatılır.
  - Duruma göre BUY veya SELL işlemi yapılır.
  - Telegram üzerinden işlem bilgisi paylaşılır.
- Çalışma esnasında herhangi bir hata ile karşılaşılırsa (Bakiye yetersizliği, Binance bağlantsının sağlanamaması gibi) Telegram üzerinden bilgi paylaşılacaktır.


## Diğer Hususlar

- TRBUSDT coin üzerinden 15 dakikalık periodda işlem yapar. Bu konfigürasyon değişecekse bilgi verilmelidir.
- TRBUSDT bakiye kontrolü sadece bu program üzerinden kontrol edilmelidir. Program çalışıyorken aynı hesap üzerinden TRBUSDT işlemleri yapılmamalıdır.
- İşleme girme şartı: minimum 11 dolarlık USDT miktarı veya buna karşılık gelecek TRBUSDT coin miktarı hesapta bulunmalıdır. Eger bu meblağ bulunmazsa önce pozisyonlar sonra sistem kapatılır. Para transferi sonrası sistem yeniden başlatılmalıdır.
- Kaldıraç etkisi: TRBUSDT coin çiftine ilişkin kaldırac etkisi dikkate alınır. 
- Telegram kullanımı: Her türlü bilgi/hata Telegramdan gönderilir. Aşağıdaki duruma göre dikkate alınız.
  - ÖNEMLİ : Program işlem yaparken ciddi bir sorun oluştu ve acil müdahale gerekiyordur. Program kapanacaktır. Mesajdaki talimatı takip edin ve sonra tekrar başlatın.
  - UYARI: Programın çalışması engellenmiştir. İlk fırsatta mesajda yazan talimatı uygulayıp programı yeniden başlatın.
  - BİLGİ: Program bilgilendirme yapiyordur.
