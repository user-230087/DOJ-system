import asyncio
import json
import os
import subprocess
import redis
from fastapi import FastAPI
from executors import ExecutorFactory

app = FastAPI(title="Execution Service", version="1.0")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

STREAM_QUEUED = "oj:submissions:queued"
STREAM_VERDICTS = "oj:verdicts:ready"
CONSUMER_GROUP = "execution-workers"
CONSUMER_NAME = "worker-1"

def init_redis_stream():
    try:
        redis_client.xgroup_create(STREAM_QUEUED, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise e

@app.on_event("startup")
async def startup_event():
    # 1. Pre-pull / initialize Docker images on app startup
    print("Initializing Docker runner environments...")
    images = ["python:3.10-slim", "gcc:latest"]
    for img in images:
        try:
            print(f"Checking/Pulling Docker image: {img}...")
            subprocess.run(["docker", "pull", img], check=True, capture_output=True)
            print(f"Image {img} is ready.")
        except Exception as e:
            print(f"Warning: Could not pull image {img}: {e}")

    # 2. Initialize Redis stream consumer group
    init_redis_stream()
    
    # 3. Start background worker loop
    asyncio.create_task(process_submissions_loop())

async def process_submissions_loop():
    while True:
        try:
            entries = redis_client.xreadgroup(
                CONSUMER_GROUP, 
                CONSUMER_NAME, 
                {STREAM_QUEUED: ">"}, 
                count=1, 
                block=2000
            )
            
            if not entries:
                await asyncio.sleep(0.5)
                continue

            for stream_name, message_list in entries:
                for message_id, data in message_list:
                    sub_id = data.get("submissionId")
                    language = data.get("language")
                    source_code = data.get("sourceCode")
                    test_cases_json = data.get("testCases")
                    time_limit_ms = int(data.get("timeLimitMs", 5000))
                    
                    test_cases = json.loads(test_cases_json)
                    print(f"Processing submission {sub_id} [{language}]...")

                    try:
                        executor = ExecutorFactory.get_executor(language)
                        result = executor.execute(source_code, test_cases, time_limit_ms)
                        status = result.get("status", "INTERNAL_ERROR")
                    except Exception as e:
                        print(f"Execution error: {e}")
                        status = "INTERNAL_ERROR"

                    verdict_payload = {
                        "submissionId": sub_id,
                        "status": status
                    }
                    redis_client.xadd(STREAM_VERDICTS, verdict_payload)
                    redis_client.xack(STREAM_QUEUED, CONSUMER_GROUP, message_id)
                    print(f"Completed submission {sub_id} -> Status: {status}")

        except Exception as e:
            print(f"Error in execution worker loop: {e}")
            await asyncio.sleep(1)

@app.get("/health")
def health():
    return {"status": "Execution Service is active with pre-warmed Docker environments"}