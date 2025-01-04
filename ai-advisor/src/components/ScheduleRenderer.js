import React from 'react';
import MessageContainer from './messageContainer';
import Calendar from './calendar';
import '../styles/scheduleRendererStyles.css';

const ScheduleRenderer = ({ scheduleData }) => {
  return (
    <div className="page-container">
      {/* Message Section */}
      {scheduleData.message && (
        <MessageContainer message={scheduleData.message} />
      )}

      {/* Calendar Section */}
      <Calendar scheduleData={scheduleData} />
    </div>
  );
};

export default ScheduleRenderer;
