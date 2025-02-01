import React, { useState } from 'react';

const Modal = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay active" onClick={onClose}>
      <div className="modal-content active" onClick={e => e.stopPropagation()}>
        {children}
        <button className="modal-close" onClick={onClose}>×</button>
      </div>
    </div>
  );
};

const Calendar = ({ scheduleData }) => {
  const [selectedClass, setSelectedClass] = useState(null);  
  const [formattedData, setFormattedData] = useState(null);

  const formatData = (inputData) => {
    // Initialize output structure
    const output = {
      class_data: {
        day_of_the_week: {
          Monday: {},
          Tuesday: {},
          Wednesday: {},
          Thursday: {},
          Friday: {}
        }
      }
    };
  
    // Day mapping from schedule format to output format
    const dayMapping = {
      'Mo': 'Monday',
      'Tu': 'Tuesday',
      'We': 'Wednesday',
      'Th': 'Thursday',
      'Fr': 'Friday'
    };
  
    // Process each course
    for (const [courseName, sections] of Object.entries(inputData)) {
      for (const [sectionId, sectionData] of Object.entries(sections)) {
        // Get the schedule string (assuming first schedule in array)
        const scheduleStr = sectionData.schedule[0];
        
        // Extract days and time
        const [daysStr, timeStr] = scheduleStr.split(' ');
        const time = timeStr.trim();
        
        // Split days into individual day codes (Mo, Tu, etc.)
        const dayCodes = daysStr.match(/(Mo|Tu|We|Th|Fr)/g) || [];
  
        // Create course info object
        const courseInfo = {
          prof: sectionData.instructor || null,
          time: time,
          location: sectionData.location || null,
          rating: sectionData.rating || null,
          avg_gpa: sectionData.gpa || null,
          difficulty: sectionData.difficulty || null
        };
  
        // Add course to each day it occurs
        dayCodes.forEach(dayCode => {
          const fullDayName = dayMapping[dayCode];
          if (fullDayName) {
            output.class_data.day_of_the_week[fullDayName][courseName] = courseInfo;
          }
        });
      }
    }

    console.log(output);
    return output;
  };

  // Move data formatting to useEffect to avoid unnecessary recalculations
  React.useEffect(() => {
    if (scheduleData) {
      const normalized = formatData(scheduleData);
      setFormattedData(normalized);
    }
  }, [scheduleData]);

  const generatePastelColor = (seed) => {
    const hash = seed.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 90%)`;
  };

  const timeSlots = Array.from({ length: 15 }, (_, i) => {
    const hour = i + 7;
    const period = hour < 12 ? 'AM' : 'PM';
    const displayHour = hour <= 12 ? hour : hour - 12;
    return `${displayHour} ${period}`;
  });

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  const getClassForTimeSlot = (time, day) => {
    if (!formattedData?.class_data?.day_of_the_week[day]) return null;

    const dayClasses = formattedData.class_data.day_of_the_week[day];

    return Object.entries(dayClasses).find(([_, details]) => {
      if (!details.time) return false;
      const [startTime] = details.time.split(' - ');
      
      let [classHour, classMinutes] = startTime.toLowerCase().split(':');
      classHour = parseInt(classHour);
      const isPM = classMinutes.includes('pm');
      
      let normalizedClassHour = classHour;
      if (isPM && classHour !== 12) normalizedClassHour += 12;
      if (!isPM && classHour === 12) normalizedClassHour = 0;

      const [timeHour, timePeriod] = time.split(' ');
      let normalizedTimeHour = parseInt(timeHour);
      if (timePeriod === 'PM' && normalizedTimeHour !== 12) normalizedTimeHour += 12;
      if (timePeriod === 'AM' && normalizedTimeHour === 12) normalizedTimeHour = 0;

      return normalizedClassHour === normalizedTimeHour;
    });
  };

  if (!formattedData) return <div>Loading...</div>;

  return (
    <div className="schedule-container">
      <div className="calendar-grid">
        <div className="header-cell">Time</div>
        {days.map(day => (
          <div key={day} className="header-cell">{day}</div>
        ))}

        {timeSlots.map(time => (
          <React.Fragment key={time}>
            <div className="time-cell">{time}</div>
            {days.map(day => {
              const classInfo = getClassForTimeSlot(time, day);
              
              if (!classInfo) {
                return <div key={`${day}-${time}`} className="calendar-cell" />;
              }

              const [className, details] = classInfo;
              const backgroundColor = generatePastelColor(className);

              return (
                <div 
                  key={`${day}-${time}`} 
                  className="calendar-cell has-class cursor-pointer"
                  onClick={() => setSelectedClass({ className, details, day, time })}
                >
                  <div
                    className="class-content"
                    style={{
                      backgroundColor,
                      borderColor: backgroundColor.replace('90%', '80%')
                    }}
                  >
                    <div className="class-name truncate">{className}</div>
                    <div className="class-time text-xs">{details.time}</div>
                    <div className="class-time text-xs">{details.prof}</div>
                    <div className="class-time text-xs">Rating: ({details.rating ?? "N/A"})</div>
                  </div>
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      <Modal isOpen={!!selectedClass} onClose={() => setSelectedClass(null)}>
        {selectedClass && (
          <div>
            <h2 className="modal-title">{selectedClass.className}</h2>
            <div className="modal-info">
              <div className="info-group">
                <h3>Time</h3>
                <p>{selectedClass.details.time}</p>
              </div>
              <div className="info-group">
                <h3>Location</h3>
                <p>{selectedClass.details.location ?? 'N/A'}</p>
              </div>
              {selectedClass.details.prof && (
                <div className="info-group">
                  <h3>Instructor</h3>
                  <p>
                    {selectedClass.details.prof}
                    <span>{selectedClass.details.rating ? ` (Rating: ${selectedClass.details.rating})` : ' (Rating: N/A)'}</span>
                  </p>
                </div>
              )}
              {selectedClass.details.avg_gpa && (
                <div className="info-group">
                  <h3>Average GPA</h3>
                  <p>{selectedClass.details.avg_gpa}</p>
                </div>
              )}
              {selectedClass.details.difficulty && (
                <div className="info-group">
                  <h3>Difficulty</h3>
                  <p>{selectedClass.details.difficulty}</p>
                </div>
              )}
              <div className="info-group">
                <h3>Learn More</h3>
                <a
                  href={`https://thecourseforum.com/course/${selectedClass.className.split(' ')[0]}/${selectedClass.className.split(' ')[1]}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700"
                >
                  View on CourseForum
                </a>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Calendar;
