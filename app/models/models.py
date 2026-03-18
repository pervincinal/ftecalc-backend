from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class PriorityEnum(enum.Enum):
    # New priority values
    BUSINESS_CRITICAL = "BUSINESS CRITICAL"
    MISSION_CRITICAL = "MISSION CRITICAL"
    BUSINESS_OPERATION = "BUSINESS OPERATION"
    # Keep old values for backward compatibility


class StatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"

# Rest of your models remain the same...
class ChapterLead(Base):
    __tablename__ = "chapter_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tribes = relationship("Tribe", back_populates="chapter_lead")

class Tribe(Base):
    __tablename__ = "tribes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    priority = Column(Enum(PriorityEnum), nullable=False)
    chapter_lead_id = Column(Integer, ForeignKey("chapter_leads.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    squads = relationship("Squad", back_populates="tribe")
    chapter_lead = relationship("ChapterLead", back_populates="tribes")

class Squad(Base):
    __tablename__ = "squads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    priority = Column(Enum(PriorityEnum), nullable=False)
    tribe_id = Column(Integer, ForeignKey("tribes.id"), nullable=False)
    platforms = Column(JSON, default=list)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    last_calculation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tribe = relationship("Tribe", back_populates="squads")
    calculations = relationship("Calculation", back_populates="squad", cascade="all, delete-orphan")

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    squad_id = Column(Integer, ForeignKey("squads.id"), nullable=False)
    needed_fte = Column(Float, nullable=False)
    current_fte = Column(Float, nullable=False)
    fte_gap = Column(Float, nullable=False)
    total_weight = Column(Float, nullable=False)
    inputs = Column(JSON, nullable=False)
    effects = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    squad = relationship("Squad", back_populates="calculations")

class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class LevelDefinition(Base):
    __tablename__ = "level_definitions"

    code = Column(String(8), primary_key=True)
    fte_multiplier = Column(Float, nullable=False)
    monthly_cost = Column(Float)
    time_to_fill_weeks = Column(Integer)

class RecommendedMixPolicy(Base):
    __tablename__ = "recommended_mix_policies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class LevelConstraints(Base):
    __tablename__ = "level_constraints"

    id = Column(Integer, primary_key=True, index=True)
    priority_code = Column(String(16), nullable=False)
    min_senior_share = Column(Float)
    max_junior_share = Column(Float)
    min_by_level_json = Column(JSON)
    max_by_level_json = Column(JSON)
    prefer_same_or_up = Column(Boolean, default=True)