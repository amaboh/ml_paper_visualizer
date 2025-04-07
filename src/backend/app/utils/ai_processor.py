import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

logger = logging.getLogger(__name__)

# Singleton instance of the AIProcessor
_instance = None

class AIProcessor:
    """
    Utility class for AI-powered processing of paper content
    Implemented as a singleton to ensure only one client is created
    """
    
    def __new__(cls, api_key: Optional[str] = None):
        """
        Singleton implementation to ensure only one instance exists
        """
        global _instance
        if _instance is None:
            _instance = super().__new__(cls)
            _instance._initialized = False
        return _instance
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI processor
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        # Skip initialization if already done (singleton pattern)
        if getattr(self, '_initialized', False):
            return
            
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. AI processing will not work.")
        else:
            try:
                # Create a custom httpx client with increased timeout
                timeout = httpx.Timeout(120.0, connect=10.0) # Increased overall timeout to 120 seconds
                http_client = httpx.AsyncClient(timeout=timeout)
                
                # Initialize the OpenAI client with explicit settings
                # and our custom http client
                self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openai.com/v1",  # Explicitly set the base URL
                    http_client=http_client,               # Use our custom httpx client
                    max_retries=3                          # Add some resilience
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
                self.client = None
        
        self._initialized = True
    
    # Commenting out orchestration methods - this logic belongs in the service layer.
    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    # async def analyze_paper_structure(self, text: str) -> Dict[str, Any]:
    #     ...
    
    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    # async def extract_ml_components(self, text: str, sections: Dict[str, Any]) -> Dict[str, Any]:
    #     ...

    # --- Generic AI Interaction Methods --- 
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def process_text(self, prompt: str, model: str = "gpt-4-turbo", max_tokens: int = 4000, temperature: float = 0.2, force_json: bool = False) -> str:
        """
        Generic method to send a prompt to the AI and get a text response.
        Handles API calls, retries, and basic error logging.

        Args:
            prompt: The complete prompt string.
            model: The OpenAI model to use.
            max_tokens: Maximum tokens for the response.
            temperature: Sampling temperature.
            force_json: If True, attempt to force JSON output using response_format.

        Returns:
            The text content of the AI's response, or a JSON string with an error key.
        """
        if not self.client:
            logger.error("AI client not initialized.")
            return json.dumps({"error": "AI client not initialized."})

        try:
            logger.debug(f"Sending prompt to {model} (force_json={force_json}, first 100 chars): {prompt[:100]}...")
            
            # Set response format if JSON is forced
            response_format_param = {"type": "json_object"} if force_json else None
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specialized in analyzing documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format_param 
            )
            
            logger.debug(f"Raw OpenAI Response Object: {response.model_dump_json(indent=2)}") # Log the full response object
            
            # Enhanced error handling: ensure we extract content safely or return empty string
            result_text = ""
            if response and hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message and hasattr(choice.message, 'content'):
                    result_text = choice.message.content or ""
            
            logger.debug(f"Received response from {model} (first 100 chars): {repr(result_text[:100])}...")
            return result_text  # Will be empty string if no content was extracted
        
        except Exception as e:
            # Log the specific error BEFORE attempting to format the response
            logger.error(f"Error during OpenAI API call in process_text: {str(e)}", exc_info=True)
            # Ensure a valid JSON error string is returned, even if str(e) fails
            try:
                error_payload = {"error": f"AI API Error: {str(e)}"}
                return json.dumps(error_payload)
            except Exception as format_e:
                logger.error(f"Failed to format error response in process_text: {format_e}")
                return json.dumps({"error": "AI API Error: Failed to format details."})

    # --- process_with_prompt might be redundant if process_text is flexible enough --- 
    # --- Or it could be kept for specific structured output formats --- 
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def process_with_prompt(
        self, 
        prompt: str, 
        content: str, 
        output_format: str = "text", 
        model: str = "gpt-4-turbo",
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> Any:
        """
        Processes text using a specific prompt and expected output format.
        Handles API calls, retries, and JSON parsing.

        Args:
            prompt: The instruction prompt for the AI.
            content: The text content to be processed.
            output_format: Expected format ('text' or 'json').
            model: OpenAI model.
            max_tokens: Max response tokens.
            temperature: Sampling temperature.

        Returns:
            Processed text (str) or parsed JSON (dict/list), or dict with error key on failure.
        """
        if not self.client:
            logger.error("AI client not initialized.")
            return {"error": "AI client not initialized."}

        full_prompt = f"{prompt}\n\nContent:\n{content}"
        
        try:
            logger.debug(f"Sending prompt to {model} for {output_format} (first 100 chars): {full_prompt[:100]}...")
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specialized in analyzing documents."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                # Use response_format if requesting JSON and model supports it
                response_format={"type": "json_object"} if output_format == "json" else None
            )
            
            result_text = response.choices[0].message.content
            logger.debug(f"Received response from {model} (first 100 chars): {result_text[:100]}...")

            if output_format == "json":
                try:
                    # Attempt to parse the entire response as JSON
                    return json.loads(result_text)
                except json.JSONDecodeError:
                    # Try extracting JSON from markdown code blocks as a fallback
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_text, re.MULTILINE)
                    if json_match:
                        try:
                             return json.loads(json_match.group(1))
                        except json.JSONDecodeError as e:
                             logger.error(f"Failed to parse extracted JSON: {e}")
                             return {"error": f"Failed to parse extracted JSON: {e}", "raw_response": result_text}
                    else:
                        logger.error("AI response was not valid JSON and no markdown JSON block found.")
                        return {"error": "AI response was not valid JSON.", "raw_response": result_text}
            else:
                return result_text # Return raw text

        except Exception as e:
            logger.error(f"Error interacting with OpenAI API: {str(e)}", exc_info=True)
            return {"error": f"AI API Error: {str(e)}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_visualization(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate visualization data from extracted components
        
        Args:
            components: List of ML workflow components
            
        Returns:
            Dict[str, Any]: Dictionary containing visualization data
        """
        if not self.api_key or not self.client:
            return {"error": "No API key provided or client not initialized"}
        
        try:
            # Create a mapping of component types to node classes
            type_classes = {
                "data_collection": "dataCollection",
                "preprocessing": "preprocessing",
                "data_partition": "dataPartition",
                "model": "model",
                "training": "training",
                "evaluation": "evaluation",
                "results": "results"
            }
            
            # Generate node IDs (A, B, C, ...)
            component_ids = {}
            for i, component in enumerate(components):
                component_ids[component["id"]] = chr(65 + i)
            
            # Generate a Mermaid flowchart
            component_info = "\n".join([
                f"{component_ids[comp['id']]}[{comp['name']}]" 
                for comp in components
            ])
            
            # Generate relationships
            relationships = []
            for i in range(len(components) - 1):
                source = components[i]
                target = components[i + 1]
                relationships.append(
                    f"{component_ids[source['id']]} --> {component_ids[target['id']]}"
                )
            
            # Special relationship - data partition to evaluation
            data_partition = next((c for c in components if c["type"] == "data_partition"), None)
            evaluation = next((c for c in components if c["type"] == "evaluation"), None)
            
            if data_partition and evaluation:
                relationships.append(
                    f"{component_ids[data_partition['id']]} -.-> {component_ids[evaluation['id']]}"
                )
            
            relationship_info = "\n".join(relationships)
            
            # Generate class definitions for styling
            class_defs = "\n".join([
                f"class {component_ids[comp['id']]} {type_classes.get(comp['type'], 'default')};"
                for comp in components
            ])
            
            # Complete Mermaid diagram
            mermaid_diagram = f"""flowchart TD
{component_info}
{relationship_info}

classDef dataCollection fill:#10B981,stroke:#047857,color:white;
classDef preprocessing fill:#6366F1,stroke:#4338CA,color:white;
classDef dataPartition fill:#F59E0B,stroke:#B45309,color:white;
classDef model fill:#EF4444,stroke:#B91C1C,color:white;
classDef training fill:#8B5CF6,stroke:#6D28D9,color:white;
classDef evaluation fill:#EC4899,stroke:#BE185D,color:white;
classDef results fill:#0EA5E9,stroke:#0369A1,color:white;
classDef default fill:#9CA3AF,stroke:#4B5563,color:white;

{class_defs}
"""
            
            # Create component mapping for the frontend
            component_mapping = {}
            for comp in components:
                component_mapping[component_ids[comp["id"]]] = comp["id"]
            
            return {
                "diagram_type": "mermaid",
                "diagram_data": mermaid_diagram,
                "component_mapping": component_mapping
            }
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            return {"error": str(e)}
    
    async def close(self):
        """
        Close any open resources
        
        This method should be called when the application is shutting down
        to properly close the OpenAI client and release resources.
        """
        if self.client and hasattr(self.client, 'http_client') and self.client.http_client:
            try:
                # Close the underlying httpx client
                await self.client.http_client.aclose()
                logger.info("Closed httpx client successfully")
            except Exception as e:
                logger.error(f"Error closing httpx client: {str(e)}")
        
        self.client = None 