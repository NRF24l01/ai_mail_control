import aiohttp
import asyncio

class AiWorker:
    def __init__(self, db_client, gpt_gateway_url: str, api_key: str):
        self.db_client = db_client
        self.gpt_gateway_url = gpt_gateway_url
        self.api_key = api_key
        self.running = True
    
    async def process_email(self, email: str):
        settings = await self.db_client.get_settings()
        print(settings)
        payload = [
            {
                "content": settings.gpt_prompt.format(types="({})".format(", ".join(settings.types))),
                "role": "system"
            },
            {
                "content": email,
                "role": "user"
            }
        ]
        print(f"Sending payload to {self.gpt_gateway_url} with API key {self.api_key}")
        send_payload = {
            "token": self.api_key,
            "context": payload,
            "model": settings.gpt_model
        }
        print(send_payload)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gpt_gateway_url, json=send_payload) as response:
                    response.raise_for_status()
                    resp_json = await response.json()
        except Exception as e:
            print(f"Error sending payload: {e}")
            return None
        
        if resp_json['result']['choices'][0]['message']['content'] in settings.types:
            print(f"Received valid response: {resp_json}")
            return resp_json['result']['choices'][0]['message']['content']
        return None

    async def process_emails(self):
        print("Processing emails...")
        emails = await self.db_client.get_unprocessed_emails()
        settings = await self.db_client.get_settings()
        print(emails)

        async def handle_email(email):
            text = email.subject + "\n" + email.body
            result = await self.process_email(text)
            if result:
                if settings.answers.get(result, None):
                    pre_generated_answer = settings.answers[result]
                elif result != "Undetectable":
                    pre_generated_answer = f"Не нашли паттерн под {result}"
                else:
                    pre_generated_answer = None
                await self.db_client.mark_email_as_processed(email.uuid, result, pre_generated_answer)

        await asyncio.gather(*(handle_email(email) for email in emails))

    async def start_continuous_processing(self):
        print("Starting continuous email processing (every 60 seconds)...")
        while self.running:
            await self.process_emails()
            print("Email processing cycle completed")
            
            # Wait 60 seconds before next processing cycle
            await asyncio.sleep(60)
    
    def stop_processing(self):
        """Stop the continuous processing loop"""
        self.running = False

    async def run(self):
        from models import run_migrations, init_db
        await init_db()
        await run_migrations()
        print("Database initialized and migrations run")
        
        await self.start_continuous_processing()

if __name__ == "__main__":
    print("Starting AiWorker...")
    from config import GPT_KEY, GPT_GATEWAY_URL
    from manage import db_client
    openai_worker = AiWorker(db_client, GPT_GATEWAY_URL, GPT_KEY)
    asyncio.run(openai_worker.run())