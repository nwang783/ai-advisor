import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import '../styles/classEditModalStyles.css';

const ClassEditModal = ({ isOpen, onClose, classData, onSave }) => {
  const [editedClass, setEditedClass] = useState({
    name: '',
    professor: '',
    location: '',
    colorClass: 'class-blue',
    meetings: [{ day: 'Monday', startTime: 9, endTime: 10 }]
  });
  
  // Update editedClass when classData changes
  useEffect(() => {
    if (classData) {
      setEditedClass(classData);
    }
  }, [classData]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(editedClass);
    onClose();
  };

  const handleMeetingChange = (meetingIndex, field, value) => {
    const newMeetings = [...editedClass.meetings];
    newMeetings[meetingIndex] = {
      ...newMeetings[meetingIndex],
      [field]: field.includes('Time') ? parseFloat(value) : value
    };
    setEditedClass({ ...editedClass, meetings: newMeetings });
  };

  const addMeeting = () => {
    setEditedClass({
      ...editedClass,
      meetings: [...editedClass.meetings, { day: 'Monday', startTime: 9, endTime: 10 }]
    });
  };

  const removeMeeting = (indexToRemove) => {
    if (editedClass.meetings.length > 1) {
      setEditedClass({
        ...editedClass,
        meetings: editedClass.meetings.filter((_, index) => index !== indexToRemove)
      });
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{classData ? 'Edit Class' : 'Add New Class'}</h2>
          <button className="close-button" onClick={onClose}>
            <X className="icon-small" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Class Name</label>
            <input
              type="text"
              value={editedClass.name}
              onChange={(e) => setEditedClass({ ...editedClass, name: e.target.value })}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label>Professor</label>
            <input
              type="text"
              value={editedClass.professor}
              onChange={(e) => setEditedClass({ ...editedClass, professor: e.target.value })}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              value={editedClass.location}
              onChange={(e) => setEditedClass({ ...editedClass, location: e.target.value })}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label>Class Color</label>
            <select
              value={editedClass.colorClass}
              onChange={(e) => setEditedClass({ ...editedClass, colorClass: e.target.value })}
              className="form-input"
            >
              <option value="class-blue">Blue</option>
              <option value="class-green">Green</option>
              <option value="class-purple">Purple</option>
              <option value="class-yellow">Yellow</option>
              <option value="class-pink">Pink</option>
            </select>
          </div>

          <div className="form-group">
            <div className="meeting-header">
              <label>Meeting Times</label>
              <button 
                type="button" 
                onClick={addMeeting}
                className="button-secondary-small"
              >
                Add Meeting
              </button>
            </div>
            {editedClass.meetings.map((meeting, index) => (
              <div key={index} className="meeting-inputs">
                <select
                  value={meeting.day}
                  onChange={(e) => handleMeetingChange(index, 'day', e.target.value)}
                  className="form-input"
                >
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                </select>

                <select
                  value={meeting.startTime}
                  onChange={(e) => handleMeetingChange(index, 'startTime', e.target.value)}
                  className="form-input"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 8).map(time => (
                    <option key={time} value={time}>
                      {time <= 12 ? time : time - 12}:00 {time < 12 ? 'AM' : 'PM'}
                    </option>
                  ))}
                </select>

                <select
                  value={meeting.endTime}
                  onChange={(e) => handleMeetingChange(index, 'endTime', e.target.value)}
                  className="form-input"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 8).map(time => (
                    <option key={time} value={time}>
                      {time <= 12 ? time : time - 12}:00 {time < 12 ? 'AM' : 'PM'}
                    </option>
                  ))}
                </select>

                {editedClass.meetings.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeMeeting(index)}
                    className="button-icon"
                  >
                    <X className="icon-small" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="modal-actions">
            <button type="button" className="button-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="button-primary">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ClassEditModal;
