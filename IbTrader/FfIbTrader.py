from tinydb import Query
import requests
import os
from datetime import datetime, date
from dateutil import parser as dup
from time import sleep
import pytz
import threading
from FfTradeExecutor import FfTradeExecutor
from Config import Config
from FfJsonDb import FfJsonDb

class FfIbTrader():
    def __executeTrades(self):
        app = FfTradeExecutor()

        app.connect(Config['DEFAULT']['IB_HOSTNAME'], 7496, Config['DEFAULT']['IB_CLIENT_ID'])
        sleep(2)
        app.reqCurrentTime()

        threadApp = threading.Thread(target=app.run)
        threadApp.start()

        app.UpdatePositions()
        sleep(5)
        app.GetTodaysExecutions()
        sleep(5)
        app.PlaceOrders()
        print("Waiting...")
        sleep(60)
        app.GetTodaysExecutions()
        sleep(5)
        app.GetTodaysExecutions()
        sleep(5)
        app.GetTodaysExecutions()
        app.disconnect()

    def __downloadTrades(self, cutoff = None):
        if cutoff:
            resp = requests.get(Config['DEFAULT']['FF_URL_BASE'] + "/trades/pending",
                            headers = {
                                'x-rapidapi-key': Config['DEFAULT']['RAPID_KEY'],
                                'api-key': Config['DEFAULT']['FF_API_KEY']
                                },
                            data = {
                                'cutoff': cutoff
                                })
        else:
            resp = requests.get(Config['DEFAULT']['FF_URL_BASE'] + "/trades/pending",
                            headers = {
                                'x-rapidapi-key': Config['DEFAULT']['RAPID_KEY'],
                                'api-key': Config['DEFAULT']['FF_API_KEY']
                                })

        resp.raise_for_status()
        orders = resp.json()
        if len(orders) == 0:
            return

        for order in orders:
            trades = Query()
            if FfJsonDb.count(trades.ID == order['ID']) > 0:
                continue

            order['TIME_STAMP'] = dup.parse(order['TIME_STAMP'])
            FfJsonDb.insert(order)

    def __uploadTrades(self):
        trades = Query()
        executedOrders = FfJsonDb.search((~(trades.TRADE_UPLOADED.exists()) | (trades.TRADE_UPLOADED == False)) & (trades.ORDER_PLACED == True))

        t2upload = []
        for eo in executedOrders:
            FfJsonDb.update({'TRADE_UPLOADED': True}, doc_ids=[eo.doc_id])
            if 'EXEC' not in eo:
                continue

            for et in eo['EXEC']:
                t2upload.append({
                    'id': eo['ID'],
                    'quantity': et['QTY'],
                    'price': et['PRICE'],
                    'time_stamp': et['TIME_STAMP'].isoformat(' ', 'seconds'),
                    })

        resp = requests.post(Config['DEFAULT']['FF_URL_BASE'] + "/trades/executed",
                            headers = {
                                'x-rapidapi-key': Config['DEFAULT']['RAPID_KEY'],
                                'api-key': Config['DEFAULT']['FF_API_KEY']
                                },
                            json = t2upload)

        resp.raise_for_status()


    def DownloadTrades(self):
        try:
            self.__downloadTrades()
        except Exception as exp:
            print(exp)


    def ExecuteTrades(self):
        try:
            self.__executeTrades()
        except Exception as exp:
            print(exp)

    def UploadTrades(self):
        try:
            self.__uploadTrades()
        except Exception as exp:
            print(exp)

