import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
import json
import ratemyprofessor
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Dict, Union, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv(find_dotenv())

# Initialize OpenAI client
client = openai.OpenAI()
model = "gpt-4o"

# Cache the UVA school object
UVA_SCHOOL = ratemyprofessor.get_school_by_name("University of Virginia")

def get_course_prerequisites(course_id: str) -> str:
    """Get prerequisites for a specific course."""
    prereqs = {
        "CS2100": ["CS1110", "CS1111", "CS1112", "CS1113"],
        "CS2150": ["CS2100"],
        "CS3140": ["CS2150"]
    }
    return json.dumps(prereqs.get(course_id, []))

def get_professor_rating(professor_name: str) -> str:
    """Get professor rating information from RateMyProfessor."""
    try:
        professor = ratemyprofessor.get_professor_by_school_and_name(UVA_SCHOOL, professor_name)
        
        if professor is None:
            return json.dumps({
                "error": "Professor not found",
                "professor_name": professor_name
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
        logging.error(f"Error retrieving professor information: {e}")
        return json.dumps({
            "error": f"Error retrieving professor information: {str(e)}",
            "professor_name": professor_name
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

    # Return both the structured data and formatted output
    return {
        'data': combined_data,
        'formatted_output': format_output(combined_data)
    }


def handle_tool_call(tool_call) -> Optional[Dict]:
    """Handle individual tool calls and return the appropriate response."""
    try:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        if function_name == "get_course_prerequisites":
            result = get_course_prerequisites(arguments["course_id"])
        elif function_name == "get_professor_rating":
            result = get_professor_rating(arguments["professor_name"])
        elif function_name == "get_comprehensive_course_info":
            result = get_comprehensive_course_info(
                mnemonic=arguments.get("mnemonic", ""),
                number=arguments.get("number", ""),
                instructor=arguments.get("instructor", "")
            )
        else:
            logging.warning(f"Unknown function call: {function_name}")
            return None
            
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(result) if not isinstance(result, str) else result
        }
    except Exception as e:
        logging.error(f"Error in tool call handling: {e}")
        return None

def wait_for_run_completion(client, thread_id: str, assistant_id: str, user_message: str, sleep_interval: int = 5):
    """Handle communication with the assistant and wait for run completion."""
    try:
        # Add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Create and start the run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run.status == "requires_action":
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    output = handle_tool_call(tool_call)
                    if output:
                        tool_outputs.append(output)
                
                if tool_outputs:
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    continue
                    
            elif run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                if messages.data:
                    response = messages.data[0].content[0].text.value
                    print("\nAssistant:", response)
                break
            elif run.status == "failed":
                logging.error(f"Run failed: {run.last_error}")
                print("\nAssistant: I encountered an error. Please try again.")
                break
            elif run.status == "expired":
                logging.error("Run expired")
                print("\nAssistant: The request timed out. Please try again.")
                break
                
            time.sleep(sleep_interval)
            
    except Exception as e:
        logging.error(f"Error in run completion: {e}")
        print("\nAssistant: I encountered an error. Please try again.")

def main():
    """Main function to run the AI advisor system."""
    try:
        # Initialize assistant
        assistant = client.beta.assistants.create(
            name="CS Advisor V3",
            instructions="""You are a Computer Science advisor for students at the University of Virginia. 
            Use the available tools to provide accurate and helpful information about courses, 
            prerequisites, professors, and degree requirements. Be breif but informative. When recommended a schedule, make sure there are no conflicts""",
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
                        "description": "Fetches detailed course information including ratings, sections, and enrollment data. Use this tool when asked about the 'best' professor or for finding the 'best' class.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "mnemonic": {
                                    "type": "string",
                                    "description": "The course mnemonic (e.g., CS, APMA)"
                                },
                                "number": {
                                    "type": "string",
                                    "description": "The course number (e.g., 2150)"
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
            tool_resources={"file_search": {"vector_store_ids": ["vs_RTYajacnG1OYvedUFbSARhup"]}}
        )
        print(f"Assistant created: {assistant.id}")

        # Create thread
        thread = client.beta.threads.create()
        
        print("UVA CS AI Advisor initialized. Type 'quit' to exit.")
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'quit':
                break
            if user_input:
                wait_for_run_completion(client, thread.id, assistant.id, user_input)
                
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        print("An error occurred. Please restart the application.")

if __name__ == "__main__":
    main()
    