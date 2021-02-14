#single page sample ripping through all endpoints

import requests
import json
from datetime import datetime, date, timedelta

TEST_API_KEY = "146e8b874ec7410b961a6fb0489d53a6" #generated on freefloat https://app.freefloat.us/account/profile
RAPID_KEY = "81e725102bmsh4f32aaae0e709aap194889jsnc9e9cbae7143" #generated on rapidapi https://rapidapi.com/drona/api/freefloatus/details
ROOT = "https://freefloatus.p.rapidapi.com"

#get freefloat portfolio
def getPortfolio():
    resp = requests.get(ROOT + "/portfolio",
                                headers = {
                                    'x-rapidapi-key': RAPID_KEY,
                                    'api-key': TEST_API_KEY
                                    })

    resp.raise_for_status()
    portfolio = resp.json()
    return portfolio

#get pending trades
def getPendingTrades(cutoff=None):
    if cutoff:
        resp = requests.get(ROOT + "/trades/pending",
                        headers = {
                            'x-rapidapi-key': RAPID_KEY,
                            'api-key': TEST_API_KEY
                            },
                        data = {
                            'cutoff': cutoff
                            })
    else:
        resp = requests.get(ROOT + "/trades/pending",
                        headers = {
                            'x-rapidapi-key': RAPID_KEY,
                            'api-key': TEST_API_KEY
                            })

    resp.raise_for_status()
    return resp.json()

#upload your trades
def updateExecutedTrades(trades):
    resp = requests.post(ROOT + "/trades/executed",
                        headers = {
                            'x-rapidapi-key': RAPID_KEY,
                            'api-key': TEST_API_KEY
                            },
                        json = trades)

    resp.raise_for_status()


trades = getPendingTrades(date.today())
trades = getPendingTrades()
portfolio = getPortfolio()

#update pending trades with the computed prices
executed = [{
    'id': x['ID'],
    'quantity': x['QUANTITY'],
    'price': x['LIMIT'],
    'time_stamp': x['TIME_STAMP'],
    } for x in trades[:5]]

updateExecutedTrades(executed)
