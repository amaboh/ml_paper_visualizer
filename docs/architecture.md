# ML Paper Visualizer - Architecture Design

## 1. System Architecture Overview

The ML Paper Visualizer will follow a modern web application architecture with clear separation of concerns between frontend, backend, and AI processing components.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │◄───►│     Backend     │◄───►│   AI Services   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Interface │     │  Data Storage   │     │ External APIs   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 2. Component Architecture

### 2.1 Frontend Architecture

The frontend will be built using Next.js with a component-based architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       Next.js App                           │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │                 │  │                 │  │             │  │
│  │   Page Router   │  │  API Services   │  │    State    │  │
│  │                 │  │                 │  │  Management │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     Components                          ││
│  │                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ││
│  │  │             │  │             │  │                 │  ││
│  │  │    Input    │  │ Visualization│  │ Paper Viewer   │  ││
│  │  │  Components │  │  Components  │  │   Components   │  ││
│  │  │             │  │             │  │                 │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Backend Architecture

The backend will use FastAPI with a service-oriented architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │                 │  │                 │  │             │  │
│  │  API Endpoints  │  │  Middleware     │  │   Models    │  │
│  │                 │  │                 │  │             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                       Services                          ││
│  │                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ││
│  │  │             │  │             │  │                 │  ││
│  │  │    Paper    │  │ ML Workflow │  │  Visualization  │  ││
│  │  │  Processing │  │  Extraction │  │   Generation    │  ││
│  │  │             │  │             │  │                 │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 AI Processing Architecture

The AI processing component will use a multi-step pipeline approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Processing Pipeline                   │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │             │  │             │  │                     │  │
│  │   Paper     │  │  Structure  │  │  Component          │  │
│  │  Parsing    │──►  Analysis   │──►  Identification     │  │
│  │             │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                                      │            │
│         │                                      │            │
│         ▼                                      ▼            │
│  ┌─────────────┐                     ┌─────────────────────┐│
│  │             │                     │                     ││
│  │   Figure    │                     │     Relationship    ││
│  │  Extraction │                     │      Mapping        ││
│  │             │                     │                     ││
│  └─────────────┘                     └─────────────────────┘│
│         │                                      │            │
│         └──────────────────┬───────────────────┘            │
│                            │                                │
│                            ▼                                │
│                    ┌─────────────────┐                      │
│                    │                 │                      │
│                    │  Visualization  │                      │
│                    │   Generation    │                      │
│                    │                 │                      │
│                    └─────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. Data Flow Architecture

The data flow through the system will follow this pattern:

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│           │     │           │     │           │     │           │
│   Paper   │────►│   Text    │────►│ ML Process│────►│ Interactive│
│   Input   │     │ Extraction│     │ Extraction│     │  Diagram  │
│           │     │           │     │           │     │           │
└───────────┘     └───────────┘     └───────────┘     └───────────┘
                        │                 ▲
                        │                 │
                        ▼                 │
                  ┌───────────┐     ┌───────────┐
                  │           │     │           │
                  │  Figure   │────►│ Component │
                  │ Extraction│     │  Mapping  │
                  │           │     │           │
                  └───────────┘     └───────────┘
```

## 4. Technology Stack

### 4.1 Frontend
- **Framework**: Next.js
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context or Redux
- **Visualization**: D3.js or Mermaid.js
- **HTTP Client**: Axios

### 4.2 Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **PDF Processing**: PyMuPDF
- **NLP**: Hugging Face Transformers
- **API Documentation**: Swagger/OpenAPI

### 4.3 AI Services
- **LLM Integration**: OpenAI API (GPT-4 or equivalent)
- **Prompt Engineering**: Custom templates
- **Image Processing**: OpenCV or similar

### 4.4 Infrastructure
- **Deployment**: Docker containers
- **CI/CD**: GitHub Actions
- **Hosting**: Google Cloud Run (frontend), Google Cloud provider (backend)
- **Monitoring**: Prometheus/Grafana

## 5. API Design

### 5.1 Backend API Endpoints

#### Paper Processing
- `POST /api/papers/upload` - Upload PDF file
- `POST /api/papers/url` - Process paper from URL
- `GET /api/papers/{paper_id}` - Get paper metadata
- `GET /api/papers/{paper_id}/text` - Get extracted text
- `GET /api/papers/{paper_id}/figures` - Get extracted figures

#### ML Workflow Extraction
- `POST /api/papers/{paper_id}/extract` - Trigger extraction process
- `GET /api/papers/{paper_id}/workflow` - Get extracted ML workflow
- `GET /api/papers/{paper_id}/components` - Get individual components
- `GET /api/papers/{paper_id}/relationships` - Get component relationships

#### Visualization
- `GET /api/papers/{paper_id}/diagram` - Get visualization data
- `POST /api/papers/{paper_id}/diagram/customize` - Customize visualization
- `GET /api/papers/{paper_id}/diagram/export` - Export visualization

### 5.2 AI Service API

- `POST /ai/analyze/structure` - Analyze paper structure
- `POST /ai/extract/components` - Extract ML components
- `POST /ai/map/relationships` - Map component relationships
- `POST /ai/generate/visualization` - Generate visualization data

## 6. Database Schema

### 6.1 Papers
```
Papers {
  id: UUID [primary key]
  title: String
  authors: String[]
  abstract: String
  url: String
  upload_date: DateTime
  status: Enum [processing, completed, failed]
  created_at: DateTime
  updated_at: DateTime
}
```

### 6.2 Components
```
Components {
  id: UUID [primary key]
  paper_id: UUID [ref: > Papers.id]
  type: Enum [data_collection, preprocessing, model, training, evaluation, results]
  name: String
  description: Text
  details: JSON
  source_section: String
  source_page: Integer
  created_at: DateTime
}
```

### 6.3 Relationships
```
Relationships {
  id: UUID [primary key]
  paper_id: UUID [ref: > Papers.id]
  source_id: UUID [ref: > Components.id]
  target_id: UUID [ref: > Components.id]
  type: String
  description: Text
  created_at: DateTime
}
```

### 6.4 Visualizations
```
Visualizations {
  id: UUID [primary key]
  paper_id: UUID [ref: > Papers.id]
  diagram_data: JSON
  settings: JSON
  created_at: DateTime
  updated_at: DateTime
}
```

## 7. Security Considerations

- HTTPS for all communications
- Rate limiting for API endpoints
- Input validation and sanitization
- Temporary storage of paper content
- No persistent storage of copyrighted content
- User authentication for saved visualizations

## 8. Scalability Considerations

- Stateless backend services for horizontal scaling
- Caching of processed papers
- Background processing for long-running tasks
- Queue system for handling multiple extraction requests
- CDN for static assets and exported visualizations
