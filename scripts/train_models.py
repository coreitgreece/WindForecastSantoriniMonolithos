"""Simple training pipeline for wind forecasting models.

This script loads the dataset produced by ``fetch_data.py`` and trains
multiple models:

- Deterministic (mean) forecast
- Quantile forecast (0.25, 0.5, 0.75 quantiles)
- Simple LSTM neural network using ``numpy`` if available
- Simple ensemble combining the above models

The script expects the dataset ``data/data.csv``. The LSTM is very
lightweight and falls back to a naive forecast if ``numpy`` is not
installed.
"""

import csv
import statistics
from collections import defaultdict
from typing import Dict, List

try:  # optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency may be missing
    np = None

DATA_PATH = "data/data.csv"


def load_dataset(path: str) -> Dict[str, List[float]]:
    columns = defaultdict(list)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k, v in row.items():
                if k == "time" or k == "source":
                    continue
                try:
                    columns[k].append(float(v))
                except (TypeError, ValueError):
                    pass
    return columns


def deterministic_model(data: Dict[str, List[float]]) -> Dict[str, float]:
    return {k: statistics.mean(v) for k, v in data.items() if v}


def quantile_model(data: Dict[str, List[float]], q: float) -> Dict[str, float]:
    return {k: statistics.quantiles(v, n=100)[int(q * 100) - 1] for k, v in data.items() if len(v) >= 4}


def ensemble(determ: Dict[str, float], quant: List[Dict[str, float]]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for k in determ:
        values = [determ[k]] + [q.get(k, determ[k]) for q in quant]
        result[k] = sum(values) / len(values)
    return result


def lstm_model(series: List[float], epochs: int = 10, lookback: int = 24) -> float:
    """Train a minimal LSTM using ``numpy`` and return the next value.

    The implementation is intentionally simple and trains only on a single
    series. If ``numpy`` is unavailable or the series is too short, a
    naive forecast is returned.
    """

    if np is None or len(series) < lookback + 1:
        return series[-1] if series else 0.0

    # Prepare training data
    X = []
    y = []
    for i in range(len(series) - lookback):
        X.append(series[i : i + lookback])
        y.append(series[i + lookback])
    X = np.array(X)
    y = np.array(y)

    input_size = 1
    hidden_size = 8

    # Initialize weights
    rng = np.random.default_rng(0)
    Wf = rng.standard_normal((input_size + hidden_size, hidden_size)) * 0.1
    Wi = rng.standard_normal((input_size + hidden_size, hidden_size)) * 0.1
    Wc = rng.standard_normal((input_size + hidden_size, hidden_size)) * 0.1
    Wo = rng.standard_normal((input_size + hidden_size, hidden_size)) * 0.1
    Wy = rng.standard_normal((hidden_size, 1)) * 0.1

    def step(x_t, h_prev, c_prev):
        z = np.concatenate([x_t, h_prev])
        f = 1 / (1 + np.exp(-z @ Wf))
        i = 1 / (1 + np.exp(-z @ Wi))
        c_hat = np.tanh(z @ Wc)
        c = f * c_prev + i * c_hat
        o = 1 / (1 + np.exp(-z @ Wo))
        h = o * np.tanh(c)
        return h, c

    lr = 0.01
    for _ in range(epochs):
        for seq, target in zip(X, y):
            h = np.zeros(hidden_size)
            c = np.zeros(hidden_size)
            for value in seq:
                h, c = step(np.array([value]), h, c)
            y_pred = h @ Wy
            error = y_pred[0] - target
            # Gradient descent update (very rough, no backprop through time)
            Wy -= lr * error * h.reshape(-1, 1)

    # Forecast next value
    h = np.zeros(hidden_size)
    c = np.zeros(hidden_size)
    for value in series[-lookback:]:
        h, c = step(np.array([value]), h, c)
    return float((h @ Wy)[0])


def main() -> None:
    data = load_dataset(DATA_PATH)
    determ = deterministic_model(data)
    q25 = quantile_model(data, 0.25)
    q50 = quantile_model(data, 0.5)
    q75 = quantile_model(data, 0.75)
    ens = ensemble(determ, [q25, q50, q75])

    lstm_forecast = None
    if "wind_speed" in data:
        lstm_forecast = lstm_model(data["wind_speed"])

    print("Deterministic forecast:", determ)
    print("Quantile 0.5 forecast:", q50)
    print("Ensemble forecast:", ens)
    if lstm_forecast is None:
        print("LSTM model could not run (numpy missing or not enough data)")
    else:
        print("LSTM next wind_speed:", lstm_forecast)


if __name__ == "__main__":
    main()
