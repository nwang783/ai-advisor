import React, { useState, useEffect } from 'react';
import { auth } from "../firebase";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import '../styles/scheduleBuilderStyles.css';
import LoadingAnimation from '../components/LoadingAnimation';
import Calendar from '../components/calendar';
import MessageContainer from '../components/messageContainer';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';

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
    const [scheduleNotes, setScheduleNotes] = useState(null);
    const [message, setMessage] = useState(null);
    const navigate = useNavigate();
    const [threadId, setThreadId] = useState(null);
    const [classInfo, setClassInfo] = useState([]);
    const [customInstructions, setCustomInstructions] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(true);
    const [spread, setSpread] = useState("evenly");
    const [searchResults, setSearchResults] = useState([]);
    const [timePreferenceEarly, setTimePreferenceEarly] = useState("");
    const [timePreferenceLate, setTimePreferenceLate] = useState("");
    const [isOpen, setIsOpen] = useState(false);

    const Header = () => (
        <>
            <header className="app-header">
                <div className="header-content">
                    <div className="logo">
                        <h1>Schedule Builder</h1>
                    </div>
                    <nav className="nav-links">
                        <a href="/">Home</a>
                        <a href="/schedules">Schedules</a>
                        <a href="/contact">Contact</a>
                    </nav>
                    <div className="auth-buttons">
                    {user ? (
                        <button className="signup-btn" onClick={() => {auth.signOut(); window.location.reload();}}>
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
                    <button className="modal-close" onClick={onClose}>×</button>
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

        // Filter classes based on search term
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

    const createInputMessage = async () => {
        let inputMessage = "I want to create a schedule for the following classes: ";
        classInfo.forEach((classObj) => {
            inputMessage += `${classObj.Mnemonic} ${classObj.Number}, `;
        });
        inputMessage += `I want my classes to ${spread} be spread out across the five days of the week. Do not worry if the classes are full.`;
        if (customInstructions) {
            inputMessage += customInstructions;
        }
        if (timePreferenceEarly) {
            inputMessage += `${timePreferenceEarly}. `;
        }
        if (timePreferenceLate) {
            inputMessage += `${timePreferenceLate}. `;
        }

        inputMessage += "Put your detailed reasoning in the message!!!";
        console.log(`Input message: ${inputMessage}`)
        return inputMessage;
    };

    const createSchedule = async () => {
        if (classInfo.length === 0) {
            alert("Please select at least one class");
            return;
        }
        
        setLoading(true);
        try {
            const inputMessage = await createInputMessage();
            // Remember to switch URL back to non-local when deploying
            const response = await fetch("https://schedule-builder-yjuaxbcwea-uc.a.run.app", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: inputMessage,
                    threadId: threadId,
                }),
            });

            if (!response.ok) {
                throw new Error("Error fetching response from AI assistant");
            }

            const data = await response.json();
            console.log(data);

            if (data.threadId) {
                // setThreadId(data.threadId); //Temporarily commented out so we don't keep using the same thread
            }

            if (data.class_data) {
                setSchedule(data);  
                console.log("Schedule set!")
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
                <Header isOpen={isOpen} setIsOpen={setIsOpen} />
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
                                        <span>{course.Mnemonic} {course.Number} - {course.Title}</span>
                                        <button onClick={() => removeClass(index)} className="remove-btn">
                                            Remove
                                        </button>
                                    </div>
                                ))}
                            </div>

                            <div className="options-container">
                                {/* <div className="spread-option">
                                    <label>Schedule Spread:</label>
                                    <select 
                                        value={spread} 
                                        onChange={(e) => setSpread(e.target.value)}
                                        className="spread-select"
                                    >
                                        <option value="evenly">Evenly Spread</option>
                                        <option value="minimally">Minimally Spread</option>
                                        <option value="moderately">Moderately Spread</option>
                                    </select>
                                </div> */}
                                <div className="spread-option">
                                    <label>Time Preference:</label>
                                    <select 
                                        value={timePreferenceEarly} 
                                        onChange={(e) => setTimePreferenceEarly(e.target.value)}
                                        className="spread-select"
                                    >
                                        <option value="">Select an option</option>
                                        <option value="No classes before 8AM">No classes before 8AM</option>
                                        <option value="No classes before 9PM">No classes before 9PM</option>
                                        <option value="No classes before 10PM">No classes before 10PM</option>
                                    </select>
                                    <select
                                        value={timePreferenceLate} 
                                            onChange={(e) => setTimePreferenceLate(e.target.value)}
                                            className="spread-select"
                                        >
                                        <option value="">Select an option</option>
                                        <option value="No classes after 4PM">No classes after 4PM</option>
                                        <option value="No classes after 5PM">No classes after 5PM</option>
                                        <option value="No classes after 6PM">No classes after 6PM</option>
                                        <option value="No classes after 7PM">No classes after 7PM</option>
                                        <option value="No classes after 8PM">No classes after 8PM</option>
                                    </select>
                                </div>

                                <div className="custom-instructions">
                                    <label>Custom Instructions:</label>
                                    <textarea
                                        value={customInstructions}
                                        onChange={(e) => setCustomInstructions(e.target.value)}
                                        placeholder="Add any specific preferences (e.g., prioritize a certain professor)"
                                        className="custom-input"
                                    />
                                </div>
                            </div>

                            <button 
                                onClick={createSchedule} 
                                className="create-schedule-btn"
                                disabled={loading || classInfo.length === 0}
                            >
                                {user ? loading ? <LoadingAnimation /> : "Create Schedule" : "Please log in to create a schedule"}
                            </button>
                            <p>Note: Currently, engagements are not supported. </p>
                            <p>Please email feedback to Nathan Wang at hmg2vg@virginia.edu</p>
                        </div>

                        <div className="calendar-container">
                            {(schedule && !loading) && <Calendar scheduleData={schedule} />}
                        </div>
                    </div>

                    <div className="bottom-section">
                        {(message && !loading) && (
                            <MessageContainer message={message} />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleBuilder;
