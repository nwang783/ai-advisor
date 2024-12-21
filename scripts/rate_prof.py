import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
import json
import ratemyprofessor
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Dict, Union, List
import pandas as pd

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
    
def get_comprehensive_course_info(mnemonic: str, number: str, instructor: str = "") -> Dict:
    """
    Fetches and combines course information from both thecourseforum and louslist.
    
    Args:
        mnemonic (str): Course mnemonic (e.g., 'CS', 'APMA')
        number (str): Course number (e.g., '1110', '3080')
        instructor (str, optional): Instructor name to filter by
        
    Returns:
        Dict containing combined course information from both sources
    """
    
    def scrape_courseforum(mnemonic: str, number: str) -> Dict:
        """Scrapes course information from thecourseforum"""
        url = f"https://thecourseforum.com/course/{mnemonic}/{number}/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            course_info = {}
            
            # Get course title and number
            title_div = soup.select_one("div.d-md-flex.align-items-baseline")
            if title_div:
                course_info['course_code'] = title_div.h1.text.strip()
                course_info['course_name'] = title_div.h2.text.strip()
            
            # Get course description
            desc_card = soup.select_one("div.card div.card-body")
            if desc_card:
                course_info['description'] = desc_card.select_one("p.card-text").text.strip()
                
                # Get prerequisites if they exist
                prereq_div = desc_card.find('div', text=lambda t: t and 'Pre-Requisite(s):' in t)
                if prereq_div:
                    course_info['prerequisites'] = prereq_div.text.replace('Pre-Requisite(s):', '').strip()
            
            # Get instructor information
            instructors = []
            instructor_cards = soup.select("div.rating-card")
            
            for card in instructor_cards:
                instructor = {}
                instructor['name'] = card.select_one("#title").text.strip()
                instructor['rating'] = float(card.select_one("#rating").text.strip())
                instructor['difficulty'] = float(card.select_one("#difficulty").text.strip())
                instructor['gpa'] = float(card.select_one("#gpa").text.strip())
                instructor['sections'] = int(card.select_one("#times").text.strip())
                instructor['last_taught'] = card.select_one("#recency").text.strip()
                instructors.append(instructor)
                
            course_info['instructors'] = instructors
            return course_info
            
        except Exception as e:
            print(f"Error fetching data from thecourseforum: {e}")
            return None

    def scrape_louslist(mnemonic: str, number: str, instructor: str = "") -> Dict:
        """Scrapes course information from louslist"""
        try:
            base_url = "https://louslist.org/pagex.php"
            
            params = {
                "Type": "Search",
                "Semester": "1252",
                "iMnemonic": mnemonic,
                "iNumber": number,
                "iInstructor": instructor,
                "Submit": "Search for Classes"
            }
            
            # Remove empty parameters
            params = {k: v for k, v in params.items() if v}
            url = f"{base_url}?{urlencode(params)}"

            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            courses_dict = {}
            current_course_number = None

            for row in soup.find_all('tr'):
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

            return courses_dict.get(f"{mnemonic} {number}")
            
        except Exception as e:
            print(f"Error fetching data from louslist: {e}")
            return None

    # Get data from both sources
    courseforum_data = scrape_courseforum(mnemonic, number)
    louslist_data = scrape_louslist(mnemonic, number, instructor)

    # Combine the data
    combined_data = {
        'course_code': None,
        'course_name': None,
        'description': None,
        'prerequisites': None,
        'course_ratings': {},
        'current_sections': []
    }

    # Add courseforum data
    if courseforum_data:
        combined_data.update({
            'course_code': courseforum_data.get('course_code'),
            'course_name': courseforum_data.get('course_name'),
            'description': courseforum_data.get('description'),
            'prerequisites': courseforum_data.get('prerequisites'),
            'course_ratings': {
                instructor['name']: {
                    'rating': instructor['rating'],
                    'difficulty': instructor['difficulty'],
                    'gpa': instructor['gpa'],
                    'last_taught': instructor['last_taught']
                }
                for instructor in courseforum_data.get('instructors', [])
            }
        })

    # Add louslist data
    if louslist_data:
        # Update course info if not already present
        if not combined_data['course_code']:
            combined_data['course_code'] = louslist_data['course_info']['number']
        if not combined_data['course_name']:
            combined_data['course_name'] = louslist_data['course_info']['name']
        
        combined_data['current_sections'] = louslist_data.get('sections', [])

    def format_output(data: Dict) -> str:
        """Formats the combined data into a readable string"""
        output = []
        
        # Basic course information
        output.append(f"Course: {data['course_code']} - {data['course_name']}")
        
        if data['description']:
            output.append(f"\nDescription:\n{data['description']}")
        
        if data['prerequisites']:
            output.append(f"\nPrerequisites:\n{data['prerequisites']}")
        
        # Instructor ratings
        if data['course_ratings']:
            output.append("\nInstructor Ratings:")
            for name, ratings in data['course_ratings'].items():
                output.append(f"\n{name}:")
                output.append(f"  Rating: {ratings['rating']}/5.0")
                output.append(f"  Difficulty: {ratings['difficulty']}/5.0")
                output.append(f"  Average GPA: {ratings['gpa']}")
                output.append(f"  Last Taught: {ratings['last_taught']}")
        
        # Current sections
        if data['current_sections']:
            output.append("\nCurrent Sections:")
            for section in data['current_sections']:
                output.append(f"\nSection {section['section_number']}:")
                output.append(f"  Instructor: {section['instructor']}")
                output.append(f"  Enrollment: {section['enrollment_current']}/{section['enrollment_max']}")
                output.append(f"  Schedule: {section['schedule']}")
                output.append(f"  Location: {section['location']}")
                output.append(f"  Status: {section['status']}")
        
        return "\n".join(output)

    # Return both the structured data and formatted output
    return {
        'data': combined_data,
        'formatted_output': format_output(combined_data)
    }

# === Create the Assistant ===
ai_advisor = client.beta.assistants.create(
    name="CS Advisor V3",
    instructions="""You are a Computer Science advisor for students at the University of Virginia. 
    Use the file search tool for general questions, the prerequisites tool for course requirement questions,
    the professor rating tool to provide information about professors, and the course search tool to find 
    current course offerings and their details, including what classes certain proffesors teach.
    IMPORTANT: Use the file search tool whenever you are asked any question related to the BSCS degree. 
    """,
    model=model,
    tools=[
        {"type": "file_search"},
        {
            "type": "function",
            "function": {
                "name": "get_course_prerequisites",
                "description": "Get prerequisites for a specific UVA CS course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {
                            "type": "string",
                            "description": "The course ID (e.g., CS2150)"
                        }
                    },
                    "required": ["course_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_comprehensive_course_info",
                "description": "Fetches detailed course information from both thecourseforum and louslist, including historical ratings, current sections, enrollment data, and more.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mnemonic": {
                            "type": "string",
                            "description": "The course mnemonic (e.g., CS, APMA)"
                        },
                        "number": {
                            "type": "string",
                            "description": "The course number (e.g., 2150, 3080)"
                        },
                        "instructor": {
                            "type": "string",
                            "description": "Optional instructor name to filter results"
                        }
                    },
                    "required": ["mnemonic", "number"]
                }
            }
        },
    ],
    tool_resources={"file_search": {"vector_store_ids": ["vs_RTYajacnG1OYvedUFbSARhup"]}},
)

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
                    elif tool_call.function.name == "get_comprehensive_course_info":
                        args = json.loads(tool_call.function.arguments)
                        result = get_comprehensive_course_info(
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
    