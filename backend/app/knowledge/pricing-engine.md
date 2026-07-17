# How the Dynamic Pricing Engine Works

## Overview

HotelIQ's pricing engine is not a machine learning model — it's a set of explainable, rule-based multiplicative factors that take a demand forecast and turn it into one concrete recommended price. Every factor and every tier boundary in this document is fixed, published logic, not a black box. The engine takes a base price and multiplies it by up to five factors, then clips the total multiplier to a floor of 0.7x and a ceiling of 1.5x so no combination of factors can push a price to an extreme.

## The predicted-occupancy factor (the strongest signal)

This is the single biggest lever in the engine, based on the demand forecast for the target date. If predicted occupancy is 90% or higher, the engine applies a 1.40x premium. If predicted occupancy is between 70% and 89%, it applies a smaller 1.15x increase. If predicted occupancy is below 40%, it applies a 0.80x discount to stimulate bookings. Between 40% and 69% predicted occupancy, this factor is neutral — no adjustment.

## The current-occupancy factor (scarcity or urgency)

This looks at how full the hotel is right now, as of the day before the booking decision. If current occupancy is above 85%, a 1.10x scarcity premium applies — the hotel is nearly full, so remaining rooms are worth more. If current occupancy is below 30%, a 0.95x discount applies to help fill empty rooms.

## The weekend factor

Friday or Saturday check-ins receive a flat 1.15x premium, reflecting higher leisure demand on those nights.

## The peak season factor

Check-ins during October through February receive a flat 1.10x premium, reflecting the Indian hospitality high season.

## The lead-time factor

Bookings made 3 days or less before check-in receive a 1.20x last-minute premium. Bookings made 30 days or more in advance receive a 0.95x early-bird discount, rewarding guests who commit early and give the hotel more certainty.

## How the factors combine

All applicable factors multiply together — for example, a weekend check-in with 92% predicted occupancy and a 2-day lead time would combine the 1.40x, 1.15x, and 1.20x factors. The result is clipped to between 0.7x and 1.5x of the base price. The engine also returns a plain-language explanation of exactly which factors fired and why, plus a strategy label (from "Aggressive Discounting" up through "Premium Pricing") describing the overall multiplier band.
