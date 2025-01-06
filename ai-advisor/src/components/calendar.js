import React from 'react';

const Calendar = ({ scheduleData }) => {
  const normalizeScheduleData = (data) => {
    // Data is already in the correct format, no need for complex normalization
    return data;
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
      
      // Convert class time to 24-hour format
      let [classHour, classMinutes] = startTime.toLowerCase().split(':');
      classHour = parseInt(classHour);
      const isPM = classMinutes.includes('pm');
      
      let normalizedClassHour = classHour;
      if (isPM && classHour !== 12) normalizedClassHour += 12;
      if (!isPM && classHour === 12) normalizedClassHour = 0;

      // Convert time slot to 24-hour format
      const [timeHour, timePeriod] = time.split(' ');
      let normalizedTimeHour = parseInt(timeHour);
      if (timePeriod === 'PM' && normalizedTimeHour !== 12) normalizedTimeHour += 12;
      if (timePeriod === 'AM' && normalizedTimeHour === 12) normalizedTimeHour = 0;

      return normalizedClassHour === normalizedTimeHour;
    });
  };

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
                <div key={`${day}-${time}`} className="calendar-cell has-class">
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
                        {details.rating && ` (${details.rating})` || ' (N/A)'}
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
  );
};

export default Calendar;
