#!/usr/bin/env python3
"""
Test the LLMInterface with Azure OpenAI
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv('../.env')

import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMInterface:
    def __init__(self, deployment_name=None, model_name=None):
        """
        Initialize the LLM interface for generating answers using OpenAI APIs
        
        Args:
            deployment_name: Azure OpenAI deployment name (optional)
            model_name: OpenAI model name for direct OpenAI API (optional)
        """
        # Force reload environment variables
        load_dotenv(override=True)
        
        # Determine whether to use Azure OpenAI or direct OpenAI API
        self.use_azure = os.getenv("USE_AZURE_OPENAI", "true").lower() == "true"
        
        if self.use_azure:
            logger.info("Using Azure OpenAI API")
            # Load Azure OpenAI configuration
            self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
            self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", deployment_name)

            logger.info(f"Azure OpenAI API version: {self.azure_api_version}")
            logger.info(f"Azure OpenAI deployment: {self.azure_deployment}")
            
            logger.info(f"Initializing Azure OpenAI with endpoint: {self.azure_endpoint}, " 
                       f"deployment: {self.azure_deployment}, API version: {self.azure_api_version}")
            
            if not self.azure_endpoint or not self.azure_api_key:
                logger.warning("Azure OpenAI credentials not found. LLM operations will fail.")
            
            # Create async OpenAI client configured for Azure
            self.client = openai.AsyncOpenAI(
                api_key=self.azure_api_key,
                base_url=f"{self.azure_endpoint}/openai/deployments/{self.azure_deployment}",
                default_query={"api-version": self.azure_api_version},
            )
            # Store the model/deployment name
            self.model = self.azure_deployment
        else:
            logger.info("Using direct OpenAI API")
            # Load OpenAI configuration
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.openai_model = os.getenv("OPENAI_MODEL", model_name or "gpt-3.5-turbo")
            
            logger.info(f"OpenAI model: {self.openai_model}")
            
            if not self.openai_api_key:
                logger.warning("OpenAI API key not found. LLM operations will fail.")
            
            # Create async OpenAI client
            self.client = openai.AsyncOpenAI(
                api_key=self.openai_api_key,
            )
            # Store the model name
            self.model = self.openai_model

    async def test_simple_query(self, question: str) -> str:
        """Test a simple query with Azure OpenAI"""
        try:
            logger.info(f"Testing simple query: {question}")
            
            messages = [
                {"role": "system", "content": "You are a code analysis expert. Analyze git commits and provide concise feature summaries."},
                {"role": "user", "content": question}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=500  # Increase for reasoning model
            )
            
            answer = response.choices[0].message.content
            logger.info(f"📊 Full response: {response}")
            logger.info(f"✅ Response content: '{answer}'")
            logger.info(f"📈 Usage: {response.usage}")
            
            if not answer or answer.strip() == "":
                logger.warning("Empty response received from Azure OpenAI")
                return "Azure OpenAI returned an empty response"
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error in simple query: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

async def test_llm_interface():
    """Test the LLM interface"""
    try:
        logger.info("🧪 Testing LLMInterface with Azure OpenAI")
        
        # Initialize LLM interface
        llm = LLMInterface()
        
        # Test simple query about triton-co-pilot
        question = """
        Analyze this git commit and provide a concise feature summary:
        
        Commit Message: Add CLI tool for converting ML models to Triton Server format
        Files Changed: main.py, triton_services.py, build_services.py
        Insertions: 150
        Deletions: 5
        Author: Developer
        
        Provide a 1-2 sentence summary of what this commit accomplishes.
        """
        
        answer = await llm.test_simple_query(question)
        
        logger.info("🎉 LLM Interface test completed!")
        return answer
        
    except Exception as e:
        logger.error(f"❌ LLM Interface test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🕰️ Codebase Time Machine - LLM Interface Test")
    print("=" * 60)
    
    # Run async test
    result = asyncio.run(test_llm_interface())
    
    if result:
        print(f"\n✅ Success! LLM Response:")
        print(f"📝 {result}")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)