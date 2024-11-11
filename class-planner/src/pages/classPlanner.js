import React, { useState } from 'react';
import { Plus, BookOpen } from 'lucide-react';
import '../styles/classPlannerStyles.css';
import ClassEditModal from '../components/classEditModal';

const ClassScheduler = () => {
  const [schedules, setSchedulules] = useState([
    { id: 1, name: 'Fall 2024' },
    { id: 2, name: 'Spring 2025' }
  ]);

  // Enhanced class data structure with meeting times
  const [classes, setClasses] = useState([
    {
      id: 1,
      name: 'Mathematics 101',
      colorClass: 'class-blue',
      meetings: [
        { day: 'Monday', startTime: 9, endTime: 10.5 },
        { day: 'Wednesday', startTime: 9, endTime: 10.5 }
      ],
      professor: 'Dr. Smith',
      location: 'Science Hall 101'
    },
    {
      id: 2,
      name: 'Physics 201',
      colorClass: 'class-green',
      meetings: [
        { day: 'Tuesday', startTime: 13, endTime: 14.5 },
        { day: 'Thursday', startTime: 13, endTime: 14.5 }
      ],
      professor: 'Dr. Johnson',
      location: 'Physics Building 305'
    },
    {
      id: 3,
      name: 'History 101',
      colorClass: 'class-purple',
      meetings: [
        { day: 'Monday', startTime: 14, endTime: 15.5 },
        { day: 'Wednesday', startTime: 14, endTime: 15.5 }
      ],
      professor: 'Prof. Williams',
      location: 'Humanities 205'
    }
  ]);

  const [selectedClass, setSelectedClass] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleClassClick = (classItem) => {
    setSelectedClass(classItem);
    setIsModalOpen(true);
  };

  const handleClassUpdate = (updatedClass) => {
    setClasses(classes.map(c => 
      c.id === updatedClass.id ? updatedClass : c
    ));
  };

  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const timeSlots = Array.from({ length: 12 }, (_, i) => i + 8); // 8 AM to 7 PM

  // Helper function to format time
  const formatTime = (time) => {
    const hours = Math.floor(time);
    const minutes = (time % 1) * 60;
    return `${hours % 12 || 12}:${minutes === 0 ? '00' : '30'} ${hours >= 12 ? 'PM' : 'AM'}`;
  };

  // Helper function to check if a class is scheduled for a specific day and time
  const getClassForTimeSlot = (day, time) => {
    return classes.find(classItem => 
      classItem.meetings.some(meeting => 
        meeting.day === day && 
        time >= meeting.startTime && 
        time < meeting.endTime
      )
    );
  };

  // Calculate if this is the first time slot for a class meeting
  const isStartTimeSlot = (day, time, classItem) => {
    return classItem.meetings.some(meeting => 
      meeting.day === day && 
      meeting.startTime === time
    );
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="app-header">
          <BookOpen className="app-icon" />
          <h1 className="app-title">ClassPlanner</h1>
        </div>
        
        <button className="new-schedule-btn">
          <Plus className="icon-small" />
          <span>New Schedule</span>
        </button>
        
        <div className="schedules-list">
          <h2 className="schedules-title">Your Schedules</h2>
          {schedules.map(schedule => (
            <button
              key={schedule.id}
              className="schedule-item"
            >
              {schedule.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Calendar Grid */}
        <div className="calendar-container">
          <div className="calendar-grid">
            {/* ... time header and days header ... */}
            {timeSlots.map(time => (
              <React.Fragment key={time}>
                <div className="time-slot">
                  {formatTime(time)}
                </div>
                {weekDays.map(day => {
                  const classItem = getClassForTimeSlot(day, time);
                  const isStart = classItem && isStartTimeSlot(day, time, classItem);
                  
                  return (
                    <div
                      key={`${day}-${time}`}
                      className={`calendar-cell ${classItem ? classItem.colorClass : ''}`}
                      onClick={() => classItem && handleClassClick(classItem)}
                    >
                      {isStart && (
                        <div className="class-info">
                          <div className="class-name">{classItem.name}</div>
                          <div className="class-details">
                            {classItem.location}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Current Classes */}
        <div className="classes-container">
          {classes.map(classItem => (
            <div
              key={classItem.id}
              className={`class-card ${classItem.colorClass}`}
              onClick={() => handleClassClick(classItem)}
            >
              <div className="class-name">{classItem.name}</div>
              <div className="class-schedule">
                {classItem.meetings.map((meeting, idx) => (
                  <div key={idx} className="meeting-time">
                    {meeting.day} {formatTime(meeting.startTime)} - {formatTime(meeting.endTime)}
                  </div>
                ))}
              </div>
              <div className="class-details">
                {classItem.professor} • {classItem.location}
              </div>
            </div>
          ))}
          <button className="add-class-btn">
            <Plus className="icon-small" />
            <span>Add Class</span>
          </button>
        </div>
      </div>

      {/* Edit Modal */}
      <ClassEditModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        classData={selectedClass}
        onSave={handleClassUpdate}
      />
    </div>
  );
};

export default ClassScheduler;
