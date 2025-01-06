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
from datetime import datetime as dt


# Initialize Firebase Admin
initialize_app()

# Define configuration parameters
OPENAI_API_KEY = StringParam("OPENAI_API_KEY")
ASSISTANT_ID = StringParam("ASSISTANT_ID", default="asst_n4Wj8E7uUACcKvKX4uPGkhgZ")

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

class ScheduleValidator:
    def __init__(self):
        self.day_mapping = {
            "mo": "Monday",
            "tu": "Tuesday",
            "we": "Wednesday",
            "th": "Thursday",
            "fr": "Friday"
        }

    def validate_schedule(self, ai_response):
        try:
            # Handle both string and dict inputs
            if isinstance(ai_response, str):
                response = json.loads(ai_response)
            else:
                response = ai_response

            if not response.get("class_data"):
                return False, ["No class data found in response"]
            
            # If day_of_the_week exists, use it, otherwise use class_data directly
            class_data = (response["class_data"].get("day_of_the_week") or 
                         response["class_data"])
            
            if not class_data:
                return False, ["No schedule data found in response"]

            # Store the class data in the format we need
            response["class_data"] = {"day_of_the_week": class_data}

            validation_messages = []
            schedule_valid = True

            # Check for conflicts
            conflicts = self._check_for_conflicts(response)
            if conflicts:  # If we have any conflicts
                schedule_valid = False
                validation_messages.extend(conflicts)
            else:
                validation_messages.append("No time conflicts detected")

            return schedule_valid, validation_messages

        except json.JSONDecodeError:
            return False, ["Invalid JSON format in response"]
        except Exception as e:
            return False, [f"Error validating schedule: {str(e)}"]

    def _check_for_conflicts(self, response):
        """Check for time conflicts between courses."""
        conflicts = []
        class_data = response["class_data"]["day_of_the_week"]

        for day, courses in class_data.items():
            # Create list of course times for this day
            day_schedule = []
            for course_name, details in courses.items():
                if isinstance(details, dict) and "time" in details:
                    day_schedule.append({
                        "name": course_name,
                        "time": details["time"]
                    })

            # Check each course against every other course for that day
            for i, course1 in enumerate(day_schedule):
                for j, course2 in enumerate(day_schedule[i + 1:], i + 1):
                    if self._has_time_overlap(course1["time"], course2["time"]):
                        conflict_msg = (
                            f"Conflict detected between {course1['name']} and "
                            f"{course2['name']} on {day} at times "
                            f"{course1['time']} and {course2['time']}"
                        )
                        conflicts.append(conflict_msg)

        return conflicts

    def _has_time_overlap(self, time_a, time_b):
        """Check if two time ranges overlap"""
        def parse_time(time_str):
            return dt.strptime(time_str, "%I:%M%p")

        try:
            start_a, end_a = map(
                parse_time,
                time_a.lower().replace(" ", "").split("-")
            )
            start_b, end_b = map(
                parse_time,
                time_b.lower().replace(" ", "").split("-")
            )
            return (start_a < end_b) and (start_b < end_a)
        except ValueError:
            return False

def wait_for_run_completion(thread_id, run_id, client):
    """Wait for assistant run to complete"""
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            
            if run.status == "requires_action":
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    try:
                        args = json.loads(tool_call.function.arguments)
                        if tool_call.function.name == "get_comprehensive_course_info":
                            result = get_comprehensive_course_info(
                                instructor=args.get("instructor", ""),
                                mnemonic=args.get("mnemonic", ""),
                                number=args.get("number", "")
                            )
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": result
                            })
                    except json.JSONDecodeError:
                        print(f"Invalid JSON in tool call arguments: {tool_call.function.arguments}")
                        continue
                
                if tool_outputs:
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    continue

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                if not messages.data:
                    return "No response received"
                return messages.data[0].content[0].text.value
                
            if run.status == "failed":
                return "Assistant run failed"
                
            # Add timeout logic
            time.sleep(1)  # Prevent tight polling loop
            
        except Exception as e:
            return f"Error in wait_for_run_completion: {str(e)}"

@https_fn.on_request()
def cs_advisor(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function that integrates OpenAI assistant with professor ratings."""
    thread_id = None
    
    try:
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

        # Validate required environment variables
        api_key = OPENAI_API_KEY.value
        assistant_id = ASSISTANT_ID.value

        print(f"Assistant ID: {assistant_id}")

        if not api_key or not assistant_id:
            raise ValueError("Missing required environment variables")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        if client:
            print("OpenAI client initialized successfully")

        # Validate request
        if not req.get_json():
            raise ValueError("Request body is required")
            
        request_json = req.get_json()
        if 'message' not in request_json:
            raise ValueError("Message is required")

        user_message = request_json['message']
        thread_id = request_json.get('threadId')

        # Create or retrieve thread
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        
        print(f"Thread ID: {thread_id}")
        
        # Add message and create run
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
        except Exception as e:
            print(f"Error creating assistant run: {str(e)}")
            raise ValueError(f"Error creating assistant run: {str(e)}")

        print(f"Run ID: {run.id}")

        # Get assistant response and handle conflicts
        validator = ScheduleValidator()

        assistant_response = wait_for_run_completion(thread_id, run.id, client)
        print(f"Assistant response: {assistant_response}")
        is_valid, validation_messages = validator.validate_schedule(assistant_response)
        print("Validation Results:")
        for msg in validation_messages:
            print(f"- {msg}")

        max_retries = 3
        retry_count = 0

        while not is_valid and retry_count < max_retries:
            print("\nSchedule validation failed. Attempting to resolve issues.")
            # Combine all validation messages into a clear request
            issues_message = "\n".join(f"- {msg}" for msg in validation_messages)
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"Please resolve these issues in the schedule:\n{issues_message}"
            )
            
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            assistant_response = wait_for_run_completion(thread_id, run.id, client)
            print(f"Assistant response: {assistant_response}")
            is_valid, validation_messages = validator.validate_schedule(assistant_response)
            
            print("\nNew Validation Results:")
            for msg in validation_messages:
                print(f"- {msg}")
            
            retry_count += 1

        if not is_valid:
            print(f"\nFailed to resolve schedule issues after {max_retries} attempts.")
        else:
            print("\nSchedule validation successful!")
            
        # Prepare response
        try:
            response_data = json.loads(assistant_response)
            response_data['threadId'] = thread_id
        except json.JSONDecodeError:
            response_data = {
                'message': assistant_response,
                'threadId': thread_id,
                'class_info': {},
                'notes': 'Response was not in JSON format'
            }
        
        return https_fn.Response(
            json.dumps(response_data),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        )

    except Exception as e:
        error_response = {
            'error': str(e),
            'message': 'An error occurred',
            'class_info': {},
            'notes': '',
            'threadId': thread_id
        }

        print(f"Error: {str(e)}")
        return https_fn.Response(    
            json.dumps(error_response),
            status=500,
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

    