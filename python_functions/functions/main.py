from firebase_functions import https_fn
from firebase_admin import initialize_app
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Dict, Optional
from datetime import datetime as dt
import re
import pandas as pd

# Initialize Firebase Admin
initialize_app()

# TODO 
# NEED TO DEPLOY THIS FUNCTION TO FIREBASE

class CSP:
    def __init__(self, variables, domains, time_constraints=None):
        """
        Initialize CSP with lab section processing
        """
        self.variables = variables
        self.domains = domains
        self.final_schedule = {}
        self.time_constraints = time_constraints
        
        # Process and separate lab sections
        self.add_classes_with_labs()
        
    def parse_schedule(self, schedule_string):
        """
        Parse a schedule string into a structured format
        
        Robust parsing handles various schedule formats
        """
        # Flexible regex to handle different schedule formats
        schedule_pattern = r'^(\w+)\s+(\d{1,2}:\d{2}(?:am|pm))\s*-\s*(\d{1,2}:\d{2}(?:am|pm))$'
        
        try:
            # Attempt to match the schedule
            match = re.match(schedule_pattern, schedule_string)
            
            if not match:
                raise ValueError(f"Cannot parse schedule format: {schedule_string}")
            
            # Extract components
            days = [match .group(1)[i:i+2] for i in range(0, len(match.group(1)), 2)]
            start_time = self.format_time(match.group(2).strip())
            end_time = self.format_time(match.group(3).strip())
            
            return {
                'days': days,
                'start_time': start_time,
                'end_time': end_time
            }
        
        except Exception as e:
            raise ValueError(f"Detailed parsing error for '{schedule_string}': {str(e)}")
    
    def format_time(self, time_string):
        """
        Convert time string to datetime time object
        
        Handles multiple time input formats
        """
        # Remove any whitespace
        time_string = time_string.replace(' ', '')
        
        try:
            # Primary parsing strategy
            return dt.strptime(time_string, "%I:%M%p").time()
        except ValueError:
            # Fallback parsing strategies
            try:
                # Try without colon
                return dt.strptime(time_string, "%I%M%p").time()
            except ValueError:
                raise ValueError(f"Cannot parse time: {time_string}")
    
    def has_time_conflict(self, schedule1, schedule2):
        """
        Detect time conflicts between two class schedules
        
        Checks for:
        - Day overlap
        - Time overlap
        """
        # Check day overlap
        shared_days = set(schedule1['days']) & set(schedule2['days'])
        
        if shared_days:
            # Check time overlap
            return not (schedule1['end_time'] <= schedule2['start_time'] or 
                        schedule2['end_time'] <= schedule1['start_time'])
        
        return False
    
    def add_classes_with_labs(self):
        """
        Process and separate lab sections from lecture sections
        
        Goals:
        - Identify lab sections
        - Create separate domain entries for labs
        - Modify variables list to include lab courses
        """
        # Create a copy of domains to avoid modifying during iteration
        original_domains = self.domains.copy()
        
        for course, sections in original_domains.items():
            lab_sections = {}  # To hold lab sections
            lecture_sections = {}  # To hold lecture sections

            # Separate lecture and lab sections
            for section, section_data in sections.items():
                # Assume lab sections start with "1"
                if str(section).startswith("1"):
                    lab_sections[section] = section_data
                else:
                    lecture_sections[section] = section_data

            # Update the main domains
            self.domains[course] = lecture_sections

            # Add lab sections as a new course if labs exist
            if lab_sections:
                lab_course_key = f"{course}_lab"
                
                # Add lab course to variables
                if lab_course_key not in self.variables:
                    self.variables.append(lab_course_key)
                
                # Add lab sections to domains
                self.domains[lab_course_key] = lab_sections
    
    def check_for_conflicts(self, new_class, current_schedule):
        """
        Check if a new class conflicts with existing schedule
        
        Handles different possible schedule structures
        """
        # If new class doesn't have a schedule, skip
        if 'schedule' not in new_class or not new_class['schedule']:
            return False
        
        # Parse the new class schedule
        parsed_new_class = self.parse_schedule(new_class['schedule'][0])
        
        # Check against existing schedule
        for course, assigned_class in current_schedule.items():
            # Iterate through sections in the assigned course
            for section, section_data in assigned_class.items():
                # Check if section has a schedule
                if 'schedule' not in section_data or not section_data['schedule']:
                    continue
                
                # Parse the assigned class schedule
                parsed_assigned = self.parse_schedule(section_data['schedule'][0])
                
                # Check for time conflict
                if self.has_time_conflict(parsed_new_class, parsed_assigned):
                    return True
        
        # Check against time constraints if specified
        print(self.time_constraints.keys())
        print(parsed_new_class['days'])
        if set(self.time_constraints.keys()) & set(parsed_new_class['days']):
            for day in parsed_new_class['days']:
                parsed_start = parsed_new_class['start_time']
                parsed_end = parsed_new_class['end_time']
                constaint_start = self.time_constraints[day][0]
                constaint_end = self.time_constraints[day][1]
                
                if (parsed_start < constaint_start or 
                    parsed_end > constaint_end):
                    return True
        
        return False
    
    def backtracking_search(self, schedule=None, optimize_ratings=False):
        """
        Advanced backtracking search with optional rating optimization
        
        Key Optimization Strategy:
        1. If optimize_ratings is True, prioritize sections with higher ratings
        2. Maintain all existing constraint satisfaction rules
        3. Provide a flexible approach to schedule generation
        
        Args:
        - schedule: Current partial schedule
        - optimize_ratings: Flag to enable rating-based section selection
        
        Returns:
        - Optimized schedule or None if no valid schedule found
        """
        if schedule is None:
            schedule = {}
        
        # Check if all variables are assigned
        if len(schedule) == len(self.variables):
            return schedule
        
        # Select an unassigned variable (course)
        var = self.select_unassigned_variable(schedule)
        
        # If optimizing ratings, sort sections by rating in descending order
        sections = self.domains[var].items()
        if optimize_ratings:
            # Filter out sections without ratings, then sort
            rated_sections = [
                (section_code, section_data) 
                for section_code, section_data in sections 
                if section_data.get('rating') is not None
            ]
            
            # Sort by rating in descending order, fallback to original order
            sections = sorted(
                rated_sections, 
                key=lambda x: x[1].get('rating', 0), 
                reverse=True
            )
            
            # Add unrated sections at the end
            unrated_sections = [
                (section_code, section_data) 
                for section_code, section_data in self.domains[var].items() 
                if section_data.get('rating') is None
            ]
            sections.extend(unrated_sections)
        
        # Try each section of the course
        for section_code, section_data in sections:
            # Skip if no schedule or section already in schedule
            if 'schedule' not in section_data or not section_data['schedule']:
                continue
            
            # Check for conflicts
            if self.check_for_conflicts(section_data, schedule):
                continue
            
            # Create a copy of the current schedule to avoid modifying the original
            new_schedule = schedule.copy()
            
            # Assign the section
            new_schedule[var] = {section_code: section_data}
            
            # Recursive search
            result = self.backtracking_search(new_schedule, optimize_ratings)
            
            if result is not None:
                return result
        
        return None
    
    def select_unassigned_variable(self, schedule):
        """
        Select the most constrained unassigned variable
        
        Prioritizes courses with fewer possible sections
        """
        unassigned = [var for var in self.variables if var not in schedule]
        return min(unassigned, key=lambda var: len(self.domains[var]))
    
    def solve(self, optimize_ratings=False):
        """
        Solve the constraint satisfaction problem
        
        Adds optional rating optimization to the search process
        
        Args:
        - optimize_ratings: Flag to enable rating-based section selection
        
        Returns:
        - Optimized final schedule
        """
        self.final_schedule = self.backtracking_search(optimize_ratings=optimize_ratings)
        return self.final_schedule

