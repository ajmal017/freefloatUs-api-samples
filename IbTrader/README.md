# Python scripts and integrates with the Interactive Brokers API
Does the following:
1. Downloads pending trades from freefloat
1. Executes (at market) and saves the execution details against each order
1. Uploads the execution details to freefloat

Note:
* Trades, execution details and upload flags are saved in a local nosql db: [tinydb](https://github.com/msiemens/tinydb)
* You need to first install the [IB API](http://interactivebrokers.github.io/) client
* Start with paper-trading before taking the plunge



