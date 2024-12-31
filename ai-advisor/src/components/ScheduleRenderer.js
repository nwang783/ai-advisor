import React from 'react';
import '../styles/scheduleRendererStyles.css';

const ScheduleRenderer = ({ scheduleData }) => {
  if (!scheduleData?.class_data?.day_of_the_week) {
    return null;
  }

  const timeSlots = [];
  for (let hour = 7; hour <= 21; hour++) {
    const period = hour < 12 ? 'AM' : 'PM';
    const displayHour = hour <= 12 ? hour : hour - 12;
    timeSlots.push(`${displayHour} ${period}`);
  }

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  // Function to generate a random pastel color
  const generatePastelColor = (seed) => {
    // Use the class name as a seed for consistent colors
    const hash = seed.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
    
    // Generate pastel RGB values
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 90%)`;
  };

  const convertTo24Hour = (timeString) => {
    // Remove any spaces before am/pm
    const cleanTime = timeString.replace(/\s*(am|pm)/i, '$1');
    const [time, period] = cleanTime.toLowerCase().split(/(?=[ap]m)/);
    let [hours, minutes] = time.split(':');
    hours = parseInt(hours);
    minutes = parseInt(minutes);

    if (period === 'pm' && hours !== 12) {
      hours += 12;
    } else if (period === 'am' && hours === 12) {
      hours = 0;
    }

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  const getTimePosition = (timeString) => {
    const [startTime] = timeString.split(' - ');
    const time24h = convertTo24Hour(startTime);
    const [hours, minutes] = time24h.split(':').map(Number);
    const totalMinutes = hours * 60 + minutes;
    const startOfDay = 7 * 60; // 7 AM in minutes
    return ((totalMinutes - startOfDay) / 30);
  };

  const getClassDuration = (timeString) => {
    const [startTime, endTime] = timeString.split(' - ');
    const start24h = convertTo24Hour(startTime);
    const end24h = convertTo24Hour(endTime);
    
    const [startHours, startMinutes] = start24h.split(':').map(Number);
    const [endHours, endMinutes] = end24h.split(':').map(Number);
    
    const startTotalMinutes = startHours * 60 + startMinutes;
    const endTotalMinutes = endHours * 60 + endMinutes;
    return (endTotalMinutes - startTotalMinutes) / 30;
  };

  return (
    <div className="schedule-container">
      {/* Days header */}
      <div className="schedule-header">
        <div className="time-header"></div>
        {days.map(day => (
          <div key={day} className="day-header">
            {day}
          </div>
        ))}
      </div>

      {/* Time grid */}
      <div className="schedule-grid">
        {timeSlots.map((time, index) => (
          <div key={time} className="time-row">
            <div className="time-slot">
              {time}
            </div>
            {days.map(day => (
              <div key={`${day}-${time}`} className="grid-cell"></div>
            ))}
          </div>
        ))}

        {/* Classes */}
        {days.map((day, dayIndex) => {
          const dayClasses = scheduleData.class_data.day_of_the_week[day];
          if (!dayClasses) return null;

          return Object.entries(dayClasses).map(([className, details]) => {
            if (!details.time) return null;

            const startRow = getTimePosition(details.time);
            const duration = getClassDuration(details.time);
            const backgroundColor = generatePastelColor(className);

            return (
              <div
                key={`${day}-${className}`}
                className="class-block"
                style={{
                  top: `${(startRow * 48) + 48}px`,
                  height: `${duration * 48}px`,
                  left: `calc(${(dayIndex + 1) * 20}% - 18%)`,
                  width: '16%',
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
            );
          });
        })}
      </div>
    </div>
  );
};

export default ScheduleRenderer;
