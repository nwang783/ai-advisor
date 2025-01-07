import React, { useState, useEffect } from 'react';
import { auth } from "../firebase";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import '../styles/scheduleBuilderStyles.css';
import LoadingAnimation from '../components/LoadingAnimation';
import Calendar from '../components/calendar';
import MessageContainer from '../components/messageContainer';

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

const Header = () => (
    <header className="app-header">
        <div className="header-content">
        <div className="logo">
            <h1>Schedule Builder</h1>
        </div>
        <nav className="nav-links">
            <a href="/about">About</a>
            <a href="/service">Service</a>
            <a href="/faq">FAQ</a>
            <a href="/contacts">Contacts</a>
        </nav>
        <div className="auth-buttons">
            <button className="login-btn">Login</button>
            <button className="signup-btn">Sign up</button>
        </div>
        </div>
    </header>
);

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
                            <div className="spread-option">
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
                            </div>

                            <div className="custom-instructions">
                                <label>Custom Instructions:</label>
                                <textarea
                                    value={customInstructions}
                                    onChange={(e) => setCustomInstructions(e.target.value)}
                                    placeholder="Add any specific preferences (e.g., no classes before 9am)"
                                    className="custom-input"
                                />
                            </div>
                        </div>

                        <button 
                            onClick={createSchedule} 
                            className="create-schedule-btn"
                            disabled={loading || classInfo.length === 0}
                        >
                            {loading ? <LoadingAnimation /> : "Create Schedule"}
                        </button>
                        <p>Note: Currently, engagements are not supported. </p>
                        <p>Please email feedback to Nathan Wang at hmg2vg@virginia.edu</p>
                        {/* <p>{JSON.stringify(schedule)}</p> */}
                    </div>
                    <div className="right-panel">
                            {(message && !loading) && (
                                <MessageContainer message={message} />
                            )}
                    </div>

                    <div className="calendar-container">
                        {(schedule && !loading) && <Calendar scheduleData={schedule} />}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleBuilder;
