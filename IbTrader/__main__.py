import requests
from FfIbTrader import FfIbTrader
from Config import Config

####################################

#get freefloat portfolio
resp = requests.get(Config['DEFAULT']['FF_URL_BASE'] + "/portfolio",
                            headers = {
                                'api_key': Config['DEFAULT']['FF_API_KEY']
                                })

resp.raise_for_status()
portfolio = resp.json()
print(portfolio)

####################################

#execute and upload pending trades
#using the interactive brokers API
ffit = FfIbTrader()
ffit.DownloadTrades()
ffit.ExecuteTrades()
ffit.UploadTrades()