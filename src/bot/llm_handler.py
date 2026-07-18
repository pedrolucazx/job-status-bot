import os
import time
import google.generativeai as genai

import json
from google.api_core.exceptions import ResourceExhausted
from google.generativeai.types import GenerationConfig

DEFAULT_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'specs', '001-job-status-bot', 'contracts', 'gemini-schema.json'
)

MAX_BODY_CHARS = 1500

RULES = """Regras pro campo "resultado":
- "rejeitado": a empresa explicitamente diz que não vai seguir com o candidato (ex: "decidimos seguir com outros candidatos", "não avançar neste momento").
- "avancou": a empresa explicitamente convida pra uma próxima etapa concreta (ex: "gostaríamos de agendar uma entrevista", "você foi selecionado para a próxima fase").
- "indefinido": qualquer coisa que não seja um veredito claro — isso INCLUI confirmação de recebimento de candidatura ("recebemos seu currículo", "sua candidatura foi enviada com sucesso", "obrigado por se candidatar"), atualização de status neutra sem decisão, ou qualquer ambiguidade. Na dúvida, use "indefinido", nunca infira "avancou" ou "rejeitado" de uma mensagem genérica de confirmação."""


class LLMHandler:
    def __init__(self, schema_path=DEFAULT_SCHEMA_PATH):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY environment variable.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.schema_path = schema_path

    def extract_info(self, email_body, schema_path=None):
        with open(schema_path or self.schema_path, 'r') as f:
            schema = json.load(f)

        prompt = f"""Você lê emails de processos seletivos e extrai o status da candidatura, em qualquer idioma.

{RULES}

Email:
{email_body}"""

        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema
        )

        return self._generate_with_retry(prompt, generation_config)

    def classify_batch(self, emails):
        """emails: list of {'id', 'sender', 'subject', 'body'}.
        Returns a dict keyed by email id. Language-agnostic — no keyword
        list to maintain, the model judges relevance per email itself."""
        with open(self.schema_path, 'r') as f:
            item_schema = json.load(f)

        batch_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Copied exactly from the input email's id."},
                    **item_schema["properties"],
                },
                "required": ["id"] + item_schema["required"],
            },
        }

        items_text = "\n\n".join(
            f"--- EMAIL id={e['id']} ---\n"
            f"De: {e['sender']}\n"
            f"Assunto: {e['subject']}\n"
            f"Corpo:\n{e['body'][:MAX_BODY_CHARS]}"
            for e in emails
        )

        prompt = f"""Você recebe uma lista de emails da caixa de entrada de alguém em busca de emprego, em qualquer idioma. Pra CADA email, decida se é relacionado a um processo seletivo (job_related) e, se for, extraia o status.

Emails que NÃO são sobre processo seletivo (newsletter, pessoal, alerta genérico de novas vagas sem candidatura associada, etc.) devem ter job_related=false, com empresa/cargo/resultado vazios ou "indefinido".

{RULES}

Retorne um item no array de saída pra CADA email da lista abaixo, usando o mesmo "id".

{items_text}"""

        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=batch_schema
        )

        results = self._generate_with_retry(prompt, generation_config)
        return {r['id']: r for r in results}

    def _generate_with_retry(self, prompt, generation_config):
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
