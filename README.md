# WindForecastSantoriniMonolithos

This repository contains simple scripts for collecting weather data for
Santorini (Monolithos) and training basic forecasting models. The
workflow is intentionally lightweight and relies only on the Python
standard library so it can run in restricted environments.

## Data collection

Run `scripts/fetch_data.py` to download historical data from
[Open‑Meteo](https://open-meteo.com/) and optional data from
[Meteostat](https://meteostat.net/) and [Windy](https://api.windy.com/).
Live observations are fetched from Weather Underground. Set the
environment variables `METEOSTAT_API_KEY` and `WINDY_API_KEY` to enable
these additional sources. The output is stored in `data/data.csv` with
the following columns:

```
time,wind_speed,wind_dir,temp,pressure,humidity,lclouds,mclouds,hclouds,precip,cape,source
```

Fetching real data requires internet access and valid API keys.
Without connectivity the script prints error messages and saves an empty
CSV file.

## Training models

`scripts/train_models.py` loads `data/data.csv` and trains a few basic
models:

- **Deterministic**: mean value forecast for each variable.
- **Quantile**: 0.25, 0.5 and 0.75 quantiles using the available data.
- **Ensemble**: average of deterministic and quantile forecasts.
- **LSTM**: small implementation using ``numpy`` (falls back to a
  placeholder if no data is available).

Running the script will print the forecasts to the console.

```bash
python3 scripts/train_models.py
```

The dataset included in the repository is only a tiny example. For real
forecasts you need to download the full history from 1/1/2020 onwards
using `fetch_data.py` with your API keys configured.

