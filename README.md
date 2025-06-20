# WindForecastSantoriniMonolithos

This repository contains simple scripts for collecting weather data for
Santorini (Monolithos) and training basic forecasting models. The
workflow is intentionally lightweight and relies only on the Python
standard library so it can run in restricted environments.

## Data collection

Run `scripts/fetch_data.py` to download historical data from
[Open‑Meteo](https://open-meteo.com/) and placeholders for other sources
(Meteostat, Windy) as well as the latest HTML page from Weather
Underground. The output is stored in `data/data.csv` with the following
columns:

```
time,wind_speed,wind_dir,temp,pressure,humidity,lclouds,mclouds,hclouds,precip,cape,source
```

Fetching real data requires internet access. The placeholders simply
print a message when executed without network connectivity.

## Training models

`scripts/train_models.py` loads `data/data.csv` and trains a few very
basic models:

- **Deterministic**: mean value forecast for each variable.
- **Quantile**: 0.25, 0.5 and 0.75 quantiles using the available data.
- **Ensemble**: average of deterministic and quantile forecasts.
- **LSTM**: placeholder (requires `tensorflow` and is not implemented).

Running the script will print the forecasts to the console.

```bash
python3 scripts/train_models.py
```

The dataset included in the repository is only a small example. For real
forecasts you need to download the full history from 1/1/2020 onwards
using `fetch_data.py`.

