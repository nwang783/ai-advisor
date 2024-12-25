// AIAdvisor Component
import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Plus, LogOut, Pencil } from "lucide-react";
import ReactMarkdown from "react-markdown";
import "../styles/aiAdvisorStyles.css";
import { auth, db } from "../firebase";
import { doc, setDoc, collection, query, where, orderBy, getDocs, updateDoc } from 'firebase/firestore';
import { signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";

const ChatHistory = ({ currentUser, onThreadClick, selectedThreadId }) => {
  const [threads, setThreads] = useState([]);
  const [editingThreadId, setEditingThreadId] = useState(null);
  const [newName, setNewName] = useState("");

  useEffect(() => {
    const fetchThreads = async () => {
      if (!currentUser?.email) return;
      
      const threadsRef = collection(db, 'threads');
      const q = query(
        threadsRef,
        where('createdBy', '==', currentUser.email),
        orderBy('createdAt', 'desc')
      );

      const querySnapshot = await getDocs(q);
      const threadList = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      
      setThreads(threadList);
    };

    fetchThreads();
  }, [currentUser]);

  const handleRename = async (threadId) => {
    if (!newName.trim()) {
      setEditingThreadId(null);
      return;
    }

    try {
      const threadRef = doc(db, 'threads', threadId);
      await updateDoc(threadRef, {
        name: newName.trim()
      });

      setThreads(threads.map(thread => 
        thread.id === threadId 
          ? { ...thread, name: newName.trim() }
          : thread
      ));

      setEditingThreadId(null);
      setNewName("");
    } catch (error) {
      console.error("Error renaming thread:", error);
    }
  };

  const handleKeyPress = (e, threadId) => {
    if (e.key === "Enter") {
      handleRename(threadId);
    } else if (e.key === "Escape") {
      setEditingThreadId(null);
      setNewName("");
    }
  };

  return (
    <div className="chat-history">
      {threads.map((thread) => (
        <div
          key={thread.id}
          className={`chat-history-item ${selectedThreadId === thread.id ? 'selected' : ''}`}
          onClick={() => onThreadClick(thread.id)}
        >
          <div className="chat-history-content">
            {editingThreadId === thread.id ? (
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => handleKeyPress(e, thread.id)}
                onBlur={() => handleRename(thread.id)}
                autoFocus
                onClick={(e) => e.stopPropagation()}
                className="rename-input"
              />
            ) : (
              <>
                <div className="chat-history-name">{thread.name}</div>
                <button 
                  className="rename-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingThreadId(thread.id);
                    setNewName(thread.name);
                  }}
                >
                  <Pencil size={14} />
                </button>
              </>
            )}
          </div>
          <div className="chat-history-date">
            {thread.createdAt?.toDate().toLocaleDateString()}
          </div>
        </div>
      ))}
      {threads.length === 0 && (
        <div className="no-chats">No chat history</div>
      )}
    </div>
  );
};

