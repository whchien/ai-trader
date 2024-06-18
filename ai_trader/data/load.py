import os
from pathlib import Path

import pandas as pd


def load_asml():
    datapath = Path(os.getcwd()) / "./.data/asml.csv"
    df = pd.read_csv(
        datapath,
        parse_dates=["Date"],
        index_col=["Date"],
    )
    return df


def load_test():
    datapath = Path(os.getcwd()) / "./.data/tsmc.csv"
    df = pd.read_csv(
        datapath,
        parse_dates=["date"],
        index_col=["date"],
    )
    return df


def load_tw_stocks():
    open_ = pd.read_csv("./.data/tw_open.csv", parse_dates=["date"], index_col=["date"])
    high = pd.read_csv("./.data/tw_high.csv", parse_dates=["date"], index_col=["date"])
    low = pd.read_csv("./.data/tw_low.csv", parse_dates=["date"], index_col=["date"])
    close = pd.read_csv(
        "./.data/tw_close.csv", parse_dates=["date"], index_col=["date"]
    )
    adj_close = pd.read_csv(
        "./.data/tw_adj_close.csv", parse_dates=["date"], index_col=["date"]
    )
    volume = pd.read_csv(
        "./.data/tw_volume.csv", parse_dates=["date"], index_col=["date"]
    )
    return open_, high, low, close, adj_close, volume


def to_one_stock(stock_id: str, open_, high, low, close, adj_close, volume):
    merged = pd.DataFrame()
    for i, df in enumerate([open_, high, low, close, adj_close, volume]):
        try:
            merged[i] = df.loc[:, stock_id]
        except KeyError:
            merged[i] = None

    merged.columns = ["open", "high", "low", "close", "adj_close", "volume"]
    return merged
