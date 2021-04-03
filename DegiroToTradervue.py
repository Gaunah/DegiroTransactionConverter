import argparse
import logging
from time import sleep

import pandas as pd
import requests


def online_lookup(isin):
    logger.info("Try to fetch symbol for: {}".format(isin))
    url = 'https://api.openfigi.com/v2/mapping'
    headers = {'Content-Type': 'text/json'}
    payload = '[{"idType":"ID_ISIN","idValue":"'+isin+'","exchCode":"US"}]'
    try:
        rsp = requests.post(url, headers=headers, data=payload).json()[0]
        logger.debug(rsp)
        sym = rsp["data"][0]["ticker"]
    except Exception:
        logger.critical("Fatal error on api call")
        exit(2)
    return sym


def lookup_symbol(isin):
    try:
        lookup = pd.read_csv("SymbolLookUp.csv")
    except FileNotFoundError:
        lookup = pd.DataFrame(columns=["ISIN", "Symbol"])

    match = (lookup["ISIN"].str.contains(isin))
    symbol = lookup["Symbol"][match]
    if symbol.size == 0:
        sym = online_lookup(isin)
        logger.info("Add to lookUpTable {} {}".format(isin, sym))
        lookup = lookup.append(pd.DataFrame(
            {"ISIN": [isin], "Symbol": [sym]}), ignore_index=True)
        lookup.to_csv("SymbolLookUp.csv", index=False)
        sleep(12) # to stay under the rate limit of 5 per Min; could be lowerd if api key is added
        return sym
    else:
        return symbol.values[0]


def main(dataFilePath):
    data = pd.read_csv(dataFilePath)

    # verify column count
    expectedColumnCount = 19
    logger.info("Verify column count")
    if data.shape[1] != expectedColumnCount:
        logger.error("Input data column count incorect! expected: {} got: {}".format(
            expectedColumnCount, data.shape[1]))
        exit(1)

    # delete unneeded columns
    logger.info("Drop unneeded columns")
    data.drop(data.columns[[2, 4, 5, 8, 9, 10, 11, 12,
              13, 14, 15, 16, 17, 18]], axis=1, inplace=True)

    # change CVS header to match Tradervue generic import format
    logger.info("Change CVS header to match Tradervue generic import format")
    newHeader = ["Date", "Time", "Symbol", "Quantity", "Price"]
    data.columns = newHeader

    # convert date
    logger.info("Convert date")
    data["Date"] = pd.to_datetime(data["Date"], format="%d-%m-%Y")

    # convert Product to Symbol
    logger.info("Convert product name to stock symbol")
    data["Symbol"] = data["Symbol"].apply(lookup_symbol)

    outputFile = "output.csv"
    logger.info("Write to {}".format(outputFile))
    data.to_csv(outputFile, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument("--data",
                        help="CSV file containing the Degiro transaction data e.g.\"Transactions.csv\"",
                        required=True)
    parser.add_argument("--log_level",
                        help="logging level",
                        choices=["DEBUG", "INFO",
                                 "WARNING", "ERROR", "CRITICAL"],
                        default="INFO")
    parser.add_argument("--log_file",
                        help="file were the log gets written to e.g. \"DegiroTradervue.log\"",
                        default=None)
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=numeric_level,
        filename=args.log_file)

    if args.log_file:  # to also print everything that is logged if log_file is provided
        logging.getLogger().addHandler(logging.StreamHandler())

    logger = logging.getLogger("DegiroToTradervueLogger")

    try:
        main(args.data)
    except KeyboardInterrupt:
        logger.info("stopped by user.")
