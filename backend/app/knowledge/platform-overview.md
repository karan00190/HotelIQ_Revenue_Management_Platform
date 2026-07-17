# HotelIQ Platform Overview

## What HotelIQ is

HotelIQ is a revenue management platform for hotels. It predicts occupancy demand and turns that prediction into a concrete price recommendation, the way a real revenue management team would. It is built in three layers: a Process layer that ingests and validates booking data, an Analytics layer that pre-aggregates that data into fast-to-read KPIs, and an AI layer that forecasts demand and recommends prices.

## The three hotels in this demo

HotelIQ currently manages three demo properties: Grand Plaza Mumbai (150 rooms, 5-star), Coastal Inn Goa (80 rooms, 4-star), and Heritage Stay Jaipur (60 rooms, 4.5-star). All financial figures in this system are in Indian Rupees (INR).

## The three-layer architecture

The Process layer validates every incoming booking against nine data-quality checks (required fields, parseable dates, logical date ordering, positive prices, duplicate and outlier detection) before it ever reaches the database. The Analytics layer pre-computes daily occupancy, ADR, and RevPAR for every hotel and every calendar day into a `daily_metrics` table, so dashboard reads never have to re-scan raw bookings. The AI layer reads only from that clean, pre-aggregated history — it never touches raw bookings directly — to forecast future demand and recommend prices.

## What this assistant can and can't do

This assistant can answer questions about real data in the system (revenue, occupancy, bookings, forecasts, pricing recommendations) by calling the same underlying functions the dashboard and API use — never by guessing or recalling a number from memory. It can also explain how the platform works (what RevPAR means, how the pricing engine decides on a price, why the system doesn't claim to know how price affects demand). It cannot see real-world data outside this demo dataset, and it cannot take actions like changing prices or creating bookings — it is read-only and advisory.