const AIAdvisor = () => {
  const [messages, setMessages] = useState([
    {
      id: 0,
      text: "Hello! I'm your AI advisor. How can I help you today?",
      sender: "ai",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isPopupOpen, setIsPopupOpen] = useState(true);

  const togglePopup = () => {
    setIsPopupOpen(!isPopupOpen);
  };

  const navigate = useNavigate();

  useEffect(() => {
    const user = auth.currentUser;
    if (user) {
      setCurrentUser(user);
    } else {
      navigate("/");
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const createNewThread = async () => {
    try {
      const response = await fetch("https://make-new-thread-yjuaxbcwea-uc.a.run.app", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("New thread data:", data);

      if (data.threadId) {
        setThreadId(data.threadId);
      }

      setMessages([
        {
          id: 0,
          text: "Hello! I'm your AI advisor. How can I help you today?",
          sender: "ai",
        },
      ]);    

      const threadRef = doc(db, "threads", data.threadId);
      await setDoc(threadRef, {
        threadId: data.threadId,
        createdAt: new Date(),
        messages: [],
        createdBy: currentUser.email,
        name: "New Chat",
      });
      
    } catch (error) {
      console.error("Error creating new thread:", error);
    }
  };

  const handleSendMessage = async () => {
    if (inputMessage.trim() === "" || isLoading) return;

    const newUserMessage = {
      id: messages.length,
      text: inputMessage,
      sender: "user",
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("https://cs-advisor-yjuaxbcwea-uc.a.run.app", {
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
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response data:", data);

      if (data.threadId) {
        setThreadId(data.threadId);
      }

      const newAIMessage = {
        id: messages.length + 1,
        text: data.response,
        sender: "ai",
      };

      setMessages((prev) => [...prev, newAIMessage]);
    } catch (error) {
      console.error("Error calling Cloud Function:", error);
      const errorMessage = {
        id: messages.length + 1,
        text: "Sorry, there was an error processing your request. Please try again later.",
        sender: "ai",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate("/");
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  const handleThreadClick = async (threadId) => {
    try {
      setThreadId(threadId);
      setIsLoading(true);
  
      const response = await fetch(`https://get-messages-from-thread-yjuaxbcwea-uc.a.run.app?threadId=${threadId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
      
      if (!data.messages || data.messages.length === 0) {
        setMessages([{
          id: 0,
          text: "This thread is empty. Start a conversation!",
          sender: "ai",
        }]);
        return;
      }
  
      const formattedMessages = data.messages
        .reverse()
        .map((msg, index) => ({
          id: index,
          text: msg.content,
          sender: msg.role === 'assistant' ? 'ai' : 'user'
        }));
  
      setMessages(formattedMessages);
  
    } catch (error) {
      console.error("Error fetching thread messages:", error);
      setMessages([{
        id: 0,
        text: "Sorry, there was an error loading this conversation. Please try again later.",
        sender: "ai",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-top">
          <button className="new-chat-button" onClick={createNewThread}>
            <Plus size={16} />
            New chat
          </button>
          <ChatHistory 
            currentUser={currentUser} 
            onThreadClick={handleThreadClick}
            selectedThreadId={threadId}
          />
        </div>
        <div className="sidebar-bottom">
          <div className="user-info">
            <div className="user-avatar">
              {currentUser ? currentUser.email?.[0].toUpperCase() : "?"}
            </div>
            <div className="user-name">
              {currentUser ? currentUser.email || "Anonymous" : "Loading..."}
            </div>
          </div>
          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="chat-container">
        <div className="chat-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${
                message.sender === "user" ? "user-message" : "ai-message"
              }`}
            >
              <div className="message-wrapper">
                <div className="message-icon">
                  {message.sender === "user" ? <User size={24} /> : <Bot size={24} />}
                </div>
                <div className="message-content">
                  {message.sender === "ai" ? (
                    <ReactMarkdown>{message.text}</ReactMarkdown>
                  ) : (
                    message.text
                  )}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message ai-message">
              <div className="message-wrapper">
                <div className="message-icon">
                  <Bot size={24} />
                </div>
                <div className="message-content">
                  <span className="loading-dots">Thinking</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message your CS advisor..."
              disabled={isLoading}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={isLoading || !inputMessage.trim()}
            >
              <Send size={16} />
            </button>
          </div>
          {/* Circular popup button */}
          <button className="popup-circle-button" onClick={togglePopup}>
            ?
          </button>

          {/* Popup content */}
          {isPopupOpen && (
            <div className="popup-overlay">
              <div className="popup">
                <h2>Instructions</h2>
                <p>This is an AI tool designed to help UVA students build their class schedules. It has access to The Course Forum and Lou's List, and thus can utilize professor ratings and class times. Currently, you must identify a class based on its mnemonic and number. For example, "APMA 3080" instead of "Linear Algebra." </p>
                <p>Note: The AI advisor only has access to courses offered Spring 2025.</p>
                <p><strong>Example prompt:</strong><br />
                I want to make a schedule for next semester. Here are the classes I want to take: APMA 3080, CS 2120, CS 2100, and ENGR 1020. Prioritize a good professor for APMA 3080. Do not worry about if the class is full. Make sure to also select a lab time for CS 2100. </p>
                <p><strong>Feedback:</strong><br />
                Please reach out to Nathan Wang (hm2vg@virginia.edu) with any bugs or improvements.</p>
                <button onClick={togglePopup}>Close</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AIAdvisor;
