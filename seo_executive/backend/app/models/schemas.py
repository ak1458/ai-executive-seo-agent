from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Website schemas
class WebsiteBase(BaseModel):
    url: str
    gsc_property: Optional[str] = None

class WebsiteCreate(WebsiteBase):
    pass

class WebsiteResponse(WebsiteBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Keyword schemas
class KeywordBase(BaseModel):
    keyword: str
    volume: Optional[int] = None
    difficulty: Optional[float] = None
    current_rank: Optional[int] = None

class KeywordCreate(KeywordBase):
    website_id: int

class KeywordResponse(KeywordBase):
    id: int
    website_id: int
    last_checked: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Audit schemas
class AuditBase(BaseModel):
    audit_type: str
    status: str = "pending"

class AuditCreate(AuditBase):
    website_id: int

class AuditResponse(AuditBase):
    id: int
    website_id: int
    results_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# GSC Data schemas
class GSCDataBase(BaseModel):
    url: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: Optional[float] = None
    date: datetime

class GSCDataCreate(GSCDataBase):
    website_id: int

class GSCDataResponse(GSCDataBase):
    id: int
    website_id: int
    
    class Config:
        from_attributes = True

# Task schemas
class TaskRequest(BaseModel):
    task_type: str
    params: Dict[str, Any]

class TaskResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Keyword Research schemas
class KeywordResearchRequest(BaseModel):
    seed: str
    location: Optional[str] = "us"
    language: Optional[str] = "en"
    depth: Optional[int] = 2

class KeywordResearchResult(BaseModel):
    keyword: str
    volume: int
    difficulty: float
    cpc: Optional[float] = None
    competition: Optional[str] = None
    parent_topic: Optional[str] = None

# Indexing schemas
class IndexingSubmitRequest(BaseModel):
    urls: List[str]

class IndexingStatusResponse(BaseModel):
    url: str
    status: str
    last_update: Optional[datetime] = None
