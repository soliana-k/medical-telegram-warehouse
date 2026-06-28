
# Shipping a Data Product: From Raw Telegram Data to an Analytical API

An end-to-end ELT data pipeline for processing public Telegram channels that sell medical and pharmaceutical products in Ethiopia. This repository implements automated data collection, localized raw data lake storage, structural PostgreSQL transformation formatting, and a multidimensional star schema using **dbt** as a trusted data transformation factory.

---

##  Project Directory Structure

This project enforces the following target architecture layout:

```text
medical-telegram-warehouse/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env                          
├── .gitignore                   
├── requirements.txt              
├── README.md                     
├── data/                         
│   └── raw/
│       ├── telegram_messages/    
│       └── images/               
├── logs/                         
├── src/
│   ├── db_loader.py
│   └── scraper.py   
           
├── medical_warehouse/            
│   ├── dbt_project.yml           
│   ├── profiles.yml              
│   ├── models/
│   │   ├── staging/
│   │   │   ├── src_telegram.yml  
│   │   │   └── stg_telegram_messages.sql
│   │   └── marts/
│   │       ├── dim_channels.sql  
│   │       ├── dim_dates.sql     
│   │       ├── fct_messages.sql 
│   │       └── schema.yml        
│   └── tests/
│       ├── assert_no_future_messages.sql 
│       └── assert_positive_views.sql     
└── scripts/

```

---

##  Step-by-Step Task Implementations

### Task 1 - Data Scraping and Collection (Extract & Load)

* **API Access:** Managed via custom `Telethon` clients utilizing `api_id` and `api_hash` tokens mapped directly out of secure root `.env` variables.
* **Scraped Target Channels:** Custom tracking focused cleanly across designated medical channels:
* `CheMed Telegram Channel` (`CheMed1`)
* `Lobelia Cosmetics` (`LobeliaCosmetics`)
* `Tikvah Pharma` (`tikvahpharma`)


* **Data Lake Partitioning Strategy:** Data is written preserving original structural JSON keys across organized chronological partitions: `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`.
* **Media Assets Isolation:** Image content downloads automatically to standard paths matching the grain framework constraint: `data/raw/images/{channel_name}/{message_id}.jpg`.
* **Logging System:** Operates inside `logs/scraper.log`, actively tracking API runtime errors, rate thresholds, and message crawl checkpoints.

### Task 2-  Data Modeling and Transformation (Transform)

The transformation layout uses **dbt** to reshape messy JSON payloads into an analytics-optimized **Star Schema** data model within PostgreSQL.

#### 1. Data Landing Phase (`db_loader.py`)

Extracts raw data from partitioned directories, flattens relational object nodes, resets existing target rows via quick truncation steps, and runs fast batch bulk-insert workloads into `raw.telegram_messages`.

#### 2. Staging Layer (`stg_telegram_messages.sql`)

Cleans raw text layers by:

* Slicing and casting plain timestamp rows to true SQL `timestamp` and `date` formats.
* Filtering out silent control logs or completely empty text notification streams.
* Constructing explicit computed analytical features: `message_length` and `has_image_flag`.

#### 3. Dimension Tables (Marts)

* **`dim_channels`:** Employs deterministic `MD5` hashing to generate standard string `channel_key` surrogate values. Classifies channels using name matching paths into explicit categorical domains (`Pharmaceutical`, `Cosmetics`, `Medical`), and tracks historical performance parameters like `total_posts` and `avg_views`.
* **`dim_dates`:** Builds a continuous conformed operational timeline ranging from 2015 to 2030, pre-calculating temporal properties (`day_of_week`, `is_weekend`, `month_name`) to eliminate slow runtime database execution overhead.

#### 4. Fact Table (`fct_messages`)

The core fact layer defines its grain explicitly at the **individual post broadcast level**. It houses relational foreign key bridges mapped cleanly back to relevant dimensions alongside transactional numeric counters (`view_count`, `forward_count`, `message_length`).

---

##  Operational Quality and Validation Tests

Data integrity checkpoints are actively tested through automated constraint schemas (`medical_warehouse/models/marts/schema.yml` and `tests/`).

### Test Assertions Overview

1. **Generic Constraints:** Ensures `message_id`, `channel_key`, and `date_key` are entirely `unique` and `not_null`. Enforces strict referential target structural checking rules (`relationships`) over relational boundaries.
2. **`assert_no_future_messages`:** Custom rule identifying data integrity anomalies by flagging records with a date greater than the system evaluation runtime context clock.
3. **`assert_positive_views`:** Custom rule flagging downstream reporting risks if message tracking metric counts map below `0`.

### Running Verification Protocols

Run these command sequences from the `medical_warehouse` project directory to execute validation rules:

```bash
# Materialize views and structural data model tables inside PostgreSQL
dbt run

# Run generic constraints and business rule tests
dbt test

```

### Reference Validation Metrics Log Output

```text
Finished running 12 data tests in 0 hours 0 minutes and 5.25 seconds (5.25s).

Completed successfully

Done. PASS=12 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=12

```

---

##  Accessing Interactive Catalog Documentation

To review structural property files, variable metadata, database constraints, and visual pipeline dependency mapping trees, run these self-generation commands from the `medical_warehouse` root path:

```bash
dbt docs generate
dbt docs serve

```

*This instantly spins up a local web catalog server accessible inside your web browser at `http://localhost:8080`.*


