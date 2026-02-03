import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except:
                pass

    def is_active(self):
        return self.client is not None

    def generate_response(self, prompt, system_role="Você é um assistente de carreira útil."):
        if not self.is_active():
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return None
