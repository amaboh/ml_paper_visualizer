# Developer Documentation: ML Paper Visualizer

## Architecture Overview

ML Paper Visualizer follows a modern web application architecture with clear separation between frontend, backend, and AI processing components. This document provides technical details for developers who want to understand, modify, or extend the application.

## Backend Architecture

### Core Components

The backend is built with FastAPI and organized into the following components:

#### 1. API Endpoints (`app/routers/`)

- `papers.py`: Handles paper upload and URL processing
- `workflow.py`: Manages ML workflow component extraction and relationships
- `visualization.py`: Generates and customizes visualizations

#### 2. Data Models (`app/core/models.py`)

Key models include:
- `Paper`: Represents a research paper with metadata
- `Component`: Represents a component in the ML workflow (data collection, model, etc.)
- `Relationship`: Represents connections between components
- `Visualization`: Stores visualization data and settings

#### 3. Services (`app/services/`)

- `paper_service.py`: Orchestrates the paper processing pipeline
- `paper_parser.py`: Extracts ML workflow components from papers
- `visualization_generator.py`: Creates visualizations from extracted components

#### 4. Utilities (`app/utils/`)

- `pdf_extractor.py`: Extracts text and structure from PDF files
- `ai_processor.py`: Uses AI to analyze paper content and identify ML components

### Data Flow

1. User uploads a paper or provides a URL
2. Paper is saved temporarily and processed by `paper_service.py`
3. `pdf_extractor.py` extracts text and structure
4. `ai_processor.py` analyzes the content to identify ML components
5. `paper_parser.py` creates structured component and relationship objects
6. `visualization_generator.py` creates visualization data
7. Results are returned to the frontend for display

### API Endpoints

#### Paper Processing

- `POST /api/papers/upload`: Upload PDF file or URL
- `GET /api/papers/{paper_id}`: Get paper metadata
- `GET /api/papers/{paper_id}/status`: Check processing status

#### ML Workflow

- `GET /api/workflow/{paper_id}`: Get complete workflow
- `GET /api/workflow/{paper_id}/components`: Get all components
- `GET /api/workflow/{paper_id}/components/{component_id}`: Get specific component
- `GET /api/workflow/{paper_id}/relationships`: Get component relationships

#### Visualization

- `GET /api/visualization/{paper_id}`: Get visualization data
- `POST /api/visualization/{paper_id}/customize`: Customize visualization
- `GET /api/visualization/{paper_id}/export`: Export visualization

## Frontend Architecture

### Page Structure

- `src/app/page.js`: Home page with paper upload interface
- `src/app/results/[id]/page.js`: Results page with visualization

### Components

- `src/components/ui.js`: UI components (Button, Card, Input, etc.)
- `src/components/icons.js`: Icon components

### State Management

The application uses React's built-in state management with hooks for simplicity.

## AI Processing

### Paper Analysis Pipeline

1. **Structure Analysis**: Identify key sections in the paper
2. **Component Extraction**: Extract ML workflow components from relevant sections
3. **Relationship Mapping**: Determine connections between components
4. **Visualization Generation**: Create diagram data from components and relationships

### Prompt Engineering

The AI processor uses carefully designed prompts to extract information from papers:

1. **Section Identification Prompt**: Identifies abstract, methods, experiments, etc.
2. **Component Extraction Prompt**: Extracts specific ML components from each section
3. **Relationship Mapping Prompt**: Determines how components relate to each other

## Extending the Application

### Adding New Component Types

1. Add the new type to `ComponentType` enum in `app/core/models.py`
2. Update the AI processor prompts to recognize the new component type
3. Add styling for the new component type in the visualization generator
4. Update the frontend to display the new component type

### Supporting New Visualization Formats

1. Add a new generator method in `visualization_generator.py`
2. Update the visualization API endpoint to support the new format
3. Implement the renderer in the frontend

### Improving AI Extraction

To improve the extraction quality:
1. Refine the prompts in `ai_processor.py`
2. Add more examples to guide the extraction process
3. Implement feedback mechanisms to learn from corrections

## Testing

### Backend Tests

- `tests/test_api.py`: Tests API endpoints
- `tests/test_paper_parser.py`: Tests paper parsing functionality
- `tests/test_visualization_generator.py`: Tests visualization generation
- `tests/test_paper_service.py`: Tests paper processing service
- `tests/test_integration.py`: Integration tests

### Running Tests

```bash
cd backend
pytest
```

## Deployment

### Backend Deployment

The backend can be deployed as a Docker container or to cloud platforms:

```bash
# Build Docker image
docker build -t ml-paper-visualizer-backend ./backend

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key ml-paper-visualizer-backend
```

### Frontend Deployment

The Next.js frontend can be deployed to Vercel or other platforms:

```bash
# Build for production
cd frontend
npm run build

# Deploy to Vercel
vercel --prod
```

## Performance Considerations

- PDF processing can be memory-intensive for large papers
- AI processing may have rate limits depending on the API used
- Consider implementing caching for frequently accessed papers
- Use background workers for processing to avoid blocking requests

## Security Considerations

- Validate and sanitize all user inputs
- Implement rate limiting for API endpoints
- Use temporary storage for uploaded papers
- Ensure API keys are properly secured
- Consider implementing authentication for production use
