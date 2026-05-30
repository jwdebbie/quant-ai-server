import pandas as pd


def calculate_ma(df: pd.DataFrame) -> dict:
    close = df["Close"]
    return {
        "MA5":  close.rolling(5).mean(),
        "MA20": close.rolling(20).mean(),
        "MA60": close.rolling(60).mean(),
    }


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(df: pd.DataFrame) -> dict:
    close = df["Close"]
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return {
        "MACD":        macd_line,
        "MACD_signal": signal,
        "MACD_hist":   macd_line - signal,
    }


def calculate_bollinger(df: pd.DataFrame, period: int = 20, std: int = 2) -> dict:
    close = df["Close"]
    mid = close.rolling(period).mean()
    sigma = close.rolling(period).std()
    return {
        "BB_upper": mid + std * sigma,
        "BB_mid":   mid,
        "BB_lower": mid - std * sigma,
    }


def calculate_volume_flag(df: pd.DataFrame, period: int = 20) -> pd.Series:
    avg_vol = df["Volume"].rolling(period).mean()
    return df["Volume"] > avg_vol * 2


def calculate_indicators(df: pd.DataFrame) -> dict:
    result = {}
    result.update(calculate_ma(df))
    result["RSI"] = calculate_rsi(df)
    result.update(calculate_macd(df))
    result.update(calculate_bollinger(df))
    result["volume_spike"] = calculate_volume_flag(df)
    return result
