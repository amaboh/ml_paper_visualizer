# User Guide: ML Paper Visualizer

## Introduction

ML Paper Visualizer is a tool designed to help researchers and ML enthusiasts easily understand the model development process in research papers. This guide will walk you through how to use the application to visualize ML workflows from academic papers.

## Getting Started

### Accessing the Application

You can access ML Paper Visualizer through your web browser at the application URL. The home page presents you with options to upload a paper or provide a URL.

### Uploading a Paper

There are two ways to input a research paper:

1. **File Upload**:
   - Click on the "Upload PDF" tab
   - Drag and drop a PDF file into the upload area, or click to browse your files
   - Select a PDF file (maximum size: 10MB)
   - Click "Visualize Paper" to begin processing

2. **URL Input**:
   - Click on the "Enter URL" tab
   - Paste a URL to a PDF file (e.g., from arXiv, academic repositories, or direct PDF links)
   - Click "Visualize Paper" to begin processing

### Example Papers

For your convenience, the application provides example papers that you can use to test the visualization capabilities:

- **CNN for Image Classification**: "Deep Residual Learning for Image Recognition" (ResNet paper)
- **Transformer Architecture**: "Attention Is All You Need" (Transformer paper)

Simply click on one of these examples to automatically fill in the URL field, then click "Visualize Paper".

## Understanding the Visualization

After processing a paper, you'll be taken to the results page with the ML workflow visualization.

### Visualization Components

The visualization represents the ML workflow as a flowchart with different components:

- **Data Collection** (Green): Information about datasets used
- **Preprocessing** (Indigo): Data cleaning and transformation steps
- **Data Partitioning** (Amber): Train/test/validation split methods
- **Model Architecture** (Red): Neural network or other model structure
- **Training Process** (Purple): Optimization methods and training procedures
- **Evaluation** (Pink): Metrics and evaluation methodology
- **Results** (Blue): Performance outcomes and findings

### Interacting with the Visualization

- **Click on components** to view detailed information in the sidebar
- **Hover over connections** to see the relationship between components
- **Zoom and pan** to navigate larger visualizations
- **Use the sidebar tabs** to switch between component details and paper content

### Customization Options

You can customize the visualization using the "Customize" button in the top right:

- **Layout**: Choose between vertical flow, horizontal flow, or radial layout
- **Component Display**: Show/hide specific component types
- **Detail Level**: Adjust the amount of information displayed
- **Color Theme**: Select from default, scientific, high contrast, or custom themes

### Exporting Results

To save or share your visualization:

1. Click the "Export" button in the top right
2. Choose your preferred format:
   - PNG: Static image
   - SVG: Vector graphic
   - HTML: Interactive visualization that can be opened in a browser

## Troubleshooting

### Common Issues

- **Paper Not Processing**: Some papers may have complex formatting that makes extraction difficult. Try papers with clearer structure.
- **Missing Components**: If certain components are not detected, the paper may not explicitly describe those aspects of the ML workflow.
- **Slow Processing**: Large or complex papers may take longer to process. Please be patient.

### Getting Help

If you encounter issues:

1. Check that your PDF is properly formatted and not password-protected
2. Try one of the example papers to verify the system is working correctly
3. Contact support with details about the specific paper and issue

## Best Practices

For optimal results:

- Use papers with clear methodology sections
- Prefer papers from established conferences and journals
- Recent papers (last 5 years) tend to have more structured methodology descriptions
- Papers with diagrams of model architecture often yield better visualizations

## Privacy and Data Handling

- Uploaded papers are processed temporarily and not permanently stored
- Paper content is used solely for visualization purposes
- No personal data is collected during the visualization process

## Feedback

We're constantly improving ML Paper Visualizer. If you have suggestions or feedback, please use the feedback button in the application footer.
