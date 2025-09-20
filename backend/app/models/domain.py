from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Domain settings
    is_available = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    max_file_size = Column(BigInteger, default=10485760)  # 10MB default
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploads = relationship("Upload", back_populates="domain")
    user_domains = relationship("UserDomain", back_populates="domain", cascade="all, delete-orphan")


class UserDomain(Base):
    __tablename__ = "user_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    
    # Domain claim settings
    is_primary = Column(Boolean, default=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_domains")
    domain = relationship("Domain", back_populates="user_domains")
    
    # Ensure one user can only claim a domain once
    __table_args__ = (UniqueConstraint('user_id', 'domain_id', name='unique_user_domain'),)


class UploadAnalytic(Base):
    __tablename__ = "upload_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False, index=True)
    
    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    
    # Timestamp
    accessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    upload = relationship("Upload", back_populates="analytics")