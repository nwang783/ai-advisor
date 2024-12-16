import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging

load_dotenv()

client = openai.OpenAI()
model = "gpt-4o-mini"

# === Create the Assistant ===
# ai_advisor = client.beta.assistants.create(
#     name="CS Advisor",
#     instructions="""You are a CS Advisor for students at the university of Virginia. If you don't know the information provided, use the retrevial tool to better answer the question. IMPORTANT: Only answer advising related questions.
#         """,
#     model=model,
#     tools=[{"type": "file_search"}],
#     tool_resources={"file_search": {"vector_store_ids": ["vs_ziscdQwFY0A5sZIkGR8qu3a2"]}},
# )
assistant_id = "asst_aZZd6r1tlPiBqBZtjoTbQyvR"
print(f"Assistant ID: {assistant_id}")

# === Create the Thread ===
thread = client.beta.threads.create()
thread_id = thread.id
print(f"Thread ID: {thread_id}")

def wait_for_run_completion(client, thread_id, assistant_id, user_message, sleep_interval=5):
    """Handles communication with the assistant and waits for the run to complete."""
    try:
        # Add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_message
        )
        # Create a new run for the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        run_id = run.id
        # Poll for the run's completion
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                # Retrieve the assistant's response
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]  # Get the latest assistant response
                response_text = last_message.content[0].text.value  # Correctly parse the response
                print(f"Assistant Response: {response_text}")  # Display the response
                break
            time.sleep(sleep_interval)
    except Exception as e:
        logging.error(f"Error occurred: {e}")

# === Main Loop ===
while True:
    user_msg = input("Talk to the AI assistant (type 'quit' to exit): ")
    if user_msg.lower() == 'quit':
        break
    wait_for_run_completion(client, thread_id, assistant_id, user_msg)
