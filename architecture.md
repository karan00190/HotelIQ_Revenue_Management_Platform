# ARCHITECTURE.md
# HotelIQ - AI-Powered Revenue Management Platform
# Complete Project Documentation and Architecture Reference

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [Database Design](#6-database-design)
7. [Module Documentation](#7-module-documentation)
   - 7.1 [Database Module](#71-database-module)
   - 7.2 [Models Module](#72-models-module)
   - 7.3 [Data Generator Module](#73-data-generator-module)
   - 7.4 [Validation Module](#74-validation-module)
   - 7.5 [ETL Pipeline Module](#75-etl-pipeline-module)
   - 7.6 [Feature Engineering Module](#76-feature-engineering-module)
   - 7.7 [Analytics Service Module](#77-analytics-service-module)
   - 7.8 [Metrics Calculator Module](#78-metrics-calculator-module)
   - 7.9 [Forecasting Service Module](#79-forecasting-service-module)
   - 7.10 [Pricing Engine Module](#710-pricing-engine-module)
   - 7.11 [Query Builder Module](#711-query-builder-module)
8. [API Layer Documentation](#8-api-layer-documentation)
   - 8.1 [Hotels API](#81-hotels-api)
   - 8.2 [Rooms API](#82-rooms-api)
   - 8.3 [Bookings API](#83-bookings-api)
   - 8.4 [Analytics API](#84-analytics-api)
   - 8.5 [Ingestion API](#85-ingestion-api)
   - 8.6 [Smart Queries API](#86-smart-queries-api)
   - 8.7 [Forecasting API](#87-forecasting-api)
9. [Data Flow Documentation](#9-data-flow-documentation)
10. [Feature Engineering Deep Dive](#10-feature-engineering-deep-dive)
11. [Forecasting and Pricing Logic](#11-forecasting-and-pricing-logic)
12. [Business Metrics Explained](#12-business-metrics-explained)
13. [Frontend Architecture Plan](#13-frontend-architecture-plan)
14. [Deployment Architecture Plan](#14-deployment-architecture-plan)
15. [Development Roadmap](#15-development-roadmap)

---

## 1. Project Overview

HotelIQ is an end-to-end revenue management platform for the hospitality industry. It is designed to help hotel managers and revenue teams make smarter pricing and operational decisions by automating data processing, generating predictive insights, and surfacing key performance metrics through a clean API layer.

The platform operates as a three-layer system:

- The Process Layer handles all data engineering work including ingestion, validation, cleaning, transformation, and feature engineering.
- The Analytics Layer calculates revenue management KPIs such as ADR, RevPAR, and occupancy rate, storing them in pre-aggregated tables for fast retrieval.
- The AI Layer uses Facebook Prophet for time-series demand forecasting and a rule-based engine for dynamic pricing recommendations.

The project is built with a production mindset, meaning every component is designed around real-world concerns: data quality, idempotency, transaction safety, performance, and modularity.

---

## 2. Problem Statement

Hotels face three core operational challenges:

**Challenge 1: Pricing Decisions Are Made Without Data**
Most hotel managers set room prices based on intuition or fixed seasonal calendars. They do not have access to demand forecasts, which means they either underprice during high-demand periods (losing revenue) or overprice during low-demand periods (leaving rooms empty).

**Challenge 2: Data Is Fragmented Across Channels**
Bookings come from multiple sources: direct website, OTAs like Booking.com and Expedia, phone reservations, and travel agents. Each source has its own format and data quality issues. There is no single system that consolidates all this data and ensures quality.

**Challenge 3: KPI Calculation Is Manual and Slow**
Industry metrics like ADR (Average Daily Rate) and RevPAR (Revenue Per Available Room) require complex calculations across large datasets. Without automation, these calculations are done in spreadsheets, are error-prone, and take hours to produce.

**What HotelIQ Solves**
HotelIQ automates the entire workflow from data ingestion to insight delivery. It validates data as it enters the system, processes it through a feature engineering pipeline, forecasts future demand using machine learning, and recommends optimal prices for any given date.

---

## 3. System Architecture

### High-Level Architecture

```
+------------------------------------------------------------------+
|                        CLIENT LAYER                              |
|   React/Next.js Dashboard (In Progress)                         |
|   Mobile Interface (Planned)                                     |
+--------------------------------+---------------------------------+
                                 |
                                 | HTTP/REST
                                 |
+--------------------------------v---------------------------------+
|                        API LAYER                                 |
|   FastAPI Application                                            |
|   Auto-generated Swagger/OpenAPI Documentation                  |
|   CORS Middleware                                                |
|   Request Validation (Pydantic)                                 |
+---+----------+----------+----------+----------+----------+------+
    |          |          |          |          |          |
    v          v          v          v          v          v
+-------+ +-------+ +--------+ +--------+ +--------+ +--------+
|Hotels | |Rooms  | |Booking | |Analytics| |Ingest  | |Forecast|
|  API  | |  API  | |  API   | |   API   | |  API   | |  API   |
+---+---+ +---+---+ +---+----+ +---+----+ +---+----+ +---+----+
    |          |          |          |          |          |
    +-----------+----------+----------+----------+----------+
                                 |
                                 v
+------------------------------------------------------------------+
|                      SERVICE LAYER                               |
|                                                                  |
|  +------------------+    +------------------+                   |
|  | ETL Pipeline     |    | Analytics Service|                   |
|  | - Extract        |    | - Revenue Calc   |                   |
|  | - Validate       |    | - Occupancy Calc |                   |
|  | - Clean          |    | - Metrics Store  |                   |
|  | - Transform      |    +------------------+                   |
|  | - Load           |                                           |
|  +------------------+    +------------------+                   |
|                           | AI Services      |                   |
|  +------------------+    | - Forecasting    |                   |
|  | Feature Engineer |    | - Pricing Engine |                   |
|  | - Time Features  |    | - Query Builder  |                   |
|  | - Stay Features  |    +------------------+                   |
|  | - Price Features |                                           |
|  | - Aggregations   |    +------------------+                   |
|  | - Occupancy      |    | Data Validator   |                   |
|  +------------------+    | - 9 QA Checks    |                   |
|                           | - Quality Report |                   |
|                           +------------------+                   |
+------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------+
|                      DATABASE LAYER                              |
|                                                                  |
|   SQLite (Development)     PostgreSQL (Production - Planned)    |
|                                                                  |
|   +----------+   +-------+   +----------+   +---------------+  |
|   |  hotels  |   | rooms |   | bookings |   | daily_metrics |  |
|   +----------+   +-------+   +----------+   +---------------+  |
|                                                                  |
+------------------------------------------------------------------+
```

### Three-Layer Design Philosophy

**Layer 1: Process Layer (Data Engineering)**
This layer is responsible for getting data into the system correctly. It does not care about business logic or intelligence. Its only job is to ensure that every record entering the database is valid, clean, and enriched with ML features. This layer includes the ingestion endpoints, validation framework, cleaning pipeline, feature engineering, and batch loader.

**Layer 2: Analytics Layer (Business Intelligence)**
This layer takes clean data from the database and calculates business metrics. It uses pre-aggregation to store computed values in a DailyMetrics table, so that dashboard queries are instant rather than recalculating from raw bookings on every request. This layer includes the analytics service, metrics calculator, and smart query builder.

**Layer 3: AI Layer (Intelligence and Prediction)**
This layer consumes the processed data and pre-computed metrics to generate predictions and recommendations. It includes the Prophet forecasting model and the dynamic pricing engine. This layer is intentionally separated from data processing so that forecasting models can be retrained independently without affecting the data pipeline.

---

## 4. Technology Stack

### Backend Framework
**FastAPI** was chosen as the web framework because it provides automatic OpenAPI documentation generation, native async support for handling multiple concurrent requests, and tight integration with Pydantic for request and response validation. It is significantly faster than Flask and Django for API workloads.

### Database ORM
**SQLAlchemy** is used as the ORM (Object Relational Mapper). It abstracts the database layer so that switching from SQLite (development) to PostgreSQL (production) requires only a connection string change. It also handles connection pooling, transaction management, and query building.

### Data Validation
**Pydantic** is used for two purposes. First, it validates all incoming API requests and ensures data types, required fields, and constraints are met before any business logic runs. Second, it defines the schema for API responses, ensuring consistent output format.

### Data Processing
**Pandas** is the core data manipulation library. All ETL operations, feature engineering, and data transformations use vectorized Pandas operations rather than Python loops. This is critical for performance. A loop-based approach to feature engineering on 500 records takes approximately 28 seconds. The vectorized Pandas approach does the same work in under 2 seconds.

### Forecasting
**Prophet** is an open-source time-series forecasting library developed by Facebook (Meta). It was chosen because it handles multiple seasonality patterns automatically (daily, weekly, yearly), is robust to missing data and outliers, requires minimal hyperparameter tuning, and provides uncertainty intervals with predictions. Critically, it is completely free and runs locally without any API costs.

### Database
**SQLite** is used during development because it is file-based, requires zero setup, and is perfectly adequate for development and demonstration purposes. The application is designed to switch to **PostgreSQL** for production deployment by changing only the DATABASE_URL environment variable.

---

## 5. Project Structure

```
hoteliq/
|
+-- backend/
|   |
|   +-- app/
|   |   |
|   |   +-- api/
|   |   |   +-- __init__.py
|   |   |   +-- hotels.py              # Hotel CRUD endpoints
|   |   |   +-- rooms.py               # Room CRUD endpoints
|   |   |   +-- bookings.py            # Booking CRUD endpoints
|   |   |   +-- analytics.py           # Revenue metrics endpoints
|   |   |   +-- ingestion.py           # Data upload and ETL endpoints
|   |   |   +-- smart_queries.py       # Pre-built query endpoints
|   |   |   +-- forecasting.py         # Forecast and pricing endpoints
|   |   |
|   |   +-- database/
|   |   |   +-- __init__.py
|   |   |   +-- connection.py          # DB engine, session, dependency
|   |   |   +-- init_db.py             # Table creation on startup
|   |   |
|   |   +-- models/
|   |   |   +-- __init__.py
|   |   |   +-- hotel.py               # SQLAlchemy ORM models
|   |   |   +-- schemas.py             # Pydantic request/response schemas
|   |   |
|   |   +-- services/
|   |   |   +-- __init__.py
|   |   |   +-- data_generator.py      # Synthetic data generation
|   |   |   +-- data_validator.py      # Data quality framework
|   |   |   +-- etl_pipeline.py        # ETL orchestration
|   |   |   +-- feature_engineering.py # ML feature creation
|   |   |   +-- analytics_service.py   # Revenue calculation logic
|   |   |   +-- forecasting_service.py # Prophet model wrapper
|   |   |   +-- pricing_engine.py      # Dynamic pricing logic
|   |   |   +-- query_builder.py       # Pre-built analytical queries
|   |   |
|   |   +-- utils/
|   |   |   +-- __init__.py
|   |   |   +-- metrics_calculator.py  # KPI calculation utilities
|   |   |
|   |   +-- main.py                    # FastAPI app, routers, startup
|   |
|   +-- data/
|   |   +-- uploads/                   # CSV upload staging directory
|   |   +-- sample_bookings.csv        # Sample data for testing
|   |
|   +-- tests/                         # Test suite (planned)
|   +-- .env                           # Environment configuration
|   +-- requirements.txt               # Python dependencies
|   +-- hoteliq.db                     # SQLite database file
|
+-- frontend/                          # Next.js application (in progress)
+-- README.md
+-- ARCHITECTURE.md
+-- LICENSE
```

---

## 6. Database Design

### Design Principles

The database schema follows third normal form (3NF) to eliminate data redundancy. Each table has a single responsibility. Foreign key constraints enforce referential integrity. Indexes are placed on frequently queried columns (dates, hotel_id) for query performance.

### Entity Relationship

```
hotels (1) ----< rooms (many)
hotels (1) ----< bookings (many)
hotels (1) ----< daily_metrics (many)
rooms  (1) ----< bookings (many)
```

### Table: hotels

**Purpose:** Stores hotel property information. This is the top-level entity in the system.

**Columns:**
- id: Primary key, auto-incremented integer
- name: Hotel display name, used in reports and API responses
- location: City and state, used for geographic filtering
- total_rooms: Critical for occupancy calculations. If this is wrong, all occupancy percentages will be wrong.
- star_rating: Used as a pricing tier indicator. Higher-rated hotels have higher base prices.
- created_at: Audit timestamp for when the record was created

**Key Design Decision:** total_rooms is stored here rather than calculated from the rooms table. This allows for a situation where not all rooms are registered in the system but the hotel still has full capacity for occupancy calculations.

### Table: rooms

**Purpose:** Stores individual room records for each hotel. Each room has a type (Standard, Deluxe, Executive, Suite) and a base price that represents the standard rate before dynamic pricing adjustments.

**Columns:**
- id: Primary key
- hotel_id: Foreign key linking room to its hotel
- room_number: Physical room identifier (e.g., 101, 202)
- room_type: Category of room (Standard, Deluxe, Executive, Suite)
- base_price: Standard nightly rate before adjustments
- max_occupancy: Maximum number of guests allowed
- is_available: Boolean flag for current availability status

**Key Design Decision:** base_price is stored per room, not per room_type. This allows individual rooms to have price variations even within the same type.

### Table: bookings

**Purpose:** Core transactional table storing all reservation records. This is the primary data source for all analytics, feature engineering, and forecasting.

**Columns:**
- id: Primary key
- hotel_id: Foreign key to hotels table
- room_id: Foreign key to rooms table
- check_in_date: Date guest checks in (indexed for range queries)
- check_out_date: Date guest checks out
- guest_name: Guest full name
- guest_email: Optional contact email
- num_guests: Number of people in booking
- booking_price: Actual price charged to guest (after discounts)
- base_price: Original standard price before any adjustments
- booking_date: When the reservation was made (used for lead time calculation)
- booking_source: Channel through which booking was made (website, booking.com, direct, expedia, makemytrip)
- status: Current state of booking (confirmed, cancelled, completed)

**Key Design Decision:** Both booking_price and base_price are stored. This allows the system to calculate discount percentages and understand pricing effectiveness over time. booking_price is what was actually charged; base_price is what would have been charged at standard rates.

### Table: daily_metrics

**Purpose:** Pre-aggregated daily performance metrics per hotel. This table is the foundation of the analytics layer. Rather than recalculating KPIs from raw bookings on every dashboard request, the ETL pipeline computes these values once and stores them here. Dashboard queries read from this table and return results in under 200ms.

**Columns:**
- id: Primary key
- hotel_id: Foreign key to hotels table
- date: The calendar date these metrics represent (indexed)
- occupancy_rate: Percentage of rooms occupied (0-100)
- rooms_occupied: Actual count of occupied rooms
- rooms_available: Total rooms in hotel (denormalized for performance)
- total_revenue: Sum of all revenue for that day
- average_daily_rate: ADR for that day (total_revenue / rooms_occupied)
- revenue_per_available_room: RevPAR for that day (total_revenue / rooms_available)
- booking_count: Number of new bookings with check-in on this date
- cancellation_count: Number of cancellations with original check-in on this date
- calculated_at: When the metric was last computed

**Key Design Decision:** This is an OLAP-style pre-aggregation pattern. In a data warehouse, this would be called a fact table. The purpose is to separate the expensive computation (aggregating 500+ booking records) from the frequent read operation (serving dashboard data).

---

## 7. Module Documentation

### 7.1 Database Module

**Location:** app/database/

**Purpose:** Manages all database connectivity, session lifecycle, and table initialization.

**connection.py**

This file creates the SQLAlchemy engine and session factory. The engine is the low-level connection to the database. The session factory produces individual database sessions for each API request.

The get_db function is a FastAPI dependency that is injected into every API endpoint that needs database access. It follows the yield pattern, which ensures that the database session is always properly closed after a request completes, even if an error occurs. This prevents connection leaks.

The DATABASE_URL is read from the environment variable, defaulting to a local SQLite file. For SQLite, the check_same_thread parameter is set to False to allow multiple threads to use the same connection, which is necessary for FastAPI's async workers.

**init_db.py**

This file contains a single function that calls SQLAlchemy's create_all method, which reads all ORM model definitions and creates the corresponding database tables if they do not already exist. This function is called once when the FastAPI application starts. It is idempotent, meaning running it multiple times will not create duplicate tables.

**Aim:** Provide a clean, reliable database connection layer that can be swapped between SQLite and PostgreSQL without changing any application code.

---

### 7.2 Models Module

**Location:** app/models/

**Purpose:** Defines the data structure of the application at two levels: the database schema (SQLAlchemy ORM models) and the API contract (Pydantic schemas).

**hotel.py - ORM Models**

Contains four SQLAlchemy model classes: Hotel, Room, Booking, and DailyMetrics. Each class maps directly to a database table. SQLAlchemy relationship definitions allow navigating between related objects without writing explicit JOIN queries. For example, booking.hotel gives the full Hotel object associated with a booking, and hotel.bookings gives all bookings for a hotel.

**schemas.py - Pydantic Schemas**

Contains request and response schemas for the API. For each entity, there are typically three schemas:

- Base schema: Contains shared fields with their types and validation rules
- Create schema: Inherits from base, adds fields required only for creation (like IDs of related entities)
- Response schema: Inherits from base, adds fields that exist only after creation (like auto-generated ID and timestamps)

Pydantic automatically validates all incoming request data against these schemas. If a request contains an invalid date format, a negative price, or a missing required field, FastAPI returns a 422 Unprocessable Entity response with a detailed error message before the request even reaches the service layer.

The from_attributes = True configuration in each response schema enables Pydantic to convert SQLAlchemy ORM objects directly into the schema format, eliminating the need for manual object mapping.

**Aim:** Create a single source of truth for data structure. The ORM models define what the database stores. The Pydantic schemas define what the API accepts and returns. These two should not be merged to avoid coupling the database structure with the API contract.

---

### 7.3 Data Generator Module

**Location:** app/services/data_generator.py

**Purpose:** Generates realistic synthetic data for development and testing. Real hotel systems take months or years to accumulate meaningful historical data. This module creates 6 months of simulated booking history instantly, enabling immediate testing of analytics and forecasting features.

**What It Generates:**

Three hotels are created with distinct characteristics:
- Grand Plaza Mumbai: 5-star, 150 rooms, premium pricing
- Coastal Inn Goa: 4-star, 80 rooms, mid-range pricing
- Heritage Stay Jaipur: 4.5-star, 60 rooms, heritage pricing

For each hotel, rooms are generated according to a realistic distribution:
- 40% Standard rooms at the lowest price tier
- 30% Deluxe rooms at mid price
- 20% Executive rooms at upper-mid price
- 10% Suite rooms at premium price

Base prices are calculated using random.uniform within realistic Indian hotel price ranges, then multiplied by the hotel's star rating factor to ensure higher-rated hotels have higher prices.

For bookings, 500 records are generated over a 6-month period. The pricing simulation includes:
- Weekend premium: Friday and Saturday check-ins get a 20-50% price increase
- Seasonal adjustment: Peak months (October to February) get a 10-30% increase
- Off-season discount: Monsoon months (June to August) get a 10-30% discount
- Status distribution: 90% confirmed, 10% cancelled
- Completion logic: Bookings with past check-out dates are marked as completed

The data generation is idempotent. If the database already contains records, the generator skips creation rather than inserting duplicates.

**Aim:** Enable immediate end-to-end testing of the entire platform without needing real booking data. The generated data should be statistically realistic enough to produce meaningful forecasts and analytics.

---

### 7.4 Validation Module

**Location:** app/services/data_validator.py

**Purpose:** Acts as the quality gate for all incoming data. No record enters the database without passing through this validator. The module contains two classes: DataQualityReport and BookingDataValidator.

**DataQualityReport Class**

A container that accumulates validation results during the checking process. It maintains three separate lists:
- errors: Critical issues that prevent data from being loaded
- warnings: Non-critical issues that are flagged but do not block loading
- info: Informational messages about the validation process

The is_valid method returns True only when the errors list is empty. A data quality report is always returned to the caller, giving full transparency into what was found.

**BookingDataValidator Class**

Executes nine validation checks against a Pandas DataFrame:

Check 1 - Required Columns:
Verifies that all mandatory columns (hotel_id, room_id, check_in_date, check_out_date, guest_name, num_guests, booking_price, base_price) are present in the DataFrame. If any are missing, validation fails immediately without running further checks, because subsequent checks depend on these columns existing.

Check 2 - Empty DataFrame:
Verifies the DataFrame contains at least one row. An empty file is technically valid CSV but has no value and should be rejected.

Check 3 - Null Values:
Counts null values in each required column. Any null in a required column is an error. Nulls in optional columns are noted as warnings.

Check 4 - Date Type Conversion:
Attempts to convert the check_in_date and check_out_date columns to Pandas datetime objects. If conversion fails for any row, it means the date format is unrecognizable and is an error.

Check 5 - Logical Date Validation:
After date conversion, compares check_out_date against check_in_date for every row. Any row where check-out is on or before check-in violates basic business logic and is an error.

Check 6 - Price Validation:
Checks that booking_price and base_price are both greater than zero for all rows. Negative or zero prices are either data entry errors or indicate corrupted data.

Check 7 - Guest Count Validation:
Verifies num_guests is greater than zero for all rows. A booking with zero guests makes no sense.

Check 8 - Duplicate Detection:
Identifies rows where hotel_id, room_id, and check_in_date combination appears more than once. This likely indicates the same booking was submitted twice. This is flagged as a warning rather than an error because one could be legitimate and one a duplicate.

Check 9 - Outlier Detection:
Calculates the mean and standard deviation of booking_price. Any price more than three standard deviations above the mean is flagged as a potential outlier. This could be a legitimate premium booking or a data entry error (like accidentally entering 150000 instead of 15000).

After all checks, the validator generates statistics about the dataset: total records, date range, price range, unique hotels, unique rooms.

The clean_dataframe method performs non-destructive repairs on the data: converting data types, filling optional columns with sensible defaults, stripping whitespace from strings, and removing verified duplicates.

**Aim:** Prevent garbage data from corrupting the analytics and forecasting models. In revenue management, a single incorrect price record can skew ADR calculations and produce misleading forecasts. The validation framework enforces business rules programmatically rather than relying on human inspection.

---

### 7.5 ETL Pipeline Module

**Location:** app/services/etl_pipeline.py

**Purpose:** Orchestrates the complete data processing workflow from raw input to clean, feature-enriched database records. ETL stands for Extract, Transform, Load. This module coordinates the three phases and all sub-processes within them.

**ETLPipeline Class**

The class is initialized with a database session and creates instances of the validator and feature engineer, making it the central coordinator for the entire data processing workflow.

**Extract Phase**

The pipeline supports two extraction sources:

extract_from_csv reads a CSV file from the local filesystem using Pandas read_csv. The file path is provided by the ingestion API endpoint after saving the uploaded file temporarily. The function logs how many records were extracted.

extract_from_database queries the bookings table using SQLAlchemy and converts the results to a Pandas DataFrame. This is used for re-processing existing records through the feature engineering pipeline, for example when new features are added and historical data needs to be updated.

**Transform Phase**

The transform method executes validation and cleaning before feature engineering:

1. Calls validate_dataframe and receives a DataQualityReport
2. If validation fails (errors exist), returns immediately with the report and the unmodified DataFrame
3. If validation passes, calls clean_dataframe to standardize the data
4. Calls create_all_features to generate all ML features

**Load Phase**

The load_to_database method handles insertion with several production-grade considerations:

Batch Processing: Records are inserted in batches of 100. Each batch is committed as a single transaction. This improves performance over committing one record at a time and limits the damage of any single failure to at most 100 records.

Idempotency: Before inserting each record, the pipeline checks whether a booking with the same hotel_id, room_id, and check_in_date already exists. If it does, the record is skipped and counted as a duplicate. This means the pipeline can be run multiple times on the same data without creating duplicates.

Error Handling: If a batch commit fails (due to constraint violations or connection issues), the transaction is rolled back, preserving the integrity of the already-committed batches. Errors are counted and included in the result report.

Column Selection: The full feature-engineered DataFrame has 58 columns, but the bookings table only has the original 12 columns. The load phase selects only the database columns, discarding the engineered features. The features were used during the transform phase for validation and future ML model training but are not stored in the bookings table.

**Run Full Pipeline**

The run_full_pipeline method combines all phases into a single callable, accepts a source parameter ('csv' or 'database'), and returns a comprehensive result dictionary including: success status, duration in seconds, validation report, load statistics, and feature summary.

**Aim:** Provide a reliable, observable, and safe data processing workflow. The pipeline should never partially corrupt data, always report what it did, and be runnable multiple times without side effects.

---

### 7.6 Feature Engineering Module

**Location:** app/services/feature_engineering.py

**Purpose:** Transforms raw booking records into rich, ML-ready feature sets. Takes 8 raw columns as input and produces 50+ derived features as output. This module encodes hotel industry domain knowledge into numerical and categorical features that machine learning models can use to find patterns.

**FeatureEngineer Class**

The class contains five static methods, each responsible for a specific category of features. All methods use Pandas vectorized operations and receive and return a DataFrame.

**create_time_features**

Extracts temporal information from the check_in_date column. Time features are among the most powerful predictors in hotel demand forecasting because hotel occupancy follows very strong temporal patterns.

- day_of_week: Integer 0-6 (Monday=0, Sunday=6). Hotels universally charge more on Fridays and Saturdays.
- day_of_month: Integer 1-31. Useful for detecting patterns around holidays and month-end business travel.
- month: Integer 1-12. Captures seasonal demand patterns.
- quarter: Integer 1-4. Useful for quarterly revenue analysis.
- year: Integer. Allows the model to detect year-over-year growth trends.
- week_of_year: Integer 1-52. More granular than month for detecting specific event weeks.
- is_weekend: Binary 1 or 0. Friday and Saturday = 1, all other days = 0. Direct signal for weekend pricing.
- season: String mapped from month. Encodes the Indian hospitality calendar: winter (Dec-Feb), spring (Mar-May), monsoon (Jun-Aug), autumn (Sep-Nov).
- is_peak_season: Binary. October through February is peak tourism season in India. Major conferences and festivals drive demand.
- is_holiday_season: Binary. December, April, and October are holiday-heavy months driving leisure travel.

**create_stay_features**

Captures characteristics of the stay duration and booking behavior.

- length_of_stay: Number of days between check-in and check-out. Calculated as (check_out_date - check_in_date).days. Business travelers typically stay 1-2 nights; leisure travelers 3-7 nights; extended stays 7+ nights.
- stay_category: Categorical bucket of length_of_stay: short (1 day), medium (2-3 days), long (4-7 days), extended (8+ days). Useful for customer segmentation.
- lead_time_days: Days between booking_date and check_in_date. Measures how far in advance the guest planned. Business travelers often book 1-3 days in advance. Leisure travelers book 2-6 weeks ahead.
- is_last_minute: Binary. If lead_time_days is 3 or fewer, this is a last-minute booking. Last-minute guests are typically willing to pay premium prices because they have less flexibility.

**create_pricing_features**

Derives pricing intelligence from the raw price columns.

- price_per_night: booking_price divided by length_of_stay. This normalizes prices across different stay durations so that a 3-night stay at 12,000 total is comparable to a 1-night stay at 4,000 total.
- discount_pct: Calculated as (base_price - booking_price) / base_price * 100. Represents how much discount was applied. Helps understand pricing elasticity: did guests only book when discounted, or did they book at full price?
- price_category: Bins price_per_night into budget (under 3,000), mid_range (3,000-6,000), premium (6,000-10,000), or luxury (10,000+) using Pandas cut function.

**create_aggregated_features**

Creates rolling window features that capture recent trends. These are particularly valuable for forecasting because they give the model context about recent market conditions.

All rolling calculations are performed using groupby on hotel_id before applying the rolling function. This ensures that rolling averages are calculated within each hotel's history, not across all hotels combined.

- avg_price_7d: 7-day rolling average of booking_price. Represents short-term price trends.
- avg_price_30d: 30-day rolling average. Represents medium-term price trends. If avg_price_30d is rising, demand has been strong for the past month.
- booking_count_7d: Number of bookings in the past 7 days. A demand velocity signal.
- booking_count_30d: Number of bookings in the past 30 days. Longer-term demand signal.
- prev_booking_price: The booking_price of the previous booking for the same room. A lag feature that allows the model to detect price momentum.

**create_occupancy_features**

Adds supply-demand context to each booking record by calculating how full the hotel was on that booking's check-in date.

- hotel_total_rooms: Fetched from the hotels table for the booking's hotel_id. Denormalized into the features for convenience.
- occupancy_rate: For each unique hotel_id + check_in_date combination, counts the number of bookings and divides by total_rooms. This requires a groupby aggregation followed by a merge back to the original DataFrame.

**create_all_features**

Orchestrates all five feature creation methods in sequence. Logs progress after each step. Returns the fully enriched DataFrame. Also calls get_feature_summary to produce a summary dictionary showing total features created and a breakdown by category.

**Performance Philosophy**

The critical design principle of this module is vectorization. Every calculation is expressed as a Pandas operation on entire columns rather than a row-by-row Python loop. This is possible because Pandas operations are implemented in C under the hood. The practical result is a 15x performance improvement: 500 records take 1.8 seconds with vectorization versus 28 seconds with loops. At production scale (thousands of records daily), this difference becomes critical.

**Aim:** Transform raw transactional data into rich numerical representations that expose hidden patterns in the data. The goal is to encode what a human revenue manager knows intuitively (weekends are expensive, last-minute guests pay more, monsoon is slow season) into features that a machine learning model can use to make predictions.

---

### 7.7 Analytics Service Module

**Location:** app/services/analytics_service.py

**Purpose:** Provides functions that calculate revenue management KPIs from raw booking records. Used by the analytics API endpoints and the metrics calculator.

**calculate_revenue_metrics**

The primary analytics function. Accepts optional filters for hotel_id, start_date, and end_date. Queries the bookings table for confirmed and completed bookings within the filters, then calculates:

Total Revenue: Simple sum of all booking_price values.

Total Room Nights: For each booking, calculates the duration as (check_out_date - check_in_date).days and sums across all bookings. This is different from booking count because a 5-night stay contributes 5 room nights.

ADR (Average Daily Rate): total_revenue divided by total_room_nights. This tells the average price charged per occupied room per night. A 10,000 booking for 2 nights contributes 5,000 to ADR, not 10,000.

Occupancy Rate: Calculated as (total_room_nights / available_room_nights) * 100. available_room_nights is the total rooms multiplied by days in the period. For example, a 150-room hotel over 30 days has 4,500 available room nights.

If no bookings are found for the filters, all metrics return zero rather than causing a division by zero error.

**get_daily_statistics**

Returns metrics for a specific hotel on a specific date. Queries for all bookings where check_in_date is on or before the target date AND check_out_date is after the target date. This correctly handles multi-night stays: a guest who checked in 3 days ago and checks out tomorrow is still occupying a room today.

**Aim:** Provide accurate, filter-aware KPI calculations as reusable service functions that multiple API endpoints can call consistently.

---

### 7.8 Metrics Calculator Module

**Location:** app/utils/metrics_calculator.py

**Purpose:** Calculates daily metrics for specific hotels and dates, then persists them to the daily_metrics table. This is the module that powers the pre-aggregation strategy.

**calculate_daily_metrics**

For a given hotel_id and target_date:

1. Fetches the hotel record to get total_rooms
2. Queries bookings that overlap the target date (check_in <= target AND check_out > target)
3. Calculates occupancy_rate, rooms_occupied, total_revenue, ADR, and RevPAR
4. Counts new bookings and cancellations specifically for that check-in date
5. Checks if a daily_metrics record already exists for that hotel+date
6. If it exists, updates the values. If not, creates a new record.
7. Commits to the database and returns the metric object.

**calculate_date_range_metrics**

Loops over every date between start_date and end_date, calling calculate_daily_metrics for each date. This is used after bulk data ingestion to populate the metrics table for the entire date range of the imported data.

**recalculate_all_metrics**

Finds the earliest check_in_date and latest check_out_date in the bookings table, then calls calculate_date_range_metrics for every hotel across that entire date range. This is a heavy operation run in the background via FastAPI's BackgroundTasks. Used after significant data changes.

**Aim:** Pre-compute expensive aggregations and store them as first-class data, enabling sub-200ms dashboard API responses regardless of how many raw booking records exist.

---

### 7.9 Forecasting Service Module

**Location:** app/services/forecasting_service.py

**Purpose:** Wraps Facebook Prophet to provide hotel occupancy forecasting. Takes historical occupancy data from the daily_metrics table and produces 30-day predictions with confidence intervals.

**DemandForecaster Class**

**prepare_training_data**

Queries the daily_metrics table for a specific hotel over the specified number of historical days (default 180 days). Converts the results into a Pandas DataFrame with exactly two columns: ds (the date, as Prophet requires) and y (the occupancy_rate, the target variable to predict).

Enforces a minimum of 30 days of data. If insufficient history exists, raises a ValueError. Prophet needs at least this much data to detect seasonality patterns.

**train**

Initializes a Prophet model with three types of seasonality enabled: daily (weekday/weekend patterns), weekly (within-week cycles), and yearly (seasonal patterns across months). The changepoint_prior_scale parameter controls how flexible the trend is: lower values produce smoother trends that are less likely to overfit.

A custom weekend seasonality is added with period 7 (weekly cycle) and fourier_order 3 (how many Fourier terms to use for the seasonality curve).

The model is fitted on the prepared training DataFrame. Prophet internally decomposes the time series into trend, seasonality, and holiday components.

**forecast**

Calls Prophet's make_future_dataframe to create a DataFrame of future dates. Then calls predict to generate occupancy estimates for each date. The predictions include yhat (the point estimate), yhat_lower (lower confidence bound), and yhat_upper (upper confidence bound).

Clips all predicted values to the 0-100 range because occupancy cannot be negative or exceed 100%.

Filters to return only future dates, not the historical fitted values.

**get_forecast_summary**

Converts the forecast DataFrame into a structured dictionary with summary statistics (mean, min, max, median predicted occupancy) and a list of individual daily predictions. This is the format returned by the API endpoint.

**Aim:** Provide accessible demand forecasting without requiring data science expertise from the API consumer. A simple POST request to train and a GET request to forecast gives hotel managers 30-day occupancy predictions automatically.

---

### 7.10 Pricing Engine Module

**Location:** app/services/pricing_engine.py

**Purpose:** Takes demand forecast data and contextual factors to generate actionable pricing recommendations. This is a rule-based engine, not a machine learning model. Rules are based on standard revenue management principles used in the hotel industry.

**DynamicPricingEngine Class**

**calculate_price_multiplier**

Accepts five inputs and returns a single price multiplier (a float between 0.7 and 1.5).

Predicted Occupancy Factor: The strongest signal. Very high predicted demand (90%+) justifies a 40% price increase because scarcity allows premium pricing. Very low demand (under 40%) requires discounting to stimulate bookings.

Current Occupancy Factor: The current actual occupancy of the hotel. If the hotel is already over 85% full, an additional scarcity premium of 10% is applied. If it is under 30% full, a 5% discount is applied to encourage bookings.

Weekend Factor: A flat 15% premium applied when the check-in date falls on a Friday or Saturday. This reflects universal weekend demand patterns in hospitality.

Peak Season Factor: A flat 10% premium for October through February check-ins. This reflects India's tourism high season.

Lead Time Factor: Last-minute bookings (3 days or fewer before check-in) receive a 20% premium. Guests with no flexibility are willing to pay more. Advance bookings (30+ days ahead) receive a 5% discount to reward and encourage early commitment.

The final multiplier is the product of all applicable factors, capped at a minimum of 0.7 (maximum 30% discount) and a maximum of 1.5 (maximum 50% premium). The cap prevents extreme recommendations.

**get_pricing_recommendation**

Applies the multiplier to the base_price to get recommended_price. Calculates price_change_percent. Assembles a list of factors explaining why each adjustment was made. Assigns a pricing strategy label: Premium Pricing, Moderate Increase, Maintain Base Price, Value Pricing, or Aggressive Discounting. Returns the full recommendation as a dictionary.

**Aim:** Give hotel managers a specific, justified pricing recommendation for any future date rather than requiring them to manually weigh demand signals. The recommendation comes with an explanation so the manager understands why the price is what it is.

---

### 7.11 Query Builder Module

**Location:** app/services/query_builder.py

**Purpose:** Provides pre-built analytical queries for the most common questions hotel managers ask. This module eliminates the need for hotel staff to write SQL or use complex BI tools. It also eliminates the need for a paid LLM API for natural language processing.

**QueryBuilder Class**

The class is initialized with a database session and provides seven query methods:

**get_total_revenue:** Aggregates total revenue and booking count from the bookings table. Accepts optional hotel_id, start_date, and end_date filters. Uses SQLAlchemy func.sum and func.count for efficient database-side aggregation.

**get_occupancy_stats:** Reads from the daily_metrics table for a specific hotel. Calculates average, maximum, and minimum occupancy rates across the filtered date range. Designed to answer "What was my average occupancy last month?"

**get_top_bookings:** Returns the highest-priced bookings (sorted by booking_price descending) or most recent bookings (sorted by check_in_date descending). Accepts a limit parameter. Designed to answer "Show me my biggest bookings."

**get_booking_source_distribution:** Groups bookings by booking_source and calculates count and total revenue for each channel. Calculates percentage of total bookings per source. Designed to answer "Where do my bookings come from?"

**get_weekend_vs_weekday_comparison:** Iterates over all bookings, classifies each as weekend (Friday or Saturday check-in) or weekday, and calculates count, total revenue, and average price for each group. Also calculates weekend_premium_percent: how much higher weekend average price is compared to weekday. Designed to answer "How much more do I make on weekends?"

**get_cancellation_analysis:** Calculates total bookings, cancelled bookings, cancellation rate, and total lost revenue from cancelled bookings. Designed to answer "What is my cancellation rate and how much revenue am I losing?"

**get_popular_room_types:** Joins the rooms and bookings tables, groups by room_type, and counts bookings and calculates average price per type. Returns top N room types sorted by booking count. Designed to answer "Which rooms are most popular?"

**get_available_queries:** Returns a descriptive list of all available queries with parameter documentation. Used by the API endpoint that shows users what they can ask.

**Aim:** Answer the 80% of analytical questions that hotel managers ask repeatedly, with fast pre-optimized database queries, zero AI API costs, and consistent reliable results.

---

## 8. API Layer Documentation

### Design Principles

All API endpoints follow REST conventions. Resources are nouns, not verbs. HTTP methods convey intent (GET for retrieval, POST for creation, PATCH for partial updates, DELETE for removal). Response codes are semantic (200 OK, 201 Created, 204 No Content, 400 Bad Request, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error).

Every endpoint has a docstring that appears in the auto-generated Swagger UI, explaining the purpose, parameters, and example responses.

---

### 8.1 Hotels API

**Location:** app/api/hotels.py

**Prefix:** /hotels

**Endpoints:**

GET /hotels/
Returns paginated list of all hotels. Supports skip and limit query parameters for pagination.

GET /hotels/{hotel_id}
Returns a single hotel by ID. Returns 404 if not found.

POST /hotels/
Creates a new hotel. Validates the hotel name is unique. Returns 400 if a hotel with the same name already exists. Returns 201 on success.

DELETE /hotels/{hotel_id}
Deletes a hotel by ID. Returns 404 if not found. Returns 204 No Content on success.

---

### 8.2 Rooms API

**Location:** app/api/rooms.py

**Prefix:** /rooms

**Endpoints:**

GET /rooms/
Returns all rooms. Optional hotel_id query parameter filters by hotel.

GET /rooms/{room_id}
Returns a single room by ID.

POST /rooms/
Creates a new room linked to an existing hotel.

---

### 8.3 Bookings API

**Location:** app/api/bookings.py

**Prefix:** /bookings

**Endpoints:**

GET /bookings/
Returns paginated bookings with multiple optional filters: hotel_id, status, start_date, end_date. Results are ordered by check_in_date descending.

GET /bookings/{booking_id}
Returns a single booking by ID.

POST /bookings/
Creates a new booking. Validates dates, prices, and guest count via Pydantic schema.

PATCH /bookings/{booking_id}/cancel
Cancels a specific booking by setting its status to 'cancelled'.

---

### 8.4 Analytics API

**Location:** app/api/analytics.py

**Prefix:** /analytics

**Endpoints:**

GET /analytics/revenue
Primary revenue analytics endpoint. Returns total_revenue, total_bookings, average_daily_rate, and occupancy_rate for a specified period. Defaults to the last 30 days if no dates are provided.

GET /analytics/daily/{hotel_id}
Returns metrics for a single hotel on a specific date. Defaults to today if no date provided.

GET /analytics/summary
Returns a system-wide summary: total hotels, total rooms, total bookings, active confirmed bookings, current month revenue, and current month occupancy.

---

### 8.5 Ingestion API

**Location:** app/api/ingestion.py

**Prefix:** /ingestion

**Endpoints:**

POST /ingestion/upload-csv
Accepts a CSV file upload. Validates file is a .csv extension. Reads the file content into a DataFrame and saves a timestamped copy to the data/uploads directory. Runs the full ETL pipeline and returns the complete result including validation report, load statistics, and feature summary.

POST /ingestion/process-existing-data
Re-processes existing database records through the ETL pipeline. Useful after feature engineering changes to regenerate features on historical data. Accepts optional hotel_id and start_date filters.

POST /ingestion/calculate-metrics
Triggers daily metrics calculation for a specific hotel over a date range. Returns count of metrics calculated.

POST /ingestion/recalculate-all-metrics
Schedules a full metrics recalculation as a background task to avoid request timeout. Returns immediately with a started status message.

GET /ingestion/data-quality-check
Extracts all bookings from the database and runs the validation framework on them, returning a quality report. Does not modify any data.

GET /ingestion/feature-summary
Extracts a sample of bookings, runs feature engineering, and returns a summary of all features created with sample values. Useful for verifying the pipeline is working correctly.

---

### 8.6 Smart Queries API

**Location:** app/api/smart_queries.py

**Prefix:** /smart-queries

**Endpoints:**

GET /smart-queries/available
Returns documentation for all available pre-built queries including parameter descriptions.

GET /smart-queries/total-revenue
Revenue aggregation with optional filters.

GET /smart-queries/occupancy-stats/{hotel_id}
Occupancy statistics with optional date filters.

GET /smart-queries/top-bookings
Configurable top N bookings by price or date.

GET /smart-queries/booking-sources
Booking channel distribution and revenue by source.

GET /smart-queries/weekend-vs-weekday/{hotel_id}
Performance comparison between weekend and weekday periods.

GET /smart-queries/cancellations
Cancellation rate and lost revenue analysis.

GET /smart-queries/popular-rooms/{hotel_id}
Room type popularity and average pricing.

---

### 8.7 Forecasting API

**Location:** app/api/forecasting.py

**Prefix:** /forecast

**Endpoints:**

POST /forecast/train/{hotel_id}
Trains a Prophet forecasting model for a specific hotel using its historical occupancy data from the daily_metrics table. The days_back parameter (default 180) controls how much history to use. Returns training status and data statistics.

GET /forecast/predict/{hotel_id}
Trains the model and immediately generates a forecast for days_ahead days (default 30, maximum 90). Returns the full forecast with confidence intervals.

GET /forecast/pricing-recommendation/{hotel_id}
The most complex endpoint. Trains the forecasting model, generates a forecast for the target_date, extracts the predicted occupancy for that date, calculates contextual factors (is_weekend, is_peak_season, lead_time_days), retrieves current occupancy from the most recent daily metric, and passes all these inputs to the pricing engine. Returns the complete pricing recommendation with strategy explanation.

---

## 9. Data Flow Documentation

### Flow 1: CSV Upload Flow

Step 1: Hotel manager selects a CSV file through the API client (Swagger UI or frontend form).

Step 2: FastAPI receives the multipart form upload. The ingestion endpoint reads the file bytes, decodes as UTF-8, and passes to Pandas read_csv.

Step 3: The file is saved to data/uploads/ with a timestamp prefix for debugging purposes.

Step 4: ETLPipeline.run_full_pipeline is called with source='csv' and the file path.

Step 5 (Extract): The pipeline reads the CSV file into a DataFrame and logs the record count.

Step 6 (Validate): BookingDataValidator.validate_dataframe runs all 9 checks and produces a DataQualityReport. If any critical errors are found, the pipeline stops and returns the report with success=False.

Step 7 (Clean): BookingDataValidator.clean_dataframe runs on the valid DataFrame: converts dates, fills defaults, strips strings, removes duplicates.

Step 8 (Transform): FeatureEngineer.create_all_features runs all 5 feature creation methods on the cleaned DataFrame. Output has 58 columns.

Step 9 (Load): load_to_database selects the 12 original columns and inserts in batches of 100. Each batch checks for duplicates before inserting. Commits each batch independently. Tracks loaded, skipped, and error counts.

Step 10 (Post-Process): The caller can subsequently trigger calculate_metrics to populate the daily_metrics table for the date range of the uploaded data.

Step 11 (Response): The endpoint returns a structured response containing the filename, timestamp, validation report, load statistics, feature summary, and total execution time.

### Flow 2: Analytics Query Flow

Step 1: Client sends GET /analytics/revenue with filters.

Step 2: FastAPI parses and validates query parameters through the endpoint function signature.

Step 3: The endpoint calls calculate_revenue_metrics with the validated parameters.

Step 4: The service builds a SQLAlchemy query with the provided filters, executing a database query that returns only confirmed and completed bookings.

Step 5: Python calculates total revenue by summing booking_price values, total room nights from stay durations, ADR from revenue/nights, and occupancy from room nights/available room nights.

Step 6: The result dictionary is returned to the endpoint and serialized to JSON.

Step 7: FastAPI returns the response with a 200 status code.

Total time: approximately 100-200ms for 500 booking records.

### Flow 3: Pricing Recommendation Flow

Step 1: Client calls GET /forecast/pricing-recommendation/{hotel_id} with target_date and base_price.

Step 2: Endpoint verifies hotel exists in database.

Step 3: DemandForecaster.train queries daily_metrics for 180 days of occupancy history and fits Prophet model.

Step 4: DemandForecaster.forecast generates 90-day predictions. The target_date prediction is extracted.

Step 5: Contextual factors are calculated from the target_date: dayofweek for is_weekend, month for is_peak_season, days from today for lead_time_days.

Step 6: Most recent daily_metrics record provides current_occupancy.

Step 7: DynamicPricingEngine.get_pricing_recommendation calculates multiplier from all factors.

Step 8: recommended_price = base_price * multiplier. Strategy and factor labels are assembled.

Step 9: Full recommendation returned to client including base price, recommended price, percentage change, strategy name, reasoning factors, and confidence level.

---

## 10. Feature Engineering Deep Dive

### Why Feature Engineering Matters

A machine learning model cannot learn from raw strings like "2024-11-20" or categories like "confirmed". Features must be numerical and must carry predictive information.

More importantly, raw data alone does not encode domain knowledge. A forecasting model given only check_in_date and booking_price has no way of knowing that November is peak season in India or that Friday bookings are more valuable than Tuesday bookings. Feature engineering injects this domain knowledge explicitly.

The transformation from 8 raw columns to 58 features is not about creating complexity. It is about making the patterns in the data visible to the model.

### Feature Interaction

Some features interact with each other in ways that are more predictive than either feature alone:
- is_weekend AND is_peak_season together indicate a high-revenue scenario
- short length_of_stay AND is_last_minute together suggest a business traveler willing to pay premium rates
- low booking_count_7d AND low occupancy_rate together signal an opportunity to run promotions

The pricing engine uses multiple factors simultaneously to capture these interactions.

### Vectorization Implementation

All feature creation uses Pandas column operations:

Extracting day of week uses the dt.dayofweek accessor on a datetime column. This processes all rows simultaneously.

Mapping months to seasons uses the map function with a dictionary. This is a vectorized lookup.

Calculating rolling averages uses groupby followed by transform with a rolling lambda. This applies the window function within each hotel's data independently, ensuring cross-hotel contamination does not occur.

The alternative (a for loop over rows) executes Python bytecode for each individual row. Pandas operations execute C-level code over the entire array at once.

---

## 11. Forecasting and Pricing Logic

### Why Prophet for Forecasting

Prophet was designed specifically for business time-series that exhibit strong multiple seasonalities. Hotel occupancy has exactly this characteristic: strong daily effects (weekends), weekly cycles, and strong yearly seasonal patterns.

Prophet is also robust to missing data. If the daily_metrics table has gaps (dates with no recorded occupancy), Prophet handles them gracefully rather than producing errors or requiring imputation.

Prophet requires no hyperparameter tuning for basic usage. It automatically detects seasonality periods from the data, making it accessible without deep machine learning expertise.

### Seasonality Components

When Prophet fits a model on hotel occupancy data, it decomposes the time series into:

Trend Component: The long-term direction of occupancy. Is the hotel growing, declining, or stable over months?

Weekly Seasonality: The repeating within-week pattern. The model learns that Saturday has higher occupancy than Tuesday, for example.

Yearly Seasonality: The repeating within-year pattern. The model learns that November has higher occupancy than July for Indian hotels.

Custom Weekend Seasonality: The additional weekend effect beyond what the weekly seasonality captures, added as a custom seasonality with period 7.

### Pricing Decision Logic

The pricing engine encodes five pricing principles from revenue management theory:

Principle 1 (Demand Pricing): Price high when demand is high, price low when demand is low. This is the core of yield management.

Principle 2 (Scarcity Premium): When a hotel is already nearly full, the remaining rooms become scarce and can command premium prices.

Principle 3 (Weekend Premium): Consumer behavior consistently shows higher willingness to pay for weekend stays across the hospitality industry.

Principle 4 (Seasonal Premium): High season periods have constrained supply relative to demand, justifying higher prices.

Principle 5 (Lead Time Pricing): Last-minute travelers have less flexibility and will pay premium prices. Advance bookers get slight discounts as an incentive to commit early.

The multiplier is multiplicative (each factor multiplies the running total) rather than additive, which means the effects compound. A high-demand weekend in peak season produces a much higher premium than the sum of individual factors would suggest.

---

## 12. Business Metrics Explained

### ADR (Average Daily Rate)

Formula: Total Revenue / Number of Rooms Occupied

What it measures: The average price charged per occupied room per night. This is the primary measure of pricing effectiveness.

Why total revenue is divided by room nights and not bookings: A 5-night booking at 2,000 per night represents 5 room nights and 10,000 in revenue. Dividing by bookings would give 10,000 for that booking. Dividing by room nights gives 2,000, which accurately represents what was charged per night.

Industry context: A luxury 5-star Mumbai hotel might target an ADR of 8,000-15,000. A budget property might target 1,500-3,000.

### RevPAR (Revenue Per Available Room)

Formula: Total Revenue / Total Available Rooms (or ADR * Occupancy Rate)

What it measures: How efficiently the hotel is using its full room inventory to generate revenue. Unlike ADR (which ignores empty rooms), RevPAR penalizes low occupancy.

Example: Two hotels both have ADR of 5,000. Hotel A has 80% occupancy. Hotel B has 40% occupancy. Hotel A's RevPAR is 4,000. Hotel B's RevPAR is 2,000. Hotel A is twice as efficient at converting its inventory into revenue.

Why it matters: A hotel could boost ADR by raising prices dramatically, but if this results in many empty rooms, RevPAR could fall. RevPAR is the holistic measure of revenue performance.

### Occupancy Rate

Formula: (Rooms Occupied / Total Rooms Available) * 100

What it measures: The percentage of rooms that are generating revenue on any given date.

Calculation note in HotelIQ: A booking that spans multiple nights counts as 1 room occupied on each of those nights. This is calculated by querying for bookings where check_in_date <= target_date AND check_out_date > target_date.

Industry benchmarks: Below 50% is concerning. 60-70% is average. Above 80% is strong. Above 90% is excellent and indicates potential to raise prices.

---

## 13. Frontend Architecture Plan

### Technology Decisions

**Next.js 14** with the App Router is chosen for its server-side rendering capabilities. Analytics dashboards benefit from SSR because data is pre-rendered on the server, resulting in faster initial page loads and better SEO.

**TypeScript** is mandatory for the frontend. Working with complex API response types (booking objects, forecast arrays, metric records) without TypeScript would produce frequent runtime type errors.

**Tailwind CSS** provides utility-first styling that is faster to write than custom CSS for a data-heavy admin interface.

**Recharts** is the visualization library. It is built specifically for React, supports all the chart types needed (line charts for trends, bar charts for comparisons, area charts for occupancy), and is actively maintained.

**shadcn/ui** provides pre-built accessible component primitives (tables, dialogs, cards, forms) that can be customized rather than built from scratch.

### Planned Pages

**Dashboard Page (/)**
The main view. Shows:
- 4 KPI cards: Today's occupancy, Month revenue, ADR, RevPAR
- Revenue trend line chart (last 30 days)
- Occupancy heatmap calendar (current month)
- Recent bookings table
- Quick stats: Active bookings, Pending cancellations

**Analytics Page (/analytics)**
Detailed analytics with date range picker:
- Revenue over time (line chart)
- Occupancy by day of week (bar chart)
- Booking source breakdown (pie chart)
- Weekend vs weekday comparison
- ADR and RevPAR trend lines

**Bookings Page (/bookings)**
Full booking management:
- Filterable, sortable bookings table
- Booking details modal
- Status management (cancel bookings)
- CSV upload interface

**Forecasting Page (/forecast)**
Demand and pricing insights:
- 30-day occupancy forecast chart with confidence bands
- Calendar view with predicted occupancy by date
- Pricing recommendation calculator (select date, enter base price, get recommendation)
- High demand alerts (dates with >80% predicted occupancy)

**Hotels Page (/hotels)**
Property management:
- Hotel list with key metrics
- Add new hotel form
- Room inventory management per hotel

### API Integration Strategy

All API calls will be made using fetch with async/await. A base API client module will handle:
- Base URL configuration from environment variables
- Request and response type definitions in TypeScript
- Error handling and status code interpretation
- Loading state management

React Query (TanStack Query) will be used for server state management, providing automatic caching, background refetching, and optimistic updates.

---

## 14. Deployment Architecture Plan

### Containerization with Docker

**Backend Container:**
The FastAPI application and all Python dependencies will be containerized. The Dockerfile will use a Python 3.10 slim base image, install dependencies from requirements.txt, copy the application code, expose port 8000, and run uvicorn.

**Frontend Container:**
The Next.js application will be containerized separately. The Dockerfile will use a Node.js 18 alpine base, install npm dependencies, build the Next.js application, and serve it on port 3000.

**Docker Compose:**
A docker-compose.yml file will define three services: the FastAPI backend, the Next.js frontend, and the PostgreSQL database. Services will communicate over an internal Docker network. Environment variables will be passed via an .env file. PostgreSQL data will be persisted using a named volume.

### AWS Deployment Plan

**EC2 Instance:**
A single EC2 instance (t3.medium initially) will run both Docker containers via docker-compose. The instance will be in a public subnet of a VPC with a security group allowing inbound traffic on ports 80, 443, 8000, and 3000.

**RDS PostgreSQL:**
An RDS PostgreSQL instance will replace the containerized PostgreSQL. It will be in a private subnet accessible only from the EC2 instance. Daily automated backups will be enabled. The backend container will connect using the RDS endpoint as DATABASE_URL.

**S3 Bucket:**
CSV upload files will be stored in S3 rather than the local filesystem. This ensures uploaded files persist across container restarts and enables future distributed processing.

**Route 53 and Load Balancer:**
A domain name will be managed via Route 53. An Application Load Balancer will distribute traffic and handle SSL termination using an ACM certificate.

### CI/CD Pipeline

GitHub Actions will automate testing and deployment on every push to the main branch:

1. Run pytest suite
2. Build Docker images
3. Push images to Amazon ECR (Elastic Container Registry)
4. SSH into EC2 instance
5. Pull updated images
6. Restart services with zero downtime using docker-compose up -d

### Database Migration Strategy

Alembic will be integrated for database schema versioning. Every schema change will be accompanied by an Alembic migration file. Migrations will run automatically during deployment before the application starts. This ensures the database schema is always synchronized with the application code.

---

## 15. Development Roadmap

### Phase 1: Backend Foundation (Complete)
- Project structure and virtual environment setup
- FastAPI application with CORS middleware
- SQLAlchemy database connection and session management
- ORM model definitions for hotels, rooms, bookings, and daily_metrics
- Pydantic schema definitions
- Database auto-initialization on startup

### Phase 2: Data Layer and CRUD APIs (Complete)
- Synthetic data generator with 3 hotels, 290 rooms, 500+ bookings
- RESTful CRUD endpoints for hotels, rooms, and bookings
- Query parameter filtering for bookings (by hotel, status, date range)
- Pagination support with skip and limit

### Phase 3: ETL Pipeline and Feature Engineering (Complete)
- 9-layer data validation framework with DataQualityReport
- Data cleaning pipeline with standardization and duplicate removal
- Feature engineering module generating 50+ ML features
- ETL pipeline orchestration with Extract, Transform, Load phases
- Batch loading with idempotency and transaction management
- CSV upload endpoint
- Daily metrics calculator for ADR, RevPAR, occupancy
- Pre-aggregation into daily_metrics table
- Analytics service and analytics API endpoints

### Phase 4: AI Layer (Complete)
- Prophet forecasting model with multi-seasonality
- 30-day occupancy prediction with confidence intervals
- Dynamic pricing engine with 5-factor analysis
- Smart query builder with 7 pre-built analytical queries
- Smart queries API and forecasting API endpoints

### Phase 5: Frontend Dashboard (In Progress)
- Next.js project initialization with TypeScript
- Tailwind CSS and shadcn/ui setup
- API client configuration
- Dashboard page with KPI cards and revenue charts
- Analytics page with detailed visualizations
- Bookings management page
- Forecasting and pricing page

### Phase 6: Production Infrastructure (Planned)
- PostgreSQL migration with Alembic migrations
- Docker containerization of backend and frontend
- AWS EC2 deployment with docker-compose
- RDS PostgreSQL database
- S3 integration for file storage
- Domain and SSL configuration

### Phase 7: Quality and Observability (Planned)
- Pytest test suite for all service modules
- Integration tests for API endpoints
- GitHub Actions CI/CD pipeline
- Redis caching layer for frequently accessed metrics
- Application logging with structured JSON logs
- Error monitoring
- API rate limiting

### Phase 8: Advanced Features (Future)
- JWT authentication with role-based access control
- Multi-user support with hotel manager accounts
- Email alerts for anomalies (sudden occupancy drops, unusual cancellation spikes)
- Webhook endpoints for real-time booking system integrations
- XGBoost or neural network pricing model replacing rule-based engine
- Competitor price analysis (web scraping or API integration)
- Customer segmentation (business vs leisure traveler classification)
- Multi-property portfolio optimization
- Mobile-friendly progressive web app

---

## Appendix A: Environment Configuration

### Development Environment Variables

```
DATABASE_URL=sqlite:///./hoteliq.db
API_TITLE=HotelIQ Revenue Management API
API_VERSION=1.0.0
DEBUG=True
```

### Production Environment Variables

```
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/hoteliq
API_TITLE=HotelIQ Revenue Management API
API_VERSION=1.0.0
DEBUG=False
REDIS_URL=redis://elasticache-endpoint:6379
AWS_BUCKET_NAME=hoteliq-uploads
AWS_REGION=ap-south-1
```

---

## Appendix B: CSV Import Format

### Required Columns

```
hotel_id         - Integer, must match existing hotel
room_id          - Integer, must match existing room
check_in_date    - Date string (YYYY-MM-DD)
check_out_date   - Date string (YYYY-MM-DD), must be after check_in_date
guest_name       - String
num_guests       - Integer, greater than 0
booking_price    - Float, greater than 0
base_price       - Float, greater than 0
```

### Optional Columns

```
guest_email      - String (email format), defaults to null
booking_source   - String, defaults to 'direct'
status           - String (confirmed/cancelled/completed), defaults to 'confirmed'
booking_date     - DateTime string, defaults to current timestamp
```

---

## Appendix C: Key Metrics Reference

```
ADR (Average Daily Rate)
Formula: Total Revenue / Rooms Occupied (in room nights)
Unit: Currency (INR)
Good benchmark: Depends on star rating and location

RevPAR (Revenue Per Available Room)
Formula: Total Revenue / Total Available Rooms
Alternative: ADR * Occupancy Rate
Unit: Currency (INR)
Relationship: RevPAR < ADR always (unless 100% occupancy)

Occupancy Rate
Formula: (Rooms Occupied / Total Rooms) * 100
Unit: Percentage
Target range: 65-80% is healthy for most properties

Lead Time
Formula: Check-in Date - Booking Date
Unit: Days
Business meaning: How far in advance guests plan

Length of Stay
Formula: Check-out Date - Check-in Date
Unit: Days (nights)
Business meaning: Guest stay duration
```

---

*This document represents the complete architectural reference for the HotelIQ platform as of current development state. Update this document when new modules are added or architectural decisions change.*

*Author: Karan Katte*
*Project: HotelIQ - AI-Powered Revenue Management Platform*
*Status: Active Development*