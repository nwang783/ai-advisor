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

# Test the fixed validator
def test_schedule_validator():
    # Test data with known conflicts
    data = {
        "message": "...",
        "class_data": {
            "day_of_the_week": {
                "Monday": {
                    "APMA 3080": {
                        "prof": "Asif Mahmood",
                        "time": "11:00am - 11:50am",
                        "location": "Thornton Hall E304",
                        "rating": 4.33
                    },
                    "ENGR 1020": {
                        "prof": "Anna Leyf Starling",
                        "time": "11:00am - 12:15pm",
                        "location": "Dell 1 103",
                        "rating": 4.33
                    }
                }
            }
        }
    }

    validator = ScheduleValidator()
    is_valid, messages = validator.validate_schedule(data)
    
    print(f"Schedule validity: {is_valid}")
    print("Validation messages:")
    for msg in messages:
        print(f"- {msg}")

    # Now test with your full original data
    full_data = {"message":"...","class_data":{"day_of_the_week":{"Monday":{"APMA 3080":{"prof":"Asif Mahmood","time":"11:00am - 11:50am","location":"Thornton Hall E304","rating":4.33},"ENGR 1020":{"prof":"Anna Leyf Starling","time":"11:00am - 12:15pm","location":"Dell 1 103","rating":4.33},"CS 2100":{"prof":"Briana Morrison","time":"12:00pm - 12:50pm","location":"Chemistry Bldg 402","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00am - 10:50am","location":"Olsson Hall 120","rating":3.5}},"Tuesday":{"PHYS 1425":{"prof":"Atsushi Yoshida","time":"12:30pm - 1:45pm","location":"Physics Bldg 238","rating":3.5}},"Wednesday":{"APMA 3080":{"prof":"Asif Mahmood","time":"11:00am - 11:50am","location":"Thornton Hall E304","rating":4.33},"ENGR 1020":{"prof":"Anna Leyf Starling","time":"11:00am - 12:15pm","location":"Dell 1 103","rating":4.33},"CS 2100":{"prof":"Briana Morrison","time":"12:00pm - 12:50pm","location":"Chemistry Bldg 402","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00am - 10:50am","location":"Olsson Hall 120","rating":3.5}},"Thursday":{"PHYS 1425":{"prof":"Atsushi Yoshida","time":"12:30pm - 1:45pm","location":"Physics Bldg 238","rating":3.5}},"Friday":{"APMA 3080":{"prof":"Asif Mahmood","time":"11:00am - 11:50am","location":"Thornton Hall E304","rating":4.33},"CS 2100":{"prof":"Briana Morrison","time":"12:00pm - 12:50pm","location":"Chemistry Bldg 402","rating":3.2},"CS 2120":{"prof":"David Evans","time":"10:00am - 10:50am","location":"Olsson Hall 120","rating":3.5}}}}}
    
    print("\nTesting full schedule:")
    is_valid, messages = validator.validate_schedule(full_data)
    print(f"Schedule validity: {is_valid}")
    print("Validation messages:")
    for msg in messages:
        print(f"- {msg}")

if __name__ == "__main__":
    test_schedule_validator()
    