import React, { useState, useEffect } from 'react';
import { auth, db } from "../firebase";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import '../styles/scheduleBuilderStyles.css';
import LoadingAnimation from '../components/LoadingAnimation';
import Calendar from '../components/calendar';
import MessageContainer from '../components/messageContainer';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { collection, addDoc } from 'firebase/firestore';
import ScheduleHistory from '../components/scheduleHistory';
import TimeConstraintsComponent from '../components/TimeContraints';

let CLASS_DATA = [];

fetch('/unique_classes.json')
  .then(response => {
    if (!response.ok) {
      throw new Error("Error fetching class data");
    }
    return response.json();
  })
  .then(data => {
    CLASS_DATA = data;
  });

const ScheduleBuilder = () => {
  const [user, setUser] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [message, setMessage] = useState(null);
  const navigate = useNavigate();
  const [classInfo, setClassInfo] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchResults, setSearchResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [timeConstraints, setTimeConstraints] = useState({
    Mo: { start: '08:00', end: '18:00' },
    Tu: { start: '08:00', end: '18:00' },
    We: { start: '08:00', end: '18:00' },
    Th: { start: '08:00', end: '18:00' },
    Fr: { start: '08:00', end: '18:00' }
  });
  const [showTimeConstraintPopUp, setShowTimeConstraintPopUp] = useState(false);

  const Header = () => (
    <>
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <h1>AI Schedule Builder</h1>
          </div>
          <nav className="nav-links">
            <a href="/">Home</a>
            <a href="/schedules">Schedules</a>
            <a href="/contact">Contact</a>
          </nav>
          <div className="auth-buttons">
            {user ? (
              <button
                className="signup-btn"
                onClick={() => {
                  auth.signOut();
                  window.location.reload();
                }}
              >
                Sign Out
              </button>
            ) : (
              <button className="signup-btn" onClick={() => setIsOpen(true)}>
                Log In
              </button>
            )}
          </div>
        </div>
      </header>
      <LoginPopup isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );

  const LoginPopup = ({ isOpen, onClose }) => {
    const navigate = useNavigate();
    const auth = getAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
      firstName: '',
      lastName: '',
      email: '',
      password: '',
    });

    if (!isOpen) return null;

    const handleInputChange = (e) => {
      setFormData({
        ...formData,
        [e.target.name]: e.target.value
      });
      setError('');
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      setError('');

      try {
        if (isLogin) {
          await signInWithEmailAndPassword(auth, formData.email, formData.password);
        } else {
          await createUserWithEmailAndPassword(auth, formData.email, formData.password);
        }
        navigate('/');
        onClose();
      } catch (err) {
        switch (err.code) {
          case 'auth/invalid-email':
            setError('Invalid email address');
            break;
          case 'auth/user-disabled':
            setError('This account has been disabled');
            break;
          case 'auth/user-not-found':
            setError('No account found with this email');
            break;
          case 'auth/wrong-password':
            setError('Incorrect password');
            break;
          case 'auth/email-already-in-use':
            setError('Email already in use');
            break;
          case 'auth/weak-password':
            setError('Password should be at least 6 characters');
            break;
          default:
            setError('An error occurred. Please try again.');
        }
        console.error(err);
      }
    };

    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
          <div className="modal-body">
            <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
            <form onSubmit={handleSubmit}>
              {!isLogin && (
                <>
                  <div>
                    <label>First Name:</label>
                    <input
                      type="text"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div>
                    <label>Last Name:</label>
                    <input
                      type="text"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </>
              )}
              <div>
                <label>Email:</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className={error.includes('email') ? 'error' : ''}
                />
              </div>
              <div>
                <label>Password:</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className={error.includes('password') ? 'error' : ''}
                />
              </div>
              {error && <div className="error-message">{error}</div>}
              <button type="submit">
                {isLogin ? 'Login' : 'Sign Up'}
              </button>
            </form>
            <div className="auth-switch">
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                  setFormData({
                    firstName: '',
                    lastName: '',
                    email: '',
                    password: '',
                  });
                }}
                className="switch-button"
              >
                {isLogin ? 'Need an account? Sign up' : 'Already have an account? Login'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      if (user) {
        setUser(user);
        setLoading(false);
      } else {
        navigate("/");
      }
    });

    return () => unsubscribe();
  }, [navigate]);

  const handleSearch = (value) => {
    setSearchTerm(value);
    if (value.trim() === "") {
      setSearchResults([]);
      return;
    }

    const results = CLASS_DATA.filter(course =>
      `${course.Mnemonic} ${course.Number} ${course.Title}`
        .toLowerCase()
        .includes(value.toLowerCase())
    );
    setSearchResults(results);
  };

  const addClass = (course) => {
    if (classInfo.length >= 7) {
      alert("Maximum of 7 classes allowed");
      return;
    }
    if (!classInfo.find(c => c.Mnemonic === course.Mnemonic && c.Number === course.Number)) {
      setClassInfo([...classInfo, course]);
    }
    setSearchTerm("");
    setSearchResults([]);
  };

  const removeClass = (index) => {
    setClassInfo(classInfo.filter((_, i) => i !== index));
  };

  const formatInputClasses = async () => {
    const inputClasses = classInfo.map(classObj => 
      `${classObj.Mnemonic} ${classObj.Number}${classObj.Mnemonic === "EGMT" ? ` | ${classObj.Title}` : ''}`
    );
    console.log(`Input classes: ${inputClasses}`);
    return inputClasses;
  };

  const formatTimeConstraints = () => {
    return Object.entries(timeConstraints).reduce((acc, [day, times]) => {
      acc[day] = [formatToAMPM(times.start), formatToAMPM(times.end)];
      return acc;
    }, {});
  };

  const formatToAMPM = (time24) => {
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'pm' : 'am';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes}${ampm}`;
  };

  const createSchedule = async () => {
    if (classInfo.length === 0) {
      alert("Please select at least one class");
      return;
    }

    setLoading(true);
    const inputClasses = await formatInputClasses();
    const formattedTimeConstraints = formatTimeConstraints();

    try {
      const response = await fetch("https://csp-build-schedule-yjuaxbcwea-uc.a.run.app", { // http://127.0.0.1:5001/gpt-advisor/us-central1/csp_build_schedule https://csp-build-schedule-yjuaxbcwea-uc.a.run.app
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          input_classes: inputClasses,
          optimimze_ratings: true,
          time_constraints: formattedTimeConstraints,
        }),
      });

      if (!response.ok) {
        throw new Error("Error fetching response from AI assistant");
      }

      const data = await response.json();
      console.log(data);

      if (data.schedule) {
        setSchedule(data.schedule);
        const inputClassesArray = classInfo.map(classObj => ({
          Mnemonic: classObj.Mnemonic,
          Number: classObj.Number,
        }));
        await addDoc(collection(db, "schedules"), {
          schedule: data,
          createdBy: user.uid,
          semester: "Spring 2025",
          createdAt: new Date(),
          inputClasses: inputClassesArray,
        });
        console.log("Schedule set!");
      }
      if (data.message) {
        setMessage(data.message);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <Header />
      <div className="schedule-builder">
        <div className="search-container">
          <div className="search-box">
            <Search className="search-icon" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search for classes..."
              className="search-input"
            />
          </div>
          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((course, index) => (
                <div
                  key={index}
                  className="search-result-item"
                  onClick={() => addClass(course)}
                >
                  {course.Mnemonic} {course.Number} - {course.Title}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="main-content">
          <div className="top-section">
            <div className="left-panel">
              <div className="selected-classes">
                <h3>Selected Classes ({classInfo.length}/7)</h3>
                {classInfo.map((course, index) => (
                  <div key={index} className="selected-class">
                    <span>
                      {course.Mnemonic} {course.Number} - {course.Title}
                    </span>
                    <button onClick={() => removeClass(index)} className="remove-btn">
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              <div className="options-container">
                <button onClick={() => setShowTimeConstraintPopUp(true)} className='time-constraints-btn'>
                  Set Time Constraints
                </button>
              </div>
              <button
                onClick={createSchedule}
                className="create-schedule-btn"
                disabled={loading || classInfo.length === 0}
              >
                {user
                  ? loading
                    ? <LoadingAnimation />
                    : "Create Schedule"
                  : "Please log in to create a schedule"}
              </button>
              <p>Please email feedback to Nathan Wang at hmg2vg@virginia.edu</p>
            </div>
            <div className="calendar-container">
              {schedule && !loading && <Calendar scheduleData={schedule} />}
            </div>
          </div>
          {user && (
            <ScheduleHistory
              db={db}
              userId={user.uid}
              onScheduleSelect={(scheduleData) => {
                setSchedule(scheduleData);
                setMessage(scheduleData.message);
              }}
            />
          )}
          <div className="bottom-section">
            {message && !loading && <MessageContainer message={message} />}
          </div>
        </div>
      </div>
      {showTimeConstraintPopUp && (
        <div className="modal-overlay" onClick={() => setShowTimeConstraintPopUp(false)}>
          <div className="modal-content-time-constraints" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowTimeConstraintPopUp(false)}>
              ×
            </button>
            <TimeConstraintsComponent
              timeConstraints={timeConstraints}
              onTimeChange={setTimeConstraints}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduleBuilder;
