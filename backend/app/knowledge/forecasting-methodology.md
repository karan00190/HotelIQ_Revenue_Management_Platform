# Forecasting Methodology: Prophet and XGBoost

## Two forecasting models, evaluated head-to-head

HotelIQ runs two independent forecasting models that both predict the same thing — daily occupancy rate for a hotel — so they can be fairly compared against each other rather than assuming one is better. Prophet is a time-series decomposition model from Meta that breaks a signal into trend, weekly seasonality, and yearly seasonality. XGBoost is a gradient-boosted decision tree model trained on explicit engineered features: calendar signals (day of week, month, peak season), real Indian public holidays, and lag/rolling features of recent occupancy history.

## Why XGBoost trains pooled across all hotels

Prophet trains a separate model per hotel. XGBoost is trained once on data from all three hotels pooled together. This is a deliberate choice: with roughly 600 usable training days per hotel after holding out a test window, pooling gives the tree model substantially more rows to learn general weekday and seasonal patterns from, and lets it share structure across properties. It is still evaluated separately per hotel for a fair comparison against Prophet's per-hotel models.

## How the models are evaluated fairly

Both models are evaluated on an identical held-out time window — the most recent roughly 20% of the two-year history — that neither model ever saw during training. This is a strict time-based split, never shuffled, because a real forecast can only ever use the past to predict the future; shuffling would let a model "see the future" during training and produce misleadingly good numbers. On the properties in this system, XGBoost has consistently shown lower forecast error (mean absolute error) than Prophet, on the order of a 25 to 35 percent reduction depending on the hotel.

## Why this assistant's live forecast tool uses XGBoost, not Prophet

The XGBoost model returns a prediction in well under a second. Prophet, on this system's hosting, can take 30 to 60 seconds or more to train per request because it fits a full Bayesian time-series model from scratch on every call. For a conversational assistant, waiting that long inside a chat turn would be a poor experience and a real timeout risk, so this assistant's forecast and pricing tools use the fast XGBoost model. Prophet's forecast, including its confidence intervals, is still available on the dedicated Forecast page in the app for anyone who wants it.
