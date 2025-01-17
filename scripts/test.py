import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Dict, Union, List, Optional
from datetime import datetime as dt

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
    return format_output(combined_data)

# Example usage
# Get all sections with topic "Art and Politics of Dreaming"
info = get_comprehensive_course_info("EGMT", "1520", topic="Birds Aren't Real")
print(info)

# Get all sections (no topic filter)
# info = get_comprehensive_course_info("EGMT", "1520")