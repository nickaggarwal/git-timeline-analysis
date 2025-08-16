#!/usr/bin/env python3
"""
Test OpenAI/Azure OpenAI client directly
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv('../.env')

import openai
from openai import AzureOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_openai_clients():
    """Test both regular OpenAI and Azure OpenAI clients"""
    
    try:
        use_azure = os.getenv('USE_AZURE_OPENAI', 'false').lower() == 'true'
        logger.info(f"🔍 Testing OpenAI clients (use_azure={use_azure})")
        
        if use_azure:
            # Test Azure OpenAI
            logger.info("🤖 Testing Azure OpenAI client...")
            
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            azure_key = os.getenv('AZURE_OPENAI_API_KEY')
            azure_version = os.getenv('AZURE_OPENAI_API_VERSION')
            deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-35-turbo')
            
            logger.info(f"   - Endpoint: {azure_endpoint}")
            logger.info(f"   - API Version: {azure_version}")
            logger.info(f"   - Deployment: {deployment_name}")
            
            if not azure_endpoint or not azure_key:
                logger.error("❌ Azure OpenAI configuration missing")
                return False
            
            # Initialize Azure OpenAI client
            try:
                # Try minimal initialization first
                logger.info("   Trying minimal Azure OpenAI initialization...")
                client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=azure_version
                )
                logger.info("✅ Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Azure OpenAI client: {str(e)}")
                return False
            
            # Test API call
            try:
                test_prompt = """
                Analyze this git commit and provide a concise feature summary:
                
                Commit Message: Add CLI tool for converting ML models to Triton Server format
                Files Changed: main.py, triton_services.py, build_services.py
                Insertions: 150
                Deletions: 5
                Author: Developer
                
                Provide a 1-2 sentence summary of what this commit accomplishes.
                """
                
                logger.info("🧪 Testing Azure OpenAI API call...")
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": "You are a code analysis expert. Analyze git commits and provide concise feature summaries."},
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                logger.info(f"✅ Azure OpenAI response: {result}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Azure OpenAI API call failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
        else:
            # Test regular OpenAI
            logger.info("🤖 Testing regular OpenAI client...")
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if not openai_key:
                logger.error("❌ OpenAI API key not found")
                return False
            
            # Initialize OpenAI client
            try:
                client = openai.OpenAI(api_key=openai_key)
                logger.info("✅ OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
                return False
            
            # Test API call
            try:
                test_prompt = """
                Analyze this git commit and provide a concise feature summary:
                
                Commit Message: Add CLI tool for converting ML models to Triton Server format
                Files Changed: main.py, triton_services.py, build_services.py
                Insertions: 150
                Deletions: 5
                Author: Developer
                
                Provide a 1-2 sentence summary of what this commit accomplishes.
                """
                
                logger.info("🧪 Testing OpenAI API call...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a code analysis expert. Analyze git commits and provide concise feature summaries."},
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                logger.info(f"✅ OpenAI response: {result}")
                return True
                
            except Exception as e:
                logger.error(f"❌ OpenAI API call failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        logger.error(f"❌ OpenAI client test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🕰️ Codebase Time Machine - OpenAI Client Test")
    print("=" * 60)
    success = test_openai_clients()
    sys.exit(0 if success else 1)