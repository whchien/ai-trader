import concurrent.futures
import os
from typing import List, Literal, Tuple

import pandas as pd
from twstock import Stock
import yfinance as yf


class StockLoader(object):
    """
    A class to load stock data and save it as CSV files.
    """

    def __init__(
        self,
        stocks: List[str] = ["2330"],
        market: Literal["us", "tw"] = "tw",
        start_ym: Tuple[int, int] = (2024, 1),
        save_dir: str = "./data/tw_stock/",
    ):
        self.stocks = stocks
        self.market = market
        self.start_ym = start_ym
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def log(self, txt: str) -> None:
        print(txt)

    def save_one_stock_to_csv(self, stock_id: str) -> None:
        self.log(f"Working on: {stock_id}")
        try:
            if self.market == "us":
                start = f"{self.start_ym[0]:04d}-{self.start_ym[1]:02d}-01"
                df = yf.download(stock_id, start=start)
                df = df.reset_index()
            elif self.market == "tw":
                stock = Stock(stock_id)
                stock.fetch_from(year=self.start_ym[0], month=self.start_ym[1])
                data_dicts = [d._asdict() for d in stock.data]
                df = pd.DataFrame(data_dicts)
                df = df[["date", "open", "high", "low", "close", "capacity"]]
                df = df.rename({"capacity": "volume"}, axis=1)
            else:
                raise ValueError("Market only supports 'tw' or 'us'")

            filepath = os.path.join(self.save_dir, f"{stock_id}.csv")
            df.to_csv(filepath, index=False)
            self.log(f"Saved: {filepath}")
        except Exception as e:
            self.log(f"Error processing {stock_id}: {e}")

    def run(self) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.save_one_stock_to_csv, stock_id)
                for stock_id in self.stocks
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.log(f"Error fetching data for {e}")

        self.log("Finished all runs.")


def load_example(market: Literal["us", "tw"] = "tw") -> pd.DataFrame:
    datapath = {"tw": "data/tw_stock/2330.csv", "us": "data/us_stock/tsm.csv"}

    date_col = "date" if market == "tw" else "Date"

    if market not in datapath.keys():
        raise ValueError("Market only supports 'tw' or 'us'")

    df = pd.read_csv(
        datapath[market],
        parse_dates=[date_col],
        index_col=[date_col],
    )
    return df


if __name__ == "__main__":
    # loader = StockLoader(["tsm"], "us", (2019, 1), "./data/us_stock/")
    loader = StockLoader(["2330"], "tw", (2019, 1), "./data/tw_stock/")
    loader.run()
