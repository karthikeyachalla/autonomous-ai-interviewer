from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime


Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    applications = relationship("Application", back_populates="candidate", lazy="joined")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_role = Column(String, nullable=False)
    resume_text = Column(String, nullable=True)
    jd_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    results = relationship("RoundResult", back_populates="application", lazy="joined")
    candidate = relationship("Candidate", back_populates="applications", lazy="joined")


class RoundResult(Base):
    __tablename__ = "round_results"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    round_name = Column(String, nullable=False)
    score = Column(Integer, nullable=True)
    passed = Column(Integer, nullable=True)
    artifacts = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    application = relationship("Application", back_populates="results", lazy="joined")
