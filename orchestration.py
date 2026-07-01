import os
import subprocess
from dagster import asset, Definitions, ScheduleDefinition, DefaultScheduleStatus, AssetSelection

# Helper function to find python executable across venv layouts
def get_python_bin():
    if os.name == 'nt':  # Windows environment
        return os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    # else:
    #     return os.path.join(os.getcwd(), "venv", "bin", "python")

@asset(description="Scrapes raw medical channels metadata directly out of Telegram channels via Telethon.")
def scrape_telegram_data():
    python_bin = get_python_bin()
    scraper_script = os.path.join("src", "scrapper.py")
    
    result = subprocess.run([python_bin, scraper_script], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Telegram Scraper process failed:\n{result.stderr}")
    return "raw_scraped_json_files"

@asset(
    deps=[scrape_telegram_data],
    description="Parses scraped JSON storage files and loads row records into raw Postgres database tables."
)
def load_raw_to_postgres():
    python_bin = get_python_bin()
    db_load_script = os.path.join("src", "db_loader.py")
    
    result = subprocess.run([python_bin, db_load_script], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Raw Postgres database loader failed:\n{result.stderr}")
    return "raw_database_tables_populated"

@asset(
    deps=[load_raw_to_postgres],
    description="Invokes dbt model generation paths to rebuild conformed dimensional tables inside the analytics schema."
)
def run_dbt_transformations():
    dbt_dir = "medical_warehouse"
    subprocess.run(["dbt", "clean"], cwd=dbt_dir, check=True)
    
    result = subprocess.run(["dbt", "run"], cwd=dbt_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"dbt transformation build compilation layer failed:\n{result.stderr}")
    return "analytics_marts_compiled"

@asset(
    deps=[run_dbt_transformations],
    description="Triggers the YOLOv8 object detection inference engine to classify gathered diagnostic media imagery."
)
def run_yolo_enrichment():
    python_bin = get_python_bin()
    yolo_script = os.path.join("src", "yolo_detect.py")
    
    result = subprocess.run([python_bin, yolo_script], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"YOLO object detection script task failed:\n{result.stderr}")
    return "image_metadata_enriched"

# FIX: Target all assets cleanly using AssetSelection.all()
daily_pipeline_schedule = ScheduleDefinition(
    name="daily_medical_warehouse_pipeline",
    cron_schedule="0 0 * * *",  
    target=AssetSelection.all(), 
    default_status=DefaultScheduleStatus.STOPPED
)


defs = Definitions(
    assets=[scrape_telegram_data, load_raw_to_postgres, run_dbt_transformations, run_yolo_enrichment],
    schedules=[daily_pipeline_schedule]
)