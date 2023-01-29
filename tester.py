# from binance.client import Client
import time
import config
import utils


def main():
    try:
        client = utils.baglan()

        balance_usdt, balance_symbol = utils.get_usdt_trb_balance(client)
        if balance_usdt < 11 and abs(balance_symbol) < 0.4:
            utils.telegramBotSendText('UYARI : \n '
                                      'PROGRAMI ÇALIŞTIRMAK İÇİN YETERLİ BAKİYE MEVCUT DEĞİL. \n'
                                      'LÜTFEN HESABINIZA PARA TRANSFER EDİN.( GEREKEN MİN BAKİYE $11.')
            exit()

        if balance_symbol:
            utils.close_position(client)
            time.sleep(2)

        client.new_order(symbol=config.settings.SYMBOL, side='BUY', type='MARKET', quantity=0.4)
        time.sleep(5)
        balance_usdt, balance_symbol = utils.get_usdt_trb_balance(client)
        if balance_symbol != 0.4:
            utils.telegramBotSendText('ÖNEMLİ: TEST BAŞARISIZ! LÜTFEN HESABINIZI MANUEL OLARAK İNCELEYİN...')
            exit()

        client.new_order(symbol=config.settings.SYMBOL, side='SELL', type='MARKET', quantity=0.8)
        time.sleep(5)
        balance_usdt, balance_symbol = utils.get_usdt_trb_balance(client)
        if balance_symbol != -0.4:
            utils.telegramBotSendText('ÖNEMLİ: TEST BAŞARISIZ! LÜTFEN HESABINIZI MANUEL OLARAK İNCELEYİN...')
            exit()

        client.new_order(symbol=config.settings.SYMBOL, side='BUY', type='MARKET', quantity=0.4)
        time.sleep(5)
        balance_usdt, balance_symbol = utils.get_usdt_trb_balance(client)
        if balance_symbol != 0:
            utils.telegramBotSendText('ÖNEMLİ: TEST BAŞARISIZ! LÜTFEN HESABINIZI MANUEL OLARAK İNCELEYİN...')
            exit()

        utils.telegramBotSendText('BİLGİ : \n'
                                  'TEST BAŞARIYLA TAMAMLANDI.\n'
                                  'ARTIK CONFIG DOSYASINDA ÇALIŞMA MODUNU 1 DURUMUNA ALABİLİRSİNİZ.')
        exit()
    except Exception as e:
        utils.telegramBotSendText('ÖNEMLİ: TEST ESNASINDA HATA İLE KARŞILAŞILDI. \n' + str(e))
        exit()
