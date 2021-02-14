from tinydb import Query
import sys, os
from datetime import date, datetime, timedelta
from dateutil import parser as dup
from time import sleep
import pytz
import threading

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.connection import Connection
from ibapi.reader import EReader
from ibapi.utils import iswrapper #just for decorator
from ibapi.common import *
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.utils import *
from ibapi.contract import *
from ibapi.order import *
from ibapi.execution import *

from Config import Config
from FfJsonDb import FfJsonDb

def printinstance(inst:Object):
    attrs = vars(inst)
    print(', '.join("%s: %s" % item for item in attrs.items()))

#executes trades through interactive brokers API
#saves executed trades to a local file
#IB is async. this wrapper serializes it
class FfTradeExecutor(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextValidOrderId = 1

    @iswrapper
    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId

    def nextOrderId(self):
        id = self.nextValidOrderId
        self.nextValidOrderId += 1
        return id

    @iswrapper
    def error(self, *args):
        super().error(*args)
        

    @iswrapper
    def winError(self, *args):
        super().error(*args)
        print(current_fn_name(), vars())

    #download existing positions so that you don't sell something you dont have, etc.
    def UpdatePositions(self):
        self.__positionLock = threading.Event()
        self._positions = []
        self.reqPositions()
        self.__positionLock.wait()

    def PlaceOrders(self, asof = datetime.now().replace(minute=0, hour=0, second=0, microsecond=0, tzinfo = pytz.utc)):
        trades = Query()
        pendingTrades = FfJsonDb.search((trades.TIME_STAMP >= asof) & (trades.SYMBOL != 'LIQUIDBEES') & (~(trades.ORDER_PLACED.exists()) | (trades.ORDER_PLACED == False)))
        
        for pt in pendingTrades:
            print(f"{pt['SYMBOL']}: {pt['QUANTITY']}")
            pos = [p for p in self._positions if p['localSymbol'] == pt['SYMBOL'] or p['symbol'] == pt['SYMBOL'][:-1]]

            if pt['QUANTITY'] < 0:
                if len(pos) == 0:
                    print("Can't go short!")
                    continue

                if pt['QUANTITY'] + pos[0]['position'] < 0:
                    print("Can't go short!")
                    continue

            if pt['QUANTITY'] > 0 and len(pos) > 0 and pt['QUANTITY'] == pos[0]['position']:
                print("Looks like already executed!")
                continue

            order = Order()
            order.action = 'BUY' if pt['QUANTITY'] > 0 else 'SELL'
            order.orderType = "MKT"
            order.totalQuantity = abs(pt['QUANTITY'])
            order.orderRef = pt['ID'] #a bigint given by freefloat to track this trade
            
            contract = Contract()
            contract.symbol = pt['SYMBOL']
            contract.secType = "STK"
            contract.currency = "USD"
            contract.exchange = "SMART"

            FfJsonDb.update({'ORDER_PLACED': True}, doc_ids=[pt.doc_id])
            self.placeOrder(self.nextOrderId(), contract, order)
            sleep(10)

    #download executions to reconcile
    def GetTodaysExecutions(self):
        self.__execsLock = threading.Event()
        self.reqExecutions(self.nextOrderId(), ExecutionFilter())
        self.__execsLock.wait()

    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        self.__execsLock.set()

    # automatically called after placeOrder
    # and when reqExecutions is called
    @iswrapper
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)
        print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, execution)
        
        id = execution.orderRef
        if not id:
            return

        execId = execution.execId
        buyOrSell = 1 if execution.side == 'BOT' else -1
        
        ts = dup.parse(execution.time.replace("  ", " "))

        trades = Query()
        orderDeets = FfJsonDb.get(trades.ID == id)
        execDeets = [] #a single order can have multiple trades through IB
        if 'EXEC' in orderDeets:
            orderExecs = [x for x in orderDeets['EXEC'] if x['ID'] == execId]
            if len(orderExecs) > 0:
                return
            execDeets = orderDeets['EXEC']

        execDeets.append({
            'ID': execId,
            'QTY': buyOrSell*execution.shares,
            'TIME_STAMP': ts,
            'PRICE': execution.price,
            })
        FfJsonDb.update({'EXEC': execDeets}, doc_ids=[orderDeets.doc_id])

    @iswrapper
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        super().position(account, contract, position, avgCost)

        self._positions.append({
            'localSymbol': contract.localSymbol,
            'symbol': contract.symbol,
            'secType': contract.secType,
            'position': position,
            'avgCost': avgCost,
            })

    @iswrapper
    def positionEnd(self):
        super().positionEnd()
        self.__positionLock.set()


