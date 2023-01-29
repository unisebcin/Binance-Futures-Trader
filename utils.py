import os
import requests
import pandas as pd
import time
import config
from datetime import datetime
import json
from binance.um_futures import UMFutures
import math
# pip install binance-futures-connector


def baglan():
    """ BINANCE VE MUSTERI HESABIYLA BAGLANTI KURULUYOR """
    api_key = os.getenv('api_key')
    api_secret = os.getenv('api_secret')
    n = 0
    while n < 3:
        try:
            n += 1
            client = UMFutures(key=api_key, secret=api_secret, timeout=15) # Client(api_key=api_key, api_secret=api_secret)
            return client
        except requests.exceptions.ReadTimeout:
            print("requests.readTimeout")
            time.sleep(3)
        except requests.exceptions.ConnectionError:
            print("requests.exceptions.ConnectionError")
            time.sleep(3)
        except Exception as e:
            print('Error while connecting to account...', e)
            time.sleep(3)
    telegramBotSendText("UYARI : \n Binance API'a Bağlanırken Hata Oluştu. \n Lütfen Daha Sonra Tekrar Deneyin.")
    return ''


def getAccount(client):
    """ MUSTERI HEABINDAKI BILGILER TEMIN EDILIYOR.
    ONEMLI BIR NOKTA OLDUGUNDAN BINANCE KAYNAKLI OLASI HATALARA KARSI MAKSIMUM 5 KEZ ISTEK YAPILIYOR."""
    n = 0
    while n<5:
        try:
            n += 1
            return client.account()
        except requests.exceptions.ReadTimeout:
            print("requests.readTimeout - get_account")
            time.sleep(3)
        except requests.exceptions.ConnectionError:
            print("requests.exceptions.ConnectionError - get_account")
            time.sleep(3)
        except Exception as e:
            print('Error during getting account info : ' , e)
            time.sleep(3)
    telegramBotSendText("ÖNEMLİ : \n Hesap bilgilerini alırken hata oluştu. \n "
                        "İnternet bağlantınızı kontrol edin. 10 dakika bekleyin ve programı yeniden başlatın. \n "
                        "Hesap durumunuzu manuel kontrol etmeniz tavsiye edilir.")
    exit()


def get_closing_price(client):
    """ PERIOD KAPANISINDAKI FIYAT TESPIT EDILIYOR """
    data = client.klines(symbol=config.settings.SYMBOL, interval=config.settings.KLINE_PERIOD, limit=10)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                     "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                     "taker_buy_quote_asset_volume", "ignore"])
    return round(float(df['close'].get(8)), 2)


def get_usdt_trb_balance(client):
    """ SIKCA IHTIYAC DUYULAN USDT VE TRBUSDT BAKIYELERI HESAPLANIYOR """
    account = getAccount(client)
    balance = pd.DataFrame(account['assets'])
    positions = pd.DataFrame(account['positions'])
    balance_usdt = float(balance.query("asset == 'USDT'").reset_index(drop=True)['availableBalance'][0])
    balance_symbol = float(positions.query(f"symbol == '{config.settings.SYMBOL}'").reset_index()['positionAmt'][0])
    return balance_usdt, balance_symbol


def initial_state(client):
    """ PROGRAM BASLADIGINDA SISTEMIN CALISABILMESI ICIN GEREKEN ILK KONTROLLER YAPILIYOR. """
    try:
        myaccount = getAccount(client)
        positions = pd.DataFrame(myaccount['positions'])
        balance_usdt, balance_symbol = get_usdt_trb_balance(client)

        balance_check(client)

        price = get_closing_price(client)
        ema100 = round(calculate_ema100()["EMA"][-2], 2)
        config.settings.LEVERAGE = int(positions.query(f"symbol == '{config.settings.SYMBOL}'").get('leverage').values[0])

        balance_current_position = ''
        if balance_symbol != 0:
            balance_current_position = 'SELL' if balance_symbol < 0 else 'BUY'

        if price > ema100:
            current_state = 'BUY'
        else:
            current_state = 'SELL'

        if balance_symbol:
            if current_state != balance_current_position:
                close_position(client)

        if not os.path.exists('log.csv'):
            log = pd.DataFrame(columns=["datetime", "status", "ema_price", "price", "balance_usdt", "balance_trb"])
            log.to_csv('log.csv', index=False)

        r = requests.get('https://api.binance.com/api/v1/time')
        if r:
            system_time = datetime.fromtimestamp(r.json()['serverTime'] / 1000).minute
        else:
            system_time = datetime.now().minute
        _,  curr_time = divmod(system_time, 15)
        config.settings.SET_INITIAL_SLEEP = (15 - curr_time) * 60

        return current_state
    except Exception as e:
        telegramBotSendText('UYARI : Sistem Başlatılamadı. Aşağıda verilen hatayı inceleyin ve giderin \n' + str(e))
        exit()


