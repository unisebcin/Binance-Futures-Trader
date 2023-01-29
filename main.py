import config
import utils
import time
import tester
from dotenv import load_dotenv
load_dotenv()
time.sleep(2)


if __name__ == '__main__':
    if config.settings.MODE == 0:
        tester.main()
    client = utils.baglan()
    if not client:
        exit()

    utils.telegramBotSendText('BİLGİ : \nBinance Trader Programı Başladı...')
    minQty = config.settings.minQty
    initial_state = utils.initial_state(client)

    if config.settings.SET_INITIAL_SLEEP:
        time.sleep(config.settings.SET_INITIAL_SLEEP)
        config.settings.SET_INITIAL_SLEEP = 0

    while True:
        try:
            utils.check_daily_message(client)

            ema_100 = utils.calculate_ema100()
            ema_price = round(float(ema_100["EMA"][-2]), 2)
            price = utils.get_closing_price(client)

            initial_state = utils.check_initial_state(initial_state, price, ema_price)

            if not initial_state:

                status = utils.control_status(client, price, ema_price)

                if status:

                    utils.balance_check(client)

                    resp = utils.new_order(client, status)

                    balance_usdt, balance_trb = utils.get_usdt_trb_balance(client)
                    utils.telegramBotSendText(f'BİLGİ : \n {status} : \n USDT {balance_usdt} \n TRB {balance_trb}\n')
                    utils.write_log(status, ema_price, price, balance_usdt, balance_trb)

            utils.sleep()
        except Exception as e:
            utils.telegramBotSendText('ÖNEMLİ: Program Çalışırken Hata Oluştu !!! \n' + str(e))
            balance_usdt, balance_trb = utils.get_usdt_trb_balance(client)
            utils.telegramBotSendText(f'Bakiye Durumu : \n USDT {balance_usdt} \n TRB {balance_trb}\n')
            utils.telegramBotSendText('Sistemi Kontrol Edin ve Yeniden Başlatın')
            break
