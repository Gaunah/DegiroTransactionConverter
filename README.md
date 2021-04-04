# Degiro Transaction Converter
> Convert Degiro transaction data to Tradervue generic importer format

DegiroToTradervue.py Python scripts converts your "Transaction.csv" export from [Degiro](https://www.degiro.com/) to the generic import format for [Tradervue](https://www.tradervue.com/).


## Requirements / Installing

* Python 3
  - Pandas Module
  - Requests Module

Modules can be installed with pip and the given requirements.txt
```shell
pip install -r requirements.txt
```

## How It Works

1. Data from Transaction.csv will be read in
2. Degiro export contains Date, Time, ProductName, ISIN, Exchange, Quantity, Price, and much more...
   * Tradervue only needs Date, Time, Symbol, Quantity and Price.
3. Change CVS header to match Tradervue format
4. Convert date format from dd-mm-YYYY to YYYY-mm-dd
5. Try to convert ISIN to stock symbol, this is the "hardest" part.
    * First try to look up symbol in "SymbolLookUp.csv" table
    * If not found make an API call to OpenFIGI.
      - This should work for US Stocks
      - Everything else needs to be added to the "SymbolLookUp.csv" manually or the API call needs to be improved.
      - Without an APIKEY the rate limit is 5 calls per minuted, so we will wait 12 Seconds between calls.
    * Write API call response back to "SymbolLookUp.csv" for furture use.
6. Write data to "output.csv"


## Usage

Basic usage just needs the path to the "Transaction.csv" exported from your [Degiro](https://www.degiro.com/) Account.

Transaction report, for a given date range, can be exported under: _Activity -> Transaction -> Export -> CSV_
![Degiro Export](https://i.imgur.com/5V7KuIP.png)

Invoke the Python script:
```shell
python3 DegiroToTradervue.py --data "path/to/Transaction.csv"
```
"output.csv" will be generated.

Which in turn can be imported by the [Tradervue](https://www.tradervue.com/) generic importer.
![Tradervue Import](https://i.imgur.com/3L4LYEH.png)

### Parameter
```
-h, --help            show help message and exit
--data DATA           [requiered] CSV file containing the Degiro transaction data e.g."Transactions.csv"
--apiKey APIKEY       [optional] OpenFIGI api key to increase the rate limit on ISIN to Symbol lookups
--log_level           [optional] Logging level: {DEBUG,INFO,WARNING,ERROR,CRITICAL}
--log_file LOG_FILE   [optional] File were the log gets written to e.g. "DegiroTradervue.log"
```

The APIKEY can be used to open up the rate limit.
The OpenFIGI API key can be obtained at [www.openfigi.com](https://www.openfigi.com/api#api-key)


## Links

* [Tradervue](https://www.tradervue.com/) - Online Trading Journal
* [Degiro](https://www.degiro.com/) - DEGIRO European brokerage company
* [OpenFiGI](https://www.openfigi.com/) - Financial Instrument Global Identifier api
