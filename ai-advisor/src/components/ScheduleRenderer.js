import React from 'react';
import Markdown from 'markdown-to-jsx';
import '../styles/scheduleRendererStyles.css';

const ScheduleRenderer = ({ scheduleData }) => {
  const normalizeScheduleData = (data) => {
    if (!data?.class_data) return null;
    
    const normalized = {
      class_data: {
        day_of_the_week: {}
      }
    };

    if (data.class_data.day_of_the_week) {
      return data;
    }
    
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    days.forEach(day => {
      if (data.class_data[day]) {
        normalized.class_data.day_of_the_week[day] = data.class_data[day];
      }
    });

    return normalized;
  };

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
  const normalizedData = normalizeScheduleData(scheduleData);

  const getClassForTimeSlot = (time, day) => {
    if (!normalizedData?.class_data?.day_of_the_week[day]) return null;

    const dayClasses = normalizedData.class_data.day_of_the_week[day];
    
    return Object.entries(dayClasses).find(([_, details]) => {
      if (!details.time) return false;
      const [startTime] = details.time.split(' - ');
      const classHour = parseInt(startTime.split(':')[0]);
      const isPM = startTime.toLowerCase().includes('pm');
      
      let normalizedClassHour = classHour;
      if (isPM && classHour !== 12) normalizedClassHour += 12;
      if (!isPM && classHour === 12) normalizedClassHour = 0;

      const timeHour = parseInt(time.split(' ')[0]);
      const isTimeSlotPM = time.includes('PM');
      let normalizedTimeHour = timeHour;
      if (isTimeSlotPM && timeHour !== 12) normalizedTimeHour += 12;
      if (!isTimeSlotPM && timeHour === 12) normalizedTimeHour = 0;

      return normalizedClassHour === normalizedTimeHour;
    });
  };

  return (
    <div className="page-container">
      {/* Message Section */}
      {scheduleData.message && (
        <div className="message-container">
          <Markdown>
            {scheduleData.message}
          </Markdown>
        </div>
      )}
      
      {/* Schedule Section */}
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
                  <div key={`${day}-${time}`} className="calendar-cell">
                    <div 
                      className="class-content"
                      style={{
                        backgroundColor,
                        borderColor: backgroundColor.replace('90%', '80%')
                      }}
                    >
                      <div className="class-name">{className}</div>
                      <div className="class-time">{details.time}</div>
                      <div className="class-location">{details.location}</div>
                      {details.prof && (
                        <div className="class-professor">
                          {details.prof}
                          {details.rating && ` (${details.rating})`}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ScheduleRenderer;
