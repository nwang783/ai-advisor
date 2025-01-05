from pydantic import BaseModel
import json
from datetime import datetime as dt

class ScheduleValidator:
    def __init__(self):
        self.day_mapping = {
            "mo": "Monday",
            "tu": "Tuesday",
            "we": "Wednesday",
            "th": "Thursday",
            "fr": "Friday"
        }

    def validate_schedule(self, ai_response, input_classes):
        """
        Comprehensive schedule validation that checks for:
        1. Presence of all required courses
        2. Time conflicts between courses
        3. Data format and completeness
        
        Parameters:
        ai_response (str or dict): The AI response containing schedule data
        input_classes (list): List of required course names
        
        Returns:
        tuple: (bool, list) indicating success/failure and a list of validation messages
        """
        try:
            # Handle both string and dict inputs
            if isinstance(ai_response, str):
                response = json.loads(ai_response)
            else:
                response = ai_response

            # Get the class data, handling both structures
            if not response.get("class_data"):
                return False, ["No class data found in response"]
            
            # If day_of_the_week exists, use it, otherwise use class_data directly
            class_data = (response["class_data"].get("day_of_the_week") or 
                         response["class_data"])
            
            if not class_data:
                return False, ["No schedule data found in response"]

            # Store the class data in the format we need
            response["class_data"]["day_of_the_week"] = class_data

            validation_messages = []
            schedule_valid = True

            # Check for all courses
            courses_check = self._check_for_all_courses(response, input_classes)
            if not courses_check[0]:
                schedule_valid = False
                validation_messages.append(courses_check[1])
            else:
                validation_messages.append("All required courses are present")

            # Check for conflicts
            conflicts_check = self._check_for_conflicts(response)
            if conflicts_check[0]:  # True means conflict was found
                schedule_valid = False
                validation_messages.append(conflicts_check[1])
            else:
                validation_messages.append("No time conflicts detected")

            return schedule_valid, validation_messages

        except json.JSONDecodeError:
            return False, ["Invalid JSON format in response"]
        except Exception as e:
            return False, [f"Error validating schedule: {str(e)}"]

    def _check_for_all_courses(self, response, input_classes):
        """Check if all required courses are present in the schedule"""
        class_data = response["class_data"]
        found_courses = set()
        for day_data in class_data.values():
            found_courses.update(day_data.keys())

        required_courses = set(input_classes)
        missing_courses = required_courses - found_courses

        if not missing_courses:
            return True, "All required courses are present"
        else:
            return False, f"Missing courses: {', '.join(missing_courses)}"

    def _check_for_conflicts(self, response):
        """Check for time conflicts between courses."""
        class_data = response["class_data"]

        for day, courses in class_data.items():  # Iterate over each day
            times = []
            for course_name, details in courses.items():  # Iterate over courses for the day
                if isinstance(details, dict) and "time" in details:  # Ensure details is a dictionary and has a 'time' field
                    times.append({
                        "name": course_name,
                        "time": details["time"]
                    })
                elif course_name == "Monday":
                    break

            # Check for conflicts within the collected times
            for i, course_a in enumerate(times):
                for j, course_b in enumerate(times):
                    if i >= j:  # Skip self-comparison and redundant checks
                        continue
                    if self._has_time_overlap(course_a["time"], course_b["time"]):
                        return True, (
                            f"Conflict detected between {course_a['name']} and "
                            f"{course_b['name']} on {day} at overlapping times."
                        )

        return False, "No conflicts detected"

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
            return max(start_a, start_b) < min(end_a, end_b)
        except ValueError:
            return False

# Test the ScheduleValidator class
data = {"class_data":{"Monday":{"CS 2100":{"prof":"Briana Morrison","time":"9:00 am - 9:50 am","location":"Rice Hall 130","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00 am - 10:50 am","location":"Olsson Hall 120","rating":None},"APMA 3080":{"prof":"Asif Mahmood","time":"11:00 am - 11:50 am","location":"Thornton Hall E304","rating":4.33}},"Tuesday":{"ENGR 1020":{"prof":"Anna Leyf Starling","time":"11:00 am - 12:15 pm","location":"Dell 1 103","rating":4.33},"PHYS 1425":{"prof":"Atsushi Yoshida","time":"12:30 pm - 1:45 pm","location":"Physics Bldg 238","rating":None}},"Wednesday":{"CS 2100":{"prof":"Briana Morrison","time":"9:00 am - 9:50 am","location":"Rice Hall 130","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00 am - 10:50 am","location":"Olsson Hall 120","rating":None},"APMA 3080":{"prof":"Asif Mahmood","time":"11:00 am - 11:50 am","location":"Thornton Hall E304","rating":4.33}},"Thursday":{"ENGR 1020":{"prof":"Anna Leyf Starling","time":"11:00 am - 12:15 pm","location":"Dell 1 103","rating":4.33},"PHYS 1425":{"prof":"Atsushi Yoshida","time":"12:30 pm - 1:45 pm","location":"Physics Bldg 238","rating":None}},"Friday":{"CS 2100":{"prof":"Briana Morrison","time":"9:00 am - 9:50 am","location":"Rice Hall 130","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00 am - 10:50 am","location":"Olsson Hall 120","rating":None},"APMA 3080":{"prof":"Asif Mahmood","time":"11:00 am - 11:50 am","location":"Thornton Hall E304","rating":4.33}}}}
validator = ScheduleValidator()
is_valid, message = validator.validate_schedule(data, ["CS 2100", "CS 2120", "APMA 3080", "ENGR 1020", "PHYS 1425"])
print(f"Is valid: {is_valid}")
print(f"Message: {message}")
