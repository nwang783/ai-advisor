import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import json

def parse_enrollment_text(text):
    """Parse enrollment numbers from text like '155 / 250'"""
    try:
        current, maximum = map(int, text.strip().split('/'))
        return {'current': current, 'maximum': maximum}
    except:
        return {'current': None, 'maximum': None}

def parse_section_row(row):
    """Parse a single section row and extract all relevant information"""
    cells = row.find_all('td')
    if not cells or len(cells) < 8:
        return None
    
    # Extract enrollment numbers
    enrollment_cell = cells[4].text.strip()
    enrollment = parse_enrollment_text(enrollment_cell)
    
    # Extract instructor info
    instructor_span = cells[5].find('span', onclick=lambda x: x and 'InstructorTip' in x)
    instructor = instructor_span.text.strip() if instructor_span else cells[5].text.strip()
    
    # Build section data dictionary
    return {
        'section_id': cells[0].text.strip(),
        'section_number': cells[1].text.strip(),
        'type': cells[2].text.strip(),
        'status': cells[3].text.strip(),
        'enrollment_current': enrollment['current'],
        'enrollment_max': enrollment['maximum'],
        'instructor': instructor,
        'schedule': cells[6].text.strip(),
        'location': cells[7].text.strip()
    }

def fetch_and_parse_table(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch the webpage: {e}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    courses_dict = {}  # Dictionary to store courses by course number
    current_course_number = None

    # Loop through each table row
    for row in soup.find_all('tr'):
        # Course header row
        course_num_cell = row.find('td', class_='CourseNum')
        if course_num_cell:
            course_number = course_num_cell.text.strip()
            course_name_cell = row.find('td', class_='CourseName')
            course_name = course_name_cell.text.strip() if course_name_cell else None
            
            # Use course number as key to prevent duplicates
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

        # Section row - if it has 8 cells and one has enrollment data
        cells = row.find_all('td')
        if len(cells) == 8 and cells[4].find('a') and current_course_number: 
            section_data = parse_section_row(row)
            if section_data:
                courses_dict[current_course_number]['sections'].append(section_data)

    # Convert dictionary to list for final output
    return list(courses_dict.values())

def construct_louslist_url(instructor="", iMnemonic="", iNumber=""):
    """Constructs a Lou's List search URL with parameters"""
    base_url = "https://louslist.org/pagex.php"
    
    params = {
        "Type": "Search",
        "Semester": "1252",
        "iMnemonic": iMnemonic,
        "iNumber": iNumber,
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
    
    complete_params = {k: (v if v is not None else "") for k, v in params.items()}
    query_string = urlencode(complete_params)
    return f"{base_url}?{query_string}"

def main():
    # Example usage
    url = construct_louslist_url(iMnemonic="APMA", iNumber="3080")
    data = fetch_and_parse_table(url)
    
    # Print results as formatted JSON
    if isinstance(data, dict) and 'error' in data:
        print(json.dumps({"error": data['error']}, indent=2))
    else:
        print(json.dumps(data, indent=2))
        
        # Also print human-readable format
        print("\nHuman-readable format:")
        for course in data:
            print(f"\nCourse: {course['course_info']['number']} - {course['course_info']['name']}")
            for section in course['sections']:
                print(f"\nSection {section['section_number']}:")
                print(f"Instructor: {section['instructor']}")
                print(f"Enrollment: {section['enrollment_current']}/{section['enrollment_max']}")
                print(f"Schedule: {section['schedule']}")
                print(f"Location: {section['location']}")

if __name__ == "__main__":
    main()
    