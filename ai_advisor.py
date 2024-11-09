import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime

load_dotenv()

client = openai.OpenAI()
model = "gpt-4o-mini"

# ==  Create our Assistant (Uncomment this to create your assistant) ==
ai_advisor = client.beta.assistants.create(
    name="AI Advisor Test",
    instructions="""You are the best personal trainer and nutritionist who knows how to get clients to build lean muscles.\n
     You've trained high-caliber athletes and movie stars. """,
    model=model,
)
asistant_id = ai_advisor.id
print(asistant_id)


# == Thread (uncomment this to create your Thread) ==
thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "How do I get started working out to lose fat and build muscles?",
        }
    ]
)
thread_id = thread.id
print(thread_id)

# === Hardcode our ids ===
asistant_id = ai_advisor.id
thread_id = thread.id

# ==== Create a Message ====
message = "How many reps do I need to do to build lean muscles?"
message = client.beta.threads.messages.create(
    thread_id=thread_id, role="user", content=message
)

# === Run our Assistant ===
run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=asistant_id,
    instructions="Please address the user as James Bond",
)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """

    Waits for a run to complete and prints the elapsed time.:param client: The OpenAI client object.
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in seconds to wait between checks.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                print(f"Assistant Response: {response}")
                break
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)


# === Run ===
wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)

# ==== Steps --- Logs ==
run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run.id)
print(f"Steps---> {run_steps.data[0]}")
