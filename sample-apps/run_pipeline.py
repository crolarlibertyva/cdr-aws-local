"""
Orchestrates Glue jobs then queries results via Trino (local Athena).

This script submits jobs via AWS CLI to a local Glue service (moto).
"""

import subprocess
import time
import json
import os
import pandas as pd

from query_utils import run_trino_query

# AWS CLI configuration (assumes moto endpoint)
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://moto:5000")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = "glue-job-scripts"
JOBS_DIR = os.path.abspath("./glue-jobs")

def ensure_s3_bucket():
    """Ensure the S3 bucket exists for job scripts."""
    result = subprocess.run([
        "aws", "s3api", "create-bucket",
        "--bucket", S3_BUCKET,
        "--endpoint-url", AWS_ENDPOINT_URL,
        "--region", AWS_REGION
    ], capture_output=True)
    # Ignore errors if bucket already exists
    return True

def upload_job_script(job_file: str) -> str:
    """Upload job script to moto S3 and return the S3 location."""
    local_path = os.path.join(JOBS_DIR, job_file)
    s3_path = f"s3://{S3_BUCKET}/{job_file}"
    
    print(f"  Uploading {job_file} to {s3_path}...")
    result = subprocess.run([
        "aws", "s3", "cp", local_path, s3_path,
        "--endpoint-url", AWS_ENDPOINT_URL,
        "--region", AWS_REGION
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to upload {job_file}: {result.stderr}")
    
    return s3_path

def run_glue_job(job_file: str):
    print(f"\n{'='*60}\nRunning: {job_file}\n{'='*60}")
    
    # Upload script to S3
    s3_location = upload_job_script(job_file)
    
    # Create or update the Glue job
    job_name = job_file.replace(".py", "").replace("/", "-")
    print(f"  Creating Glue job: {job_name}...")
    
    role_arn = "arn:aws:iam::123456789012:role/GlueJobRole"  # Mock ARN for moto
    
    create_job_cmd = [
        "aws", "glue", "create-job",
        "--name", job_name,
        "--role", role_arn,
        "--command", json.dumps({
            "Name": "glueetl",
            "ScriptLocation": s3_location,
            "PythonVersion": "3"
        }),
        "--endpoint-url", AWS_ENDPOINT_URL,
        "--region", AWS_REGION
    ]
    
    subprocess.run(create_job_cmd, capture_output=True)
    
    # Start the job run
    print(f"  Starting job run for {job_name}...")
    start_cmd = [
        "aws", "glue", "start-job-run",
        "--job-name", job_name,
        "--endpoint-url", AWS_ENDPOINT_URL,
        "--region", AWS_REGION
    ]
    
    result = subprocess.run(start_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{job_file} submission failed: {result.stderr}")
    
    # Parse the job run ID from response
    try:
        response = json.loads(result.stdout)
        job_run_id = response.get("JobRunId", "unknown")
        print(f"✅ {job_file} submitted (JobRunId: {job_run_id})")
    except json.JSONDecodeError:
        print(f"✅ {job_file} submitted")

def query(sql: str, label: str):
    print(f"\n── {label} ──")
    cols, rows = run_trino_query(sql)
    df = pd.DataFrame(rows, columns=cols)
    print(df.to_string(index=False))
    return df

if __name__ == "__main__":
    # ── Run Glue jobs ─────────────────────────────────────────────────────────────
    print(f"\nUsing AWS endpoint: {AWS_ENDPOINT_URL}")
    ensure_s3_bucket()
    
    run_glue_job("01_ingest_to_catalog.py")
    run_glue_job("02_join_and_write.py")

    # Give Trino a moment to reflect catalog changes
    time.sleep(3)

    # ── Query via Athena (Trino) ──────────────────────────────────────────────────
    query(
        "SELECT * FROM glue.sales_db.customer_orders ORDER BY order_date",
        "All orders with customer details"
    )

    query(
        """
        SELECT customer_name, country,
               COUNT(*)    AS orders,
               SUM(amount) AS total_spent
        FROM glue.sales_db.customer_orders
        GROUP BY customer_name, country
        ORDER BY total_spent DESC
        """,
        "Spend by customer"
    )

    query(
        """
        SELECT country, SUM(amount) AS revenue
        FROM glue.sales_db.customer_orders
        GROUP BY country
        ORDER BY revenue DESC
        """,
        "Revenue by country"
    )
