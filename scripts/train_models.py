"""Simple training pipeline for wind forecasting models.

This script loads the dataset produced by ``fetch_data.py`` and trains
multiple models:

- Deterministic (mean) forecast
- Quantile forecast (0.25, 0.5, 0.75 quantiles)
- LSTM neural network (placeholder, requires ``tensorflow``)
- Simple ensemble combining the above models

The script expects the dataset ``data/data.csv``. Only the deterministic
and quantile models are implemented using the Python standard library.
"""

import csv
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

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


def main() -> None:
    data = load_dataset(DATA_PATH)
    determ = deterministic_model(data)
    q25 = quantile_model(data, 0.25)
    q50 = quantile_model(data, 0.5)
    q75 = quantile_model(data, 0.75)
    ens = ensemble(determ, [q25, q50, q75])

    print("Deterministic forecast:", determ)
    print("Quantile 0.5 forecast:", q50)
    print("Ensemble forecast:", ens)
    print("LSTM model not implemented - requires tensorflow and real data")


if __name__ == "__main__":
    main()
