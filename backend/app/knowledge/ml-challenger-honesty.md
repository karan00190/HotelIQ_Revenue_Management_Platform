# Methodological Honesty: What the ML Models Do and Don't Claim

## This system never claims to know how price affects demand

A common mistake in demand forecasting projects is to build a model that claims to predict how changing the price would change demand — "price elasticity." HotelIQ deliberately does not make this claim. The booking data only records bookings that actually happened; there is no record of what would have happened at a different price, no declined offers, no counterfactual data at all. Building a price-elasticity model from data like this would not find a real effect — it would fit sampling noise and present it as insight. This is a structural limitation of the data, not something more data would fix. Because of this, both forecasting models predict the same honest, data-supported thing: occupancy demand, not price sensitivity.

## The revenue backtest and its one real assumption

To test whether either model's forecast would have been useful for pricing, HotelIQ runs a backtest: it takes real historical bookings from the held-out test window and replays them through the same, unmodified pricing engine, once using Prophet's forecast for each date and once using XGBoost's forecast, then compares the simulated revenue to what was actually charged. This carries one unavoidable assumption: that the guest would have booked anyway even at the recommended price. Neither model measures real price sensitivity, so this assumption is stated plainly next to every backtest number rather than hidden in a footnote.

## The comparison that matters most, and the one that matters less

The most reliable comparison from the backtest is XGBoost-priced revenue versus Prophet-priced revenue on the identical real bookings, through the identical pricing formula — only the forecast input changes, which makes this close to a pure arithmetic comparison with little room for the elasticity assumption to distort it. The weaker comparison is either simulated scenario against what actually happened historically, since that comparison fully depends on the constant-demand assumption above.

## A genuinely interesting finding: better forecasts don't always mean more revenue

Across the three hotels, XGBoost is consistently the more accurate forecaster — lower error on every property. But that has not always translated into higher simulated revenue in the backtest. The reason is that the pricing engine reacts to a forecast through discrete tiers (for example, a jump in the price multiplier at 70% and again at 90% predicted occupancy), not a smooth function of the number. Two different forecasts that land in the same tier produce an identical recommended price, regardless of which one was numerically closer to the truth. This is a real, correct finding about how forecast accuracy interacts with a tiered pricing rule — not a bug, and not something to be hidden because it complicates a simpler "our model is better" story.