def get_comprehensive_course_info(mnemonic: str, number: str, instructor: str = "", topic: str = None) -> Dict:
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


    def scrape_louslist(mnemonic: str, number: str, instructor: str = "", topic_name: Optional[str] = None) -> Dict:
        """Scrapes course information from Lou's List, optionally filtering by topic name."""
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
            current_topic = None  # Track the current topic

            for row in soup.find_all('tr'):
                # Check for course number
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

                # Check for topic rows - using the full class structure
                row_classes = row.get('class', [])
                if row_classes and ('SectionTopicOdd' in row_classes or 'SectionTopicEven' in row_classes):
                    # Find the td with colspan="8" which contains the topic
                    topic_cell = row.find('td', attrs={'colspan': '8'})
                    if topic_cell and topic_cell.text.strip():
                        current_topic = topic_cell.text.strip()
                    continue

                # Check for section rows
                cells = row.find_all('td')
                if len(cells) == 8 and cells[4].find('a') and current_course_number:
                    # Only process section if topic matches or no topic filter specified
                    if topic_name is None or (current_topic and topic_name.lower() in current_topic.lower()):
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
                            'location': cells[7].text.strip(),
                            'topic': current_topic
                        }
                        courses_dict[current_course_number]['sections'].append(section_data)
                        last_section_num = cells[1].text.strip()

                elif len(cells) == 4 and current_course_number and last_section_num:
                    # Handle additional rows for sections, only if they belong to a matching topic
                    if topic_name is None or (current_topic and topic_name.lower() in current_topic.lower()):
                        section_data = {
                            'section_number': last_section_num,
                            'instructor': cells[1].text.strip(),
                            'schedule': cells[2].text.strip(),
                            'location': cells[3].text.strip(),
                            'topic': current_topic
                        }
                        courses_dict[current_course_number]['sections'].append(section_data)

            return courses_dict.get(f"{mnemonic} {number}")

        except Exception as e:
            print(f"Error fetching data from Lou's List: {e}")
            return None

    # Get data from both sources
    louslist_data = scrape_louslist(mnemonic, number, instructor, topic_name=topic)
    courseforum_data = scrape_courseforum(mnemonic, number)

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
    if courseforum_data and louslist_data:
        # Get unique instructors from louslist sections
        louslist_instructors = {section['instructor'] for section in louslist_data['sections']}

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
                if instructor['name'] in louslist_instructors
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
                output.append(f"  Topic: {section.get('topic', 'N/A')}")
        
        return "\n".join(output)

    # Return formatted output
    return format_output(combined_data), combined_data

