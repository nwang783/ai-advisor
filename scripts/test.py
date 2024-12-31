from pydantic import BaseModel

class StructuredOutput(BaseModel):
    class_info: dict
    message: str

# Create an instance
test_output = StructuredOutput(
    class_info={"Monday": {"CS101": {"prof": "Smith", "time": "10AM"}}},
    message="Schedule successfully parsed."
)

# Test serialization
print(test_output.json())

