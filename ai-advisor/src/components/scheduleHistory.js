import React, { useEffect, useState } from 'react';
import { collection, query, where, getDocs } from 'firebase/firestore';
import '../styles/scheduleBuilderStyles.css';

const ScheduleHistory = ({ db, userId, onScheduleSelect }) => {
  const [schedules, setSchedules] = useState([]);
  const [selectedScheduleId, setSelectedScheduleId] = useState(null);

  useEffect(() => {
    const fetchSchedules = async () => {
      if (!userId) return;
      
      const schedulesQuery = query(
        collection(db, "schedules"),
        where("createdBy", "==", userId)
      );

      try {
        const querySnapshot = await getDocs(schedulesQuery);
        const schedulesList = querySnapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        schedulesList.sort((a, b) => b.createdAt - a.createdAt);
        setSchedules(schedulesList);
      } catch (error) {
        console.error("Error fetching schedules:", error);
      }
    };

    fetchSchedules();
  }, [db, userId]);

  const handleScheduleSelect = (schedule, id) => {
    setSelectedScheduleId(id);
    onScheduleSelect(schedule);
  };

  return (
    <div className="schedule-history">
      <h3>Previous Schedules</h3>
      <div className="schedule-cards">
        {schedules.map((schedule, index) => (
          <div
            key={schedule.id}
            onClick={() => handleScheduleSelect(schedule.schedule, schedule.id)}
            className={`schedule-card ${selectedScheduleId === schedule.id ? 'selected' : ''}`}
          >
            <div>Schedule {index + 1}</div>
            <div>{schedule.semester}</div>
            <div>
              Created at: {schedule.createdAt ? new Date(schedule.createdAt.seconds * 1000).toLocaleString() : ""}
            </div>
          </div>
        ))}
        {schedules.length === 0 && (
          <div>No previous schedules found</div>
        )}
      </div>
    </div>
  );
};

export default ScheduleHistory;
