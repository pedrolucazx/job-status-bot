import os
import google.generativeai as genai

import json
from google.generativeai.types import GenerationConfig

DEFAULT_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'specs', '001-job-status-bot', 'contracts', 'gemini-schema.json'
)

class LLMHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY environment variable.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def extract_info(self, email_body, schema_path=DEFAULT_SCHEMA_PATH):
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        prompt = f"Extract the required information from the following email body:\n\n{email_body}"
        
        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema
        )

        response = self.model.generate_content(prompt, generation_config=generation_config)
        
        return json.loads(response.text)

