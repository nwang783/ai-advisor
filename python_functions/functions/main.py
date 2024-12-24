from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions.params import StringParam
import json
from openai import OpenAI
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Dict, Union, List


# Initialize Firebase Admin
initialize_app()

# Define configuration parameters
OPENAI_API_KEY = StringParam("OPENAI_API_KEY")
ASSISTANT_ID = StringParam("ASSISTANT_ID", default="asst_ppqkwkdwmE8KZl5aQ6R3jKA2")

def get_course_prerequisites(course_id):
    """Get course prerequisites"""
    prereqs = {
        "CS2100": ["CS1110", "CS1111", "CS1112", "CS1113"],
        "CS2150": ["CS2100"],
        "CS3140": ["CS2150"]
    }
    return json.dumps(prereqs.get(course_id, []))

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
                for param in ['gpa', 'rating', 'difficulty', 'times']:
                    try: # Some instructors may not have a these fields
                        instructor[param] = float(card.select_one(f"#{param}").text.strip())
                    except:
                        instructor[param] = "N/A"
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
            last_section_num = None

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
                    last_section_num = cells[1].text.strip()

                elif len(cells) == 4 and current_course_number:
                    
                    instructor = cells[1].text.strip()
                    
                    section_data = {
                        'section_number': last_section_num,
                        'instructor': instructor,
                        'schedule': cells[2].text.strip(),
                        'location': cells[3].text.strip()
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
                output.append(f"  Instructor: {section.get('instructor', 'N/A')}")
                
                # Handle enrollment info only if both values are present
                if 'enrollment_current' in section and 'enrollment_max' in section:
                    output.append(f"  Enrollment: {section['enrollment_current']}/{section['enrollment_max']}")
                
                output.append(f"  Schedule: {section.get('schedule', 'N/A')}")
                output.append(f"  Location: {section.get('location', 'N/A')}")
                output.append(f"  Status: {section.get('status', 'N/A')}")
        
        return "\n".join(output)

    # Return formatted output
    return format_output(combined_data)

@https_fn.on_request()
def cs_advisor(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function that integrates OpenAI assistant with professor ratings."""
    try:
        # Handle CORS preflight requests
        if req.method == 'OPTIONS':
            return https_fn.Response(
                status=204,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600'
                }
            )

        api_key = OPENAI_API_KEY.value
        assistant_id = "asst_ppqkwkdwmE8KZl5aQ6R3jKA2"
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        request_json = req.get_json()
        if not request_json or 'message' not in request_json:
            return https_fn.Response(
                json.dumps({'error': 'Invalid request'}),
                status=400,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        user_message = request_json['message']
        thread_id = request_json.get('threadId')

        # Create a new thread if none exists
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        
        # Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Poll for completion or required actions
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            
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
                
                if tool_outputs:
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    continue

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                response = messages.data[0].content[0].text.value
                return https_fn.Response(
                    json.dumps({
                        'response': response,
                        'threadId': thread_id
                    }),
                    headers={'Access-Control-Allow-Origin': '*'}
                )

            if run.status == "failed":
                return https_fn.Response(
                    json.dumps({
                        'error': 'Assistant run failed',
                        'threadId': thread_id
                    }),
                    status=500,
                    headers={'Access-Control-Allow-Origin': '*'}
                )

            time.sleep(0.5)

    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': str(e)}),
            status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )

@https_fn.on_request()
def make_new_thread(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function to create a new OpenAI thread."""
    try:
        if req.method == 'OPTIONS':
            return https_fn.Response(
                status=204,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600'
                }
            )

        api_key = OPENAI_API_KEY.value
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Create a new thread
        thread = client.beta.threads.create()
        threadId = thread.id

        return https_fn.Response(
            json.dumps({'threadId': threadId}),
            headers={'Access-Control-Allow-Origin': '*'}
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': str(e)}),
            status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )
    
@https_fn.on_request()
def get_messages_from_thread(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function to get messages from an OpenAI thread."""
    try:
        if req.method == 'OPTIONS':
            return https_fn.Response(
                status=204,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600'
                }
            )

        api_key = OPENAI_API_KEY.value
        thread_id = req.args.get('threadId')

        if not thread_id:
            return https_fn.Response(
                json.dumps({'error': 'Missing threadId'}),
                status=400,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        messages = [
            {
                'role': message.role,
                'content': message.content[0].text.value
            }
            for message in messages.data
        ]

        return https_fn.Response(
            json.dumps({'messages': messages}),
            headers={'Access-Control-Allow-Origin': '*'}
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': str(e)}),
            status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )

    