#!/usr/bin/env python3
import argparse
import logging
from time import sleep

import pandas as pd
import requests


def online_lookup(isin):
    logger.info("Try to fetch symbol for: {}".format(isin))
    url = 'https://api.openfigi.com/v2/mapping'
    headers = {'Content-Type': 'text/json'}
    if args.apiKey != None:
        # use api key if one is provided
        headers.update({'X-OPENFIGI-APIKEY': args.apiKey})
    else:
        sleepTime = 12
        logger.info(
            "Wait for {}s to stay under the rate limit".format(sleepTime))
        sleep(sleepTime)  # to stay under the rate limit of 5 per Min

    # this should work for US stocks, everything else ¯\_(ツ)_/¯
    payload = '[{"idType":"ID_ISIN","idValue":"'+isin+'","exchCode":"US"}]'
    try:
        rsp = requests.post(url, headers=headers, data=payload)
        if rsp.ok:
            sym = rsp.json()[0]["data"][0]["ticker"]
        else:
            logger.error(rsp.text)
            exit(1)
    except Exception as ex:
        logger.debug(ex)
        logger.critical("Fatal error on api call")
        exit(2)
    return sym


def lookup_symbol(isin):
    try:
        lookup = pd.read_csv("SymbolLookUp.csv")
    except FileNotFoundError:
        lookup = pd.DataFrame(columns=["ISIN", "Symbol"])

    # try to find the symbol in the look up file
    match = (lookup["ISIN"].str.contains(isin))
    symbol = lookup["Symbol"][match]
    # if not found make an api call to openfigi
    if symbol.size == 0:
        sym = online_lookup(isin)
        logger.info("Add to lookUpTable {} {}".format(isin, sym))
        # write back found symbols for furture use
        lookup = pd.concat([lookup, pd.DataFrame(
            {"ISIN": [isin], "Symbol": [sym]})], ignore_index=True)
        lookup.to_csv("SymbolLookUp.csv", index=False)
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
              13, 15, 16, 17, 18]], axis=1, inplace=True)

    # change CVS header to match Tradervue generic import format
    logger.info("Change CVS header to match Tradervue generic import format")
    newHeader = ["Date", "Time", "Symbol", "Quantity", "Price", "Commissions"]
    data.columns = newHeader

    # convert date
    logger.info("Convert dates")
    data["Date"] = pd.to_datetime(data["Date"], format="%d-%m-%Y")

    # convert Product to Symbol
    logger.info("Try to convert ISIN to stock symbol")
    data["Symbol"] = data["Symbol"].apply(lookup_symbol)

    # Write data to "output.csv"
    outputFile = "output.csv"
    logger.info("Finished! Write to {}".format(outputFile))
    data.to_csv(outputFile, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument("--data",
                        help="CSV file containing the Degiro transaction data e.g.\"Transactions.csv\"",
                        required=True)
    parser.add_argument("--apiKey",
                        help="OpenFIGI api key to increase the rate limit on ISIN to Symbol lookups",
                        default=None)
    parser.add_argument("--log_level",
                        help="Logging level",
                        choices=["DEBUG", "INFO",
                                 "WARNING", "ERROR", "CRITICAL"],
                        default="INFO")
    parser.add_argument("--log_file",
                        help="File where the log gets written to e.g. \"DegiroTradervue.log\"",
                        default=None)
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=numeric_level,
        filename=args.log_file)

    if args.log_file:  # also print everything that is logged
        logging.getLogger().addHandler(logging.StreamHandler())

    logger = logging.getLogger("DegiroToTradervueLogger")

    try:
        main(args.data)
    except KeyboardInterrupt:
        logger.info("stopped by user.")
