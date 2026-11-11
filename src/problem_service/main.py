import asyncio
import json
import os
import redis
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Problem Service", version="1.0")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

STREAM_QUEUED = "oj:submissions:queued"
STREAM_VERDICTS = "oj:verdicts:ready"
CONSUMER_GROUP = "problem-workers"
CONSUMER_NAME = "problem-listener-1"

def init_verdict_stream():
    try:
        redis_client.xgroup_create(STREAM_VERDICTS, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise e

async def process_verdicts_loop():
    init_verdict_stream()
    while True:
        try:
            entries = redis_client.xreadgroup(
                CONSUMER_GROUP, 
                CONSUMER_NAME, 
                {STREAM_VERDICTS: ">"}, 
                count=1, 
                block=2000
            )
            
            if not entries:
                await asyncio.sleep(0.5)
                continue

            for stream_name, message_list in entries:
                for message_id, data in message_list:
                    sub_id = int(data.get("submissionId"))
                    status = data.get("status")

                    print(f"Received verdict for submission {sub_id}: {status}")

                    # Update database row
                    db = next(get_db())
                    try:
                        sub = db.query(models.SubmissionModel).filter(models.SubmissionModel.id == sub_id).first()
                        if sub:
                            sub.status = status
                            db.commit()
                    finally:
                        db.close()

                    # Acknowledge verdict message
                    redis_client.xack(STREAM_VERDICTS, CONSUMER_GROUP, message_id)

        except Exception as e:
            print(f"Error in verdict worker loop: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_verdicts_loop())

# --- Admin CRUD APIs ---
@app.post("/api/admin/questions", response_model=schemas.QuestionResponse)
def create_question(q: schemas.QuestionCreate, db: Session = Depends(get_db)):
    db_question = models.QuestionModel(
        title=q.title,
        statement=q.statement,
        difficulty=q.difficulty
    )
    for tc in q.testCases:
        db_question.test_cases.append(models.TestCaseModel(
            input=tc.input,
            expected_output=tc.expectedOutput,
            hidden=tc.hidden
        ))
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

# --- Solver Read APIs ---
@app.get("/api/questions/{question_id}", response_model=schemas.QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(models.QuestionModel).filter(models.QuestionModel.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    response_data = schemas.QuestionResponse.model_validate(q)
    for tc in response_data.testCases:
        if tc.hidden:
            tc.input = None
            tc.expectedOutput = None
    return response_data

# --- Submission Orchestration API (Async via Redis) ---
@app.post("/api/questions/{question_id}/submissions", response_model=schemas.SubmissionResponse)
def submit_solution(question_id: int, sub: schemas.SubmissionRequest, db: Session = Depends(get_db)):
    q = db.query(models.QuestionModel).filter(models.QuestionModel.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 1. Save submission with PENDING status immediately
    submission = models.SubmissionModel(
        question_id=question_id,
        user_id=sub.userId,
        language=sub.language,
        source_code=sub.sourceCode,
        status="PENDING"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 2. Push event to Redis Stream instead of making a blocking HTTP call
    test_cases_payload = [{"input": tc.input, "expectedOutput": tc.expected_output} for tc in q.test_cases]
    
    event_payload = {
        "submissionId": str(submission.id),
        "language": sub.language,
        "sourceCode": sub.sourceCode,
        "testCases": json.dumps(test_cases_payload)
    }
    
    redis_client.xadd(STREAM_QUEUED, event_payload)

    # 3. Return PENDING response immediately to the client
    return submission

# --- Get Submission Status API ---
@app.get("/api/submissions/{submission_id}", response_model=schemas.SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.SubmissionModel).filter(models.SubmissionModel.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub