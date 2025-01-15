import React, { useEffect, useState } from 'react';
import { collection, query, where, getDocs } from 'firebase/firestore';
import '../styles/scheduleBuilderStyles.css';

const ScheduleHistory = ({ db, userId, onScheduleSelect }) => {
  const [schedules, setSchedules] = useState([]);

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
        setSchedules(schedulesList);
      } catch (error) {
        console.error("Error fetching schedules:", error);
      }
    };

    fetchSchedules();
  }, [db, userId]);

  return (
    <div className="schedule-history">
      <h3>Previous Schedules</h3>
      <div className="schedule-cards">
        {schedules.map((schedule, index) => (
          <div
            key={schedule.id}
            onClick={() => onScheduleSelect(schedule.schedule)}
            className="schedule-card"
          >
            <div>Schedule {index + 1}</div>
            <div>{schedule.semester}</div>
            <div>
              {schedule.schedule.class_data?.length || 0} classes
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
