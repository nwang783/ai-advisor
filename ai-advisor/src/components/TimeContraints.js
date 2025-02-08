import React from 'react';
import { Clock } from 'lucide-react';

const TimeConstraintsComponent = ({ timeConstraints, onTimeChange }) => {
  const daysFullNames = {
    Mo: 'Monday',
    Tu: 'Tuesday',
    We: 'Wednesday',
    Th: 'Thursday',
    Fr: 'Friday'
  };

  const handleTimeChange = (day, type, value) => {
    onTimeChange({
      ...timeConstraints,
      [day]: {
        ...timeConstraints[day],
        [type]: value
      }
    });
  };

  const formatTimeForDisplay = (time24) => {
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'pm' : 'am';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes}${ampm}`;
  };

  return (
    <div className="w-full max-w-2xl bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-gray-900">
          <Clock className="w-5 h-5" />
          Time Constraints
        </h2>
      </div>
      <div className="p-6">
        <div className="space-y-4">
          {Object.entries(timeConstraints).map(([day, times]) => (
            <div key={day} className="flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg transition-colors">
              <div className="w-32 font-medium text-gray-700">
                {daysFullNames[day]}
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="time"
                  value={times.start}
                  onChange={(e) => handleTimeChange(day, 'start', e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                />
                <span className="text-gray-500">to</span>
                <input
                  type="time"
                  value={times.end}
                  onChange={(e) => handleTimeChange(day, 'end', e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                />
                <div className="text-sm text-gray-500">
                  ({formatTimeForDisplay(times.start)} - {formatTimeForDisplay(times.end)})
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TimeConstraintsComponent;
