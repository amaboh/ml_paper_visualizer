# ML Paper Visualizer

A tool for visualizing ML model development processes from research papers, inspired by GitDiagram.

## Overview

ML Paper Visualizer is an application that enables researchers and ML enthusiasts to easily understand the model development process in research papers. It automatically extracts and visualizes the complete ML workflow from data collection through preprocessing, modeling, to results evaluation.

## Features

- **Paper Input**: Upload PDF files or provide URLs to research papers
- **ML Workflow Extraction**: Automatically identify data collection methods, preprocessing steps, model architecture, training methodology, and evaluation metrics
- **Interactive Visualization**: View the complete ML process as an interactive diagram with clickable components
- **Component Details**: Access detailed information about each component of the ML workflow
- **Paper Reference**: Link visualization components back to relevant sections in the original paper
- **Customization Options**: Adjust visualization layout, theme, and detail level

## Project Structure

```
ml_paper_visualizer/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── core/          # Core models and utilities
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic services
│   │   └── utils/         # Utility functions
│   └── tests/             # Backend tests
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/           # Frontend utilities
├── docs/                  # Documentation
│   ├── architecture.md    # System architecture
│   ├── features.md        # Feature specifications
│   ├── requirements.md    # Project requirements
│   └── ui_design.md       # UI/UX design
├── research/              # Research findings
└── tests/                 # Integration tests and sample papers
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or pnpm

### Backend Setup

1. Navigate to the backend directory:

   ```
   cd ml_paper_visualizer/backend
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```
   # Create a .env file with the following variables
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run the backend server:
   ```
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```
   cd ml_paper_visualizer/frontend
   ```

2. Install dependencies:

   ```
   npm install
   # or
   pnpm install
   ```

3. Run the development server:

   ```
   npm run dev
   # or
   pnpm dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Running with Docker (Recommended)

This is the recommended way to run the application as it handles dependencies and setup within isolated containers.

### Prerequisites

- Docker ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose ([Usually included with Docker Desktop](https://docs.docker.com/compose/install/))

### Setup

1.  **Environment Variables:** Create a `.env` file in the project root directory (the same directory as `docker-compose.yml`). Add your OpenAI API key to this file:

    ```
    OPENAI_API_KEY=your_actual_openai_api_key
    ```

    _Important:_ Ensure `.env` is listed in your root `.gitignore` file to prevent committing secrets.

2.  **Frontend API URL:** The frontend service in `docker-compose.yml` is configured to connect to the backend at `http://backend:8000`. Ensure your frontend code uses `process.env.NEXT_PUBLIC_API_URL` to make API calls.

### Build and Run

1.  Navigate to the project root directory in your terminal.
2.  Run the following command to build the images and start the containers:

    ```bash
    docker compose up --build
    ```

    To run the containers in the background (detached mode), use:

    ```bash
    docker compose up --build -d
    ```

3.  **Accessing the Application:**
    - Frontend: Open [http://localhost:3000](http://localhost:3000) in your browser.
    - Backend API Docs: Open [http://localhost:8000/docs](http://localhost:8000/docs).

### Stopping the Application

To stop the containers, run the following command in the project root directory:

```bash
docker compose down
```

## Usage

1. **Upload a Paper**: On the home page, either upload a PDF file or enter a URL to a research paper.

2. **View Visualization**: After processing, the application will display an interactive visualization of the ML workflow.

3. **Explore Components**: Click on components in the visualization to view detailed information about each part of the ML process.

4. **Customize View**: Use the customization panel to adjust the visualization layout, theme, and detail level.

5. **Export Results**: Export the visualization as an image or interactive HTML file for sharing or inclusion in presentations.

## Testing

### Backend Tests

Run the backend tests with pytest:

```
cd ml_paper_visualizer/backend
pytest
```

### Frontend Tests

Run the frontend tests with Jest:

```
cd ml_paper_visualizer/frontend
npm test
```

## Technologies Used

- **Backend**: FastAPI, PyMuPDF, OpenAI API, Hugging Face Transformers
- **Frontend**: Next.js, TypeScript, Tailwind CSS, D3.js/Mermaid.js
- **Testing**: Pytest, Jest

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started, report bugs, and suggest enhancements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by [GitDiagram](https://github.com/ahmedkhaleel2004/gitdiagram)
- Uses research papers from [arXiv](https://arxiv.org/)

image.png