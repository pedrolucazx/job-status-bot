import os
import time
import google.generativeai as genai

import json
from google.api_core.exceptions import ResourceExhausted
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
        
        prompt = f"""Você lê emails de processos seletivos e extrai o status da candidatura.

Regras pro campo "resultado":
- "rejeitado": a empresa explicitamente diz que não vai seguir com o candidato (ex: "decidimos seguir com outros candidatos", "não avançar neste momento").
- "avancou": a empresa explicitamente convida pra uma próxima etapa concreta (ex: "gostaríamos de agendar uma entrevista", "você foi selecionado para a próxima fase").
- "indefinido": qualquer coisa que não seja um veredito claro — isso INCLUI confirmação de recebimento de candidatura ("recebemos seu currículo", "sua candidatura foi enviada com sucesso", "obrigado por se candidatar"), atualização de status neutra sem decisão, ou qualquer ambiguidade. Na dúvida, use "indefinido", nunca infira "avancou" ou "rejeitado" de uma mensagem genérica de confirmação.

Email:
{email_body}"""
        
        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema
        )

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt, generation_config=generation_config)
                return json.loads(response.text)
            except ResourceExhausted as e:
                wait = getattr(e, 'retry_delay', None)
                wait = wait.seconds if wait else 15
                print(f"Gemini rate limit hit, waiting {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
        raise ResourceExhausted("Gemini rate limit exceeded after 3 retries.")

