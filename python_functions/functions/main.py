from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions.params import StringParam
import ratemyprofessor
import json
from openai import OpenAI
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

# Initialize Firebase Admin
initialize_app()

# Define configuration parameters
OPENAI_API_KEY = StringParam("OPENAI_API_KEY")
ASSISTANT_ID = StringParam("ASSISTANT_ID", default="asst_dXiCpxEc4Nfu2INAoKgDLOgN")

# Cache the UVA school object
UVA_SCHOOL = ratemyprofessor.get_school_by_name("University of Virginia")

def get_professor_rating(professor_name):
    """Get professor rating from RateMyProfessor"""
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

def get_course_prerequisites(course_id):
    """Get course prerequisites"""
    prereqs = {
        "CS2100": ["CS1110", "CS1111", "CS1112", "CS1113"],
        "CS2150": ["CS2100"],
        "CS3140": ["CS2150"]
    }
    return json.dumps(prereqs.get(course_id, []))

def search_courses(instructor="", mnemonic="", number=""):
    """Search for courses based on provided criteria"""
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

            
        return "\n".join(output) if output else "No courses found matching the criteria."
        
    except Exception as e:
        return f"Error searching courses: {str(e)}"

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
        assistant_id = "asst_dXiCpxEc4Nfu2INAoKgDLOgN"
        
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
