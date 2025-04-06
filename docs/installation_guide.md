# Installation Guide: ML Paper Visualizer

This guide provides detailed instructions for installing and setting up the ML Paper Visualizer application on different platforms.

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor, 2.0 GHz or higher
- **RAM**: 4 GB (8 GB recommended for processing large papers)
- **Disk Space**: 1 GB free space
- **Operating System**: 
  - Windows 10/11
  - macOS 10.15 (Catalina) or newer
  - Ubuntu 20.04 or newer, or other Linux distributions

### Software Prerequisites
- **Python**: Version 3.10 or higher
- **Node.js**: Version 18 or higher
- **npm** or **pnpm**: Latest stable version
- **Git**: For cloning the repository

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ml-paper-visualizer.git
cd ml-paper-visualizer
```

### 2. Backend Setup

#### Create and Activate Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key
```

Replace `your_openai_api_key` with your actual OpenAI API key. You can obtain an API key from [OpenAI's website](https://platform.openai.com/).

### 3. Frontend Setup

#### Install Dependencies

**Using npm:**
```bash
cd ../frontend
npm install
```

**Using pnpm:**
```bash
cd ../frontend
pnpm install
```

#### Configure Frontend Environment (Optional)

Create a `.env.local` file in the `frontend` directory if you need to customize the API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Running the Application

#### Start the Backend Server

From the `backend` directory with the virtual environment activated:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start the Frontend Development Server

From the `frontend` directory:

**Using npm:**
```bash
npm run dev
```

**Using pnpm:**
```bash
pnpm dev
```

#### Access the Application

Open your web browser and navigate to:
```
http://localhost:3000
```

## Docker Installation (Alternative)

If you prefer using Docker, follow these steps:

### Prerequisites
- Docker and Docker Compose installed

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ml-paper-visualizer.git
cd ml-paper-visualizer
```

2. Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key
```

3. Build and start the containers:
```bash
docker-compose up -d
```

4. Access the application at:
```
http://localhost:3000
```

## Troubleshooting

### Common Issues

#### Backend Dependencies Installation Fails
- Ensure you have the required system libraries:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install -y python3-dev build-essential
  
  # macOS
  brew install python
  ```

#### OpenAI API Key Issues
- Verify your API key is correct and has sufficient credits
- Check that the `.env` file is in the correct location
- Restart the backend server after updating the API key

#### Port Conflicts
If port 8000 or 3000 is already in use:
- For backend: Change the port in the uvicorn command
- For frontend: Change the port in the package.json scripts or use the `-p` flag

#### PDF Processing Issues
- Ensure you have the required libraries for PDF processing:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y poppler-utils
  
  # macOS
  brew install poppler
  ```

### Getting Help

If you encounter issues not covered here:
1. Check the logs for error messages
2. Consult the [developer documentation](./developer_guide.md)
3. Open an issue on the GitHub repository

## Updating the Application

To update to the latest version:

1. Pull the latest changes:
```bash
git pull origin main
```

2. Update backend dependencies:
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Update frontend dependencies:
```bash
cd ../frontend
npm install  # or pnpm install
```

4. Restart both servers