def check_initial_state(initial, price, ema_price):
    """ PROGRAM BASLANGICINDA BELIRLENEN initial_state DEGISKENININ DEGISIMI KONTROL EDILIR.
    BU DEGISKEN BIR KEZ DEGISTKTEN SONRA BIR DAHA IHTIYAC KALMAZ.
    PROGRAM HER BASLATILDIGINDA ALIM SATIMA GIDILEBILMESI ICIN BU DEGISKENIN BIR KEZ KIRILMASI GEREKMEKTEDIR."""
    if initial == 'BUY':
        if ema_price > price:
            return ''
        else:
            return 'BUY'
    elif initial == 'SELL':
        if price > ema_price:
            return ''
        else:
            return 'SELL'
    else:
        return ''


def calculate_ema100():
    """ 15 DAKIKALIK PERIODA GORE EMA100 HESABI YAPILIR. ISLEMIN YAPILABILMESI ICIN interval=15m OLMAK ZORUNDADIR.
     AKSI HALDE BASKA YERLERDE DE DEGISIKLIK YAPMAK GEREKECEKTIR. """

    url = "https://fapi.binance.com/fapi/v1/klines"

    symbol = config.settings.SYMBOL
    interval = config.settings.KLINE_PERIOD
    if interval != '15m':
        telegramBotSendText(""" ÖNEMLİ: 
        EMA100 hesaplaması 15 dakikalık perioda göre yapılmalıdır!! 
        Bunu değiştirmek istiyorsanız, yazılımda genel bir değişiklik yapmak gerekecektir.
        """)
        exit()

    params = {
        "symbol": symbol,
        "interval": interval
    }

    response = requests.get(url, params=params)

    data = json.loads(response.text)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                     "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                     "taker_buy_quote_asset_volume", "ignore"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')

    df.set_index("timestamp", inplace=True)

    df = df.astype(float)

    df["EMA"] = df["close"].ewm(span=100, adjust=False).mean()
    return df[["open", "high", "low", "close","EMA"]]


def telegramBotSendText(bot_message):
    """ TELEGRAM UZERINDEN ISTENILEN MESAJ GONDERILIR """
    bot_token = '5794773301:AAHXDVijv7DqsTyEvWeiQ9vEugg8MRMunZQ'
    chat_id = '-728427299'
    msg = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=HTML&disable_web_page_preview=True&text=' + bot_message
    requests.get(msg)


def check_daily_message(client):
    """ HER GUN SAAT 12.00 DE PROGRAMIN CALISTIGI BILGISI PAYLASILIR """
    if datetime.now().hour == 12 and datetime.now().minute < 3:
        balance_usdt, balance_symbol = get_usdt_trb_balance(client)
        telegramBotSendText(f'BİLGİ : \n '
                            f'Hatırlatma Mesajı... \n Binance Trader Programı Çalışmaya Devam Ediyor...\n '
                            f'Gün : {datetime.today().date()}\n'
                            f'USDT : {balance_usdt} \n'
                            f'TRBUSDT : {balance_symbol}')


def control_status(client, price, ema_price):
    """HER PRIOD BASLANGICINDA EMA100-FIYAT KIRILIMINI KONTROL EDER.
    FIYAT KIRILMIS ISE ISLEM ALINMASI BILGISINI GONDERIR. FIYAT KIRILMAMIS ISE BOS DONER. """
    _, balance_symbol = get_usdt_trb_balance(client)

    if price >= ema_price:  # FIYAT BUY - BALANCE SELL VEYA 0 ISE ALIM YAP
        if balance_symbol <= 0:
            return 'BUY'
    else:  # FIYAT SELL - BALANCE BUY VEYA O ISE SATIS YAP.
        if balance_symbol >= 0:
            return 'SELL'

    return ''


