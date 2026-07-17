# About This Demo's Data

## This is a synthetic demo dataset, not real hotel data

Every booking, guest name, and price in this system is synthetically generated for demonstration purposes — none of it represents real hotels, real guests, or real transactions. This should always be disclosed plainly if asked, never presented as if it were live production data.

## How the data was generated, and why it's realistic

The synthetic data generator was deliberately built so that booking arrival rates — not just prices — respond to real seasonal and weekly patterns: more check-ins arrive on Friday and Saturday nights and during the October-to-February peak season, and fewer during the June-to-August monsoon low season. Each room's bookings are generated as a sequence of non-overlapping stays walked forward day by day, so no room is ever double-booked and occupancy can never mathematically exceed 100%. The dataset spans two full years of daily history across the three hotels, which gives both forecasting models enough real seasonal signal to learn genuine yearly and weekly patterns from, rather than fitting noise.

## Why this matters for trusting the numbers

Because demand genuinely varies with the calendar in this dataset (not just price), the forecasting models have real patterns to find, and the pricing engine's premium and discount tiers get exercised across a realistic range of occupancy levels rather than always landing in the same bucket. That's what makes the forecast comparison and revenue backtest meaningful demonstrations of the methodology, rather than a trivial exercise on flat, unvarying data.
