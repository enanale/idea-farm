import os
import sys
import logging
from services.ai_service import get_ai_service

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Run local prompt tuning.
    Usage: python tune.py [input_file]
    If no input file provided, uses a default sample text.
    """
    
    # Check for ADC
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json")):
        print("⚠️  WARNING: Application Default Credentials not found.")
        print("Run: gcloud auth application-default login")
        # Proceeding anyway, might fail or use other methods
        
    print("🚀 Initializing AI Service...")
    ai = get_ai_service()
    
    # 1. Read Prompt Template
    prompt_path = "prompt.md"
    if not os.path.exists(prompt_path):
        print(f"❌ Error: {prompt_path} not found.")
        return

    with open(prompt_path, "r") as f:
        prompt_template = f.read()
        
    print(f"📄 Loaded prompt template from {prompt_path} ({len(prompt_template)} chars)")

    # 2. Read Input Content
    content = "Idea Farm is a personal knowledge capture tool that uses AI to summarize content."
    input_file = sys.argv[1] if len(sys.argv) > 1 else "sample.txt"
    
    if os.path.exists(input_file):
        with open(input_file, "r") as f:
            content = f.read()
            print(f"📖 Loaded input from {input_file} ({len(content)} chars)")
    else:
        print(f"ℹ️  Using default sample text (pass a filename to use your own)")

    # 3. Generate
    print("\n⏳ Generating summary...")
    try:
        result = ai.summarize(content, prompt_template=prompt_template)
        
        print("\n" + "="*80)
        print("RESULT")
        print("="*80)
        import json
        print(json.dumps(result, indent=2))
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")

if __name__ == "__main__":
    main()