def find_stats_for_section(instructor, course_data):
    """
    Find the rating for a given instructor in the course data
    """
    for course, course_info in course_data.items():
        for instructor_name, info in course_info.get('course_ratings', []).items():
            if instructor_name == instructor:
                info = [info['rating'], info['difficulty'], info['gpa']]
                for i, entry in enumerate(info):
                    if entry == "N/A":
                        info[i] = None
                    else:
                        info[i] = round(float(entry), 2)
                return info 
                
    return None  # Default stats if not founds

def calculate_solution_stats(solution):
    """
    Calculate the average rating, difficulty, and GPA for the solution
    """
    num_ratings = 0
    total_rating = 0
    num_difficulties = 0
    total_difficulty = 0
    num_gpas = 0
    total_gpa = 0
    
    for course, sections in solution.items():
        for section, section_data in sections.items():
            # Check if 'rating' exists and is not None
            if section_data.get('rating') is not None:
                num_ratings += 1
                total_rating += section_data['rating']
            
            # Check if 'difficulty' exists and is not None
            if section_data.get('difficulty') is not None:
                num_difficulties += 1
                total_difficulty += section_data['difficulty']
            
            # Check if 'gpa' exists and is not None
            if section_data.get('gpa') is not None:
                num_gpas += 1
                total_gpa += section_data['gpa']
    
    # Handle cases where there are no ratings, difficulties, or GPAs to avoid ZeroDivisionError
    return {
        'average_rating': round(total_rating / num_ratings, 2) if num_ratings > 0 else 0,
        'average_difficulty': round(total_difficulty / num_difficulties, 2) if num_difficulties > 0 else 0,
        'average_gpa': round(total_gpa / num_gpas, 2) if num_gpas > 0 else 0
    }

@https_fn.on_request()
def csp_build_schedule(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function that using a csp algorithm to build a schedule.
    
    Args: 
    1. input_classes (List[str]): List of classes to build a schedule for. 
        Should be in the format of 'CS 1110', 'APMA 3080', etc. 
    2. time_constraints (Optional[List[str]]): List of time constraints in the format of 'HH:MM AM/PM'.
        """
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

        if not req.get_json():
            raise ValueError("Request body is required")
        
        print(f"Request JSON: {req.get_json()}")
    
        request_json = req.get_json()
        if 'input_classes' not in request_json:
            raise ValueError("Variables and domains are required")
        
        # Get the course info for each input class
        data = {}
        for course in request_json.get('input_classes'):
            mnemonic, number = course.split()
            _, data[course] = get_comprehensive_course_info(mnemonic, number)
        
        # Process the data into variables and domains
        variables = []
        domains = {}

        for course, course_data in data.items():
            variables.append(course)
            # Initialize the domain for the course
            if course not in domains:
                domains[course] = {}
            # Process each section
            for section in course_data['current_sections']:
                schedule = section['schedule']
                section_number = section['section_number']
                # Split the schedule and filter invalid entries
                schedules = schedule.split(",")
                schedules = [s.strip() for s in schedules if not s[0].isdigit()]
                if section_number not in domains[course]:
                    domains[course][section_number] = {}  # Ensure it's a dict, not a list
                # Add schedule and rating
                domains[course][section_number]["schedule"] = schedules
                instructor = section['instructor']
                section_info = find_stats_for_section(instructor, data)
                if section_info:
                    domains[course][section_number]["rating"] = section_info[0]
                    domains[course][section_number]["difficulty"] = section_info[1]
                    domains[course][section_number]["gpa"] = section_info[2]
                    domains[course][section_number]["instructor"] = instructor
                    domains[course][section_number]["location"] = section['location']

        optimize_ratings = request_json.get('optimize_ratings', False)
        time_constraints = request_json.get('time_constraints', None)
        time_constraints_dt = {
            day: tuple(dt.strptime(time, "%I:%M%p").time() 
            for time in times) 
            for day, times in time_constraints.items()
        }
        # Create the CSP instance
        csp = CSP(variables, domains, time_constraints_dt)

        # Solve and get the schedule
        solution = csp.solve()
        print(solution)
        stats = calculate_solution_stats(solution)
        print(f"\nNo optimization stats: {stats}")


        stats = calculate_solution_stats(solution)
        print(f"Solution Stats: {stats}")

        response_data = {
            'schedule': solution,
            'stats': stats
        }
        
        return https_fn.Response(
            json.dumps(response_data),
            headers={'Access-Control-Allow-Origin': '*'}
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': str(e)}),
            status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )
