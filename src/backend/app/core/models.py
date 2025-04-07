from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class PaperStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PaperType(str, Enum):
    NEW_ARCHITECTURE = "new_architecture"
    SURVEY = "survey"
    APPLICATION = "application"
    THEORETICAL = "theoretical"
    UNKNOWN = "unknown"

class ComponentType(str, Enum):
    DATA_COLLECTION = "data_collection"
    PREPROCESSING = "preprocessing"
    DATA_PARTITION = "data_partition"
    MODEL = "model"
    TRAINING = "training"
    EVALUATION = "evaluation"
    RESULTS = "results"
    # Extended component types for more detailed model architecture representation
    LAYER = "layer"
    MODULE = "module"
    HYPERPARAMETER = "hyperparameter"
    ALGORITHM = "algorithm"
    DATASET = "dataset"
    METRIC = "metric"

class LocationInfo(BaseModel):
    page: Optional[int] = None
    paragraph: Optional[int] = None
    position: Optional[int] = None  # Character position in document

class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    title: str
    start_location: LocationInfo
    end_location: LocationInfo
    summary: str
    text: Optional[str] = None  # Full text of the section

class Component(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    type: ComponentType
    name: str
    description: str
    details: Dict[str, Any] = {}
    source_section: Optional[str] = None
    source_page: Optional[int] = None
    location: Optional[LocationInfo] = None
    is_novel: bool = False  # Indicates if this is a novel contribution

class Relationship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    source_id: str
    target_id: str
    type: str
    description: str

class Visualization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paper_id: str
    diagram_type: str
    diagram_data: str
    component_mapping: Dict[str, str] = {}

class Paper(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    url: Optional[str] = None
    status: PaperStatus = PaperStatus.UPLOADED
    uploaded_at: datetime = Field(default_factory=datetime.now)
    paper_type: Optional[PaperType] = None
    sections: Dict[str, Section] = {}
    components: List[Component] = []
    relationships: List[Relationship] = []
    visualization: Optional[Visualization] = None
    details: Dict[str, Any] = {}  # Store additional metadata

class PaperUpload(BaseModel):
    file: Optional[bytes] = None
    url: Optional[str] = None

class PaperResponse(BaseModel):
    id: str
    title: Optional[str] = None
    status: PaperStatus
    message: Optional[str] = None
    paper_type: Optional[PaperType] = None
    sections: Optional[List[str]] = None

class WorkflowResponse(BaseModel):
    paper_id: str
    components: List[Component]
    relationships: List[Relationship]

class VisualizationSettings(BaseModel):
    layout: str = "vertical"
    theme: str = "default"
    detail_level: str = "standard"
    component_filters: List[ComponentType] = []

# In-memory database (for development purposes)
class PaperDatabase:
    papers: Dict[str, Paper] = {}
    
    @classmethod
    def add_paper(cls, paper: Paper):
        cls.papers[paper.id] = paper
        return paper
    
    @classmethod
    def get_paper(cls, paper_id: str) -> Optional[Paper]:
        return cls.papers.get(paper_id)
    
    @classmethod
    def update_paper(cls, paper: Paper):
        cls.papers[paper.id] = paper
        return paper
