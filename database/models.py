"""SQLAlchemy ORM models for the NetGuard database."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.database import Base


class UploadedFile(Base):
    """Stores metadata about uploaded CSV traffic files."""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, processing, done, error
    row_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    analyses = relationship("AnalysisResult", back_populates="file", cascade="all, delete-orphan")


class AnalysisResult(Base):
    """Stores aggregated results of a traffic analysis run."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    total_records = Column(Integer, default=0)
    normal_count = Column(Integer, default=0)
    attack_count = Column(Integer, default=0)
    best_model = Column(String(100))
    best_accuracy = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)
    chart_distribution = Column(String(512), nullable=True)
    chart_confusion = Column(String(512), nullable=True)
    chart_roc = Column(String(512), nullable=True)
    chart_comparison = Column(String(512), nullable=True)

    file = relationship("UploadedFile", back_populates="analyses")
    ml_metrics = relationship("MLMetric", back_populates="analysis", cascade="all, delete-orphan")
    attack_stats = relationship("AttackStatistic", back_populates="analysis", cascade="all, delete-orphan")


class MLMetric(Base):
    """Stores per-model ML performance metrics for an analysis."""
    __tablename__ = "ml_metrics"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    training_time = Column(Float, default=0.0)
    is_best = Column(Integer, default=0)

    analysis = relationship("AnalysisResult", back_populates="ml_metrics")


class AttackStatistic(Base):
    """Stores per-attack-type statistics for an analysis."""
    __tablename__ = "attack_statistics"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    attack_type = Column(String(100), nullable=False)
    count = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)

    analysis = relationship("AnalysisResult", back_populates="attack_stats")
