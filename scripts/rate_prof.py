import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
import json
import ratemyprofessor
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

load_dotenv()

client = openai.OpenAI()
model = "gpt-4o-mini"

# Cache the UVA school object to avoid repeated API calls
UVA_SCHOOL = ratemyprofessor.get_school_by_name("University of Virginia")

def get_course_prerequisites(course_id):
    prereqs = {
        "CS2100": ["CS1110", "CS1111", "CS1112", "CS1113"],
        "CS2150": ["CS2100"],
        "CS3140": ["CS2150"]
    }
    return json.dumps(prereqs.get(course_id, []))

def get_professor_rating(professor_name):
    """Get professor rating information from RateMyProfessor"""
    try:
        professor = ratemyprofessor.get_professor_by_school_and_name(UVA_SCHOOL, professor_name)
        
        if professor is None:
            return json.dumps({
                "error": "Professor not found"
            })
        
        return json.dumps({
            "name": professor.name,
            "department": professor.department,
            "rating": professor.rating,
            "difficulty": professor.difficulty,
            "num_ratings": professor.num_ratings,
            "would_take_again": professor.would_take_again,
            "top_tags": professor.get_tags()[:3] if hasattr(professor, 'get_tags') else []
        })
    except Exception as e:
        return json.dumps({
            "error": f"Error retrieving professor information: {str(e)}"
        })
    
def search_courses(instructor="", mnemonic="", number=""):
    """Search for courses based on provided criteria"""
    print("Starting course search...")
    try:
        base_url = "https://louslist.org/pagex.php"
        
        params = {
            "Type": "Search",
            "Semester": "1252",
            "iMnemonic": mnemonic,
            "iNumber": number,
            "iStatus": "",
            "iType": "",
            "iInstructor": instructor,
            "iBuilding": "",
            "iRoom": "",
            "iMode": "",
            "iDays": "",
            "iTime": "",
            "iDates": "",
            "iUnits": "",
            "iTitle": "",
            "iTopic": "",
            "iDescription": "",
            "iDiscipline": "",
            "iMinPosEnroll": "",
            "iMaxPosEnroll": "",
            "iMinCurEnroll": "",
            "iMaxCurEnroll": "",
            "iMinCurWaitlist": "",
            "iMaxCurWaitlist": "",
            "Submit": "Search for Classes"
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        # Construct URL
        url = f"{base_url}?{urlencode(params)}"

        # Fetch and parse data
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        courses_dict = {}
        current_course_number = None

        # Parse the content
        for row in soup.find_all('tr'):
            # Course header row
            course_num_cell = row.find('td', class_='CourseNum')
            if course_num_cell:
                course_number = course_num_cell.text.strip()
                course_name_cell = row.find('td', class_='CourseName')
                course_name = course_name_cell.text.strip() if course_name_cell else None
                
                if course_number not in courses_dict:
                    courses_dict[course_number] = {
                        'course_info': {
                            'number': course_number,
                            'name': course_name,
                        },
                        'sections': []
                    }
                current_course_number = course_number
                continue

            # Section row
            cells = row.find_all('td')
            if len(cells) == 8 and cells[4].find('a') and current_course_number:
                enrollment = cells[4].text.strip().split('/')
                enrollment_current = int(enrollment[0]) if len(enrollment) > 0 else None
                enrollment_max = int(enrollment[1]) if len(enrollment) > 1 else None
                
                instructor_span = cells[5].find('span', onclick=lambda x: x and 'InstructorTip' in x)
                instructor = instructor_span.text.strip() if instructor_span else cells[5].text.strip()
                
                section_data = {
                    'section_number': cells[1].text.strip(),
                    'type': cells[2].text.strip(),
                    'status': cells[3].text.strip(),
                    'enrollment_current': enrollment_current,
                    'enrollment_max': enrollment_max,
                    'instructor': instructor,
                    'schedule': cells[6].text.strip(),
                    'location': cells[7].text.strip()
                }
                courses_dict[current_course_number]['sections'].append(section_data)

        # Convert data to human-readable format
        output = []
        for course in courses_dict.values():
            course_text = f"\nCourse: {course['course_info']['number']} - {course['course_info']['name']}"
            for section in course['sections']:
                section_text = f"\nSection {section['section_number']}:"
                section_text += f"\nInstructor: {section['instructor']}"
                section_text += f"\nEnrollment: {section['enrollment_current']}/{section['enrollment_max']}"
                section_text += f"\nSchedule: {section['schedule']}"
                section_text += f"\nLocation: {section['location']}"
                section_text += f"\nStatus: {section['status']}"
                course_text += section_text
            output.append(course_text)

        print(output)

        return "\n".join(output) if output else "No courses found matching the criteria."
        
    except Exception as e:
        return f"Error searching courses: {str(e)}"

# === Create the Assistant ===
# ai_advisor = client.beta.assistants.create(
#     name="CS Advisor V2",
#     instructions="""You are a Computer Science advisor for students at the University of Virginia. 
#     Use the file search tool for general questions, the prerequisites tool for course requirement questions,
#     the professor rating tool to provide information about professors, and the course search tool to find 
#     current course offerings and their details, including what classes certain proffesors teach.
#     IMPORTANT: Use the file search tool whenever you are asked any question related to the BSCS degree.""",
#     model=model,
#     tools=[
#         {"type": "file_search"},
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_course_prerequisites",
#                 "description": "Get prerequisites for a specific UVA CS course",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "course_id": {
#                             "type": "string",
#                             "description": "The course ID (e.g., CS2150)"
#                         }
#                     },
#                     "required": ["course_id"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_professor_rating",
#                 "description": "Get RateMyProfessor information for a UVA professor",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "professor_name": {
#                             "type": "string",
#                             "description": "The professor's name"
#                         }
#                     },
#                     "required": ["professor_name"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "search_courses",
#                 "description": "Search for UVA courses, professors, and their sections. Be sure to include the 'Type' and 'Enrollment' in your response.",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "instructor": {
#                             "type": "string",
#                             "description": "The instructor's name (optional)"
#                         },
#                         "mnemonic": {
#                             "type": "string",
#                             "description": "The course mnemonic (e.g., CS, APMA) (optional)"
#                         },
#                         "number": {
#                             "type": "string",
#                             "description": "The course number (e.g., 2150) (optional)"
#                         }
#                     }
#                 }
#             }
#         }
#     ],
#     tool_resources={"file_search": {"vector_store_ids": ["vs_RTYajacnG1OYvedUFbSARhup"]}},
# )

assistant_id = "asst_dXiCpxEc4Nfu2INAoKgDLOgN"
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
        
        # Poll for the run's completion or required actions
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            
            if run.status == "requires_action":
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    print(f"Tool call name: {tool_call.function.name}")
                    print(f"Tool call arguments: {tool_call.function.arguments}")
                    if tool_call.function.name == "get_course_prerequisites":
                        args = json.loads(tool_call.function.arguments)
                        result = get_course_prerequisites(args["course_id"])
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result
                        })
                    elif tool_call.function.name == "get_professor_rating":
                        args = json.loads(tool_call.function.arguments)
                        result = get_professor_rating(args["professor_name"])
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result
                        })
                    elif tool_call.function.name == "search_courses":
                        args = json.loads(tool_call.function.arguments)
                        result = search_courses(
                            instructor=args.get("instructor", ""),
                            mnemonic=args.get("mnemonic", ""),
                            number=args.get("number", "")
                        )
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result
                        })
                
                # Submit tool outputs
                if tool_outputs:
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                    print(tool_outputs)
                    continue  # Continue polling for completion
                    
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
    