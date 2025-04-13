from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter()

# Placeholder data for example papers
# In a real application, this might come from a database or config file
# We'll use Mermaid syntax for the diagram definition

EXAMPLE_PAPERS_DATA = {
    "cnn-image-classification": {
        "id": "cnn-image-classification",
        "title": "CNN for Image Classification",
        "description": "Deep Residual Learning for Image Recognition (ResNet)",
        "mermaid_graph": """
graph LR
    A[ImageNet Dataset] --> B(Preprocessing);
    B --> C{Train/Val Split};
    C --> D[ResNet-50 Model];
    D --> E(Training Loop);
    E --> F[SGD Optimizer];
    F --> E;
    D --> G{Evaluation};
    G --> H[Top-1 Accuracy];
    G --> I[Top-5 Accuracy];
    A --> J(Data Augmentation);
    J --> B;
"""
    },
    "transformer-architecture": {
        "id": "transformer-architecture",
        "title": "Transformer Architecture",
        "description": "Attention Is All You Need",
        "mermaid_graph": """
graph TD
    A[Input Embedding] --> B(Positional Encoding);
    B --> C{Multi-Head Attention};
    C --> D(Add & Norm);
    D --> E{Feed Forward};
    E --> F(Add & Norm);
    F --> C; subgraph Encoder Layer
    direction TB
    C
    D
    E
    F
    end
    F --> G[Encoder Output];


    H[Output Embedding] --> I(Positional Encoding);
    I --> J{Masked Multi-Head Attention};
    J --> K(Add & Norm);
    K --> L{Multi-Head Attention};
    L --> M(Add & Norm);
    M --> N{Feed Forward};
    N --> O(Add & Norm);
    O --> J; subgraph Decoder Layer
    direction TB
    J
    K
    L
    M
    N
    O
    end

    G --> L;
    O --> P[Linear Layer];
    P --> Q[Softmax];
    Q --> R(Output Probabilities);
"""
    }
}

class ExamplePaperInfo(BaseModel):
    id: str
    title: str
    description: str

class ExamplePaperDetail(ExamplePaperInfo):
    mermaid_graph: str


@router.get("/examples", response_model=List[ExamplePaperInfo], tags=["Examples"])
async def list_example_papers():
    """
    Retrieve a list of available example papers.
    """
    # Explicitly select only the fields needed for ExamplePaperInfo
    return [
        ExamplePaperInfo(
            id=data["id"],
            title=data["title"],
            description=data["description"]
        ) 
        for data in EXAMPLE_PAPERS_DATA.values()
    ]

@router.get("/examples/{example_id}", response_model=ExamplePaperDetail, tags=["Examples"])
async def get_example_paper_detail(example_id: str):
    """
    Retrieve the details and visualization data for a specific example paper.
    """
    if example_id not in EXAMPLE_PAPERS_DATA:
        raise HTTPException(status_code=404, detail="Example paper not found")
    return ExamplePaperDetail(**EXAMPLE_PAPERS_DATA[example_id]) 