def balance_check(client):
    """ISLEM YAPACAK KADAR PARA VE COIN YOK ISE MESAJ GONDERILIR VE SISTEM KAPATILIR."""
    balance_usdt, balance_symbol = get_usdt_trb_balance(client)
    price = get_price()
    balance = balance_usdt + abs(balance_symbol)*price
    if balance < 11:
        telegramBotSendText('ÖNEMLİ : \n FUTURES USDT Bakiyenize para transfer edin. Bakiyeniz toplamda $11 altında \n'
                            'Binance Trader programı kapanacak. Transfer tamamlandığında programı tekrar başlatın.')
        exit()


def get_price():
    """ ANLIK FIYAT BILGISI ALINIR """
    url = 'https://fapi.binance.com/fapi/v1/ticker/price'

    symbol = config.settings.SYMBOL

    response = requests.get(url, params={'symbol': symbol})

    price_info = response.json()

    return float(price_info['price'])


def close_position(client):
    """ HESAPTAKI BUTUN POZISYONLAR KAPATILIYOR """
    _, balance_symbol = get_usdt_trb_balance(client)
    side = 'SELL' if balance_symbol > 0 else 'BUY'
    if abs(balance_symbol) < config.settings.minQty:
        side2 = 'BUY' if side == 'SELL' else 'SELL'
        resp = client.new_order(symbol=config.settings.SYMBOL, side=side2, type='MARKET', quantity=0.4)
        time.sleep(2)
        _, balance_symbol = get_usdt_trb_balance(client)
        resp = client.new_order(symbol=config.settings.SYMBOL, side=side, type='MARKET', quantity=abs(balance_symbol))
    else:
        resp = client.new_order(symbol=config.settings.SYMBOL, side=side, type='MARKET', quantity=abs(balance_symbol))


def new_order(client, side):
    """ ALIM SATIM EMRI VERILIYOR """
    _, balance_symbol = get_usdt_trb_balance(client)

    if balance_symbol:
        close_position(client)
        time.sleep(2)

    price = get_price()
    balance_usdt, _ = get_usdt_trb_balance(client)
    qty = round(math.floor(min(balance_usdt, config.settings.MAX_AMOUNT) * 10 / price) / 10, 1) * config.settings.LEVERAGE
    resp = client.new_order(symbol=config.settings.SYMBOL, side=side, type='MARKET', quantity=qty)

    return resp


def write_log(status, ema_price, price, balance_usdt, balance_trb):
    log = pd.read_csv('log.csv')
    log.loc[len(log.index)] = [str(datetime.now()), status, ema_price, price, round(balance_usdt, 2),
                               balance_trb]
    log.to_csv('log.csv', index=False)


def sleep():
    """ PERIOD BASLANGICINA KADAR UYKU DURUMUNA GECILIYOR. """
    r = requests.get('https://api.binance.com/api/v1/time')
    if r:
        system_time = datetime.fromtimestamp(r.json()['serverTime'] / 1000).minute
    else:
        system_time = datetime.now().minute
    _, curr_time = divmod(system_time, 15)
    sleeptime = (config.settings.SLEEP_TIME - curr_time) * 60
    print(f'sleeping {sleeptime} sec')
    time.sleep(sleeptime)


# SIMDILIK KULLANILMAYAN FONKSIYONLAR
def check_ema_period():
    if datetime.now().minute in [0, 1, 15, 16, 30, 31, 45, 46]:
        return True
    return False


def get_historical_kline_data(client):
    data = client.klines(symbol=config.settings.SYMBOL, interval=config.settings.KLINE_PERIOD, limit=200)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                "taker_buy_quote_asset_volume", "ignore"])
    return df[["timestamp", "open", "high", "low", "close"]]


def get_symbol_info(client):
    data = client.exchange_info()
    data = [i for i in data['symbols'] if i['symbol'] == config.settings.SYMBOL]
    return data[0]
