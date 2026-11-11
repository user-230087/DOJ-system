from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class QuestionModel(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    statement = Column(Text)
    difficulty = Column(String, default="EASY")

    test_cases = relationship("TestCaseModel", back_populates="question", cascade="all, delete-orphan")
    submissions = relationship("SubmissionModel", back_populates="question", cascade="all, delete-orphan")

class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    input = Column(Text)
    expected_output = Column(Text)
    hidden = Column(Boolean, default=False)

    question = relationship("QuestionModel", back_populates="test_cases")

class SubmissionModel(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(String)
    language = Column(String)
    source_code = Column(Text)
    status = Column(String, default="PENDING")

    question = relationship("QuestionModel", back_populates="submissions")