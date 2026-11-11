from pydantic import BaseModel, Field
from typing import List, Optional

class TestCaseCreate(BaseModel):
    input: str
    expectedOutput: str
    hidden: bool = False

class TestCaseResponse(BaseModel):
    id: int
    input: Optional[str] = None
    expectedOutput: Optional[str] = Field(default=None, validation_alias="expected_output", serialization_alias="expectedOutput")
    hidden: bool

    class Config:
        from_attributes = True
        populate_by_name = True

class QuestionCreate(BaseModel):
    title: str
    statement: str
    difficulty: str = "EASY"
    testCases: List[TestCaseCreate]

class QuestionResponse(BaseModel):
    id: int
    title: str
    statement: str
    difficulty: str
    testCases: List[TestCaseResponse] = Field(validation_alias="test_cases", serialization_alias="testCases")

    class Config:
        from_attributes = True
        populate_by_name = True

class SubmissionRequest(BaseModel):
    userId: str
    language: str
    sourceCode: str

class SubmissionResponse(BaseModel):
    id: int
    questionId: int = Field(validation_alias="question_id", serialization_alias="questionId")
    userId: str = Field(validation_alias="user_id", serialization_alias="userId")
    language: str
    status: str

    class Config:
        from_attributes = True
        populate_by_name = True