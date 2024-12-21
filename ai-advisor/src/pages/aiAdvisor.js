import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Plus, LogOut } from "lucide-react";
import ReactMarkdown from "react-markdown";
import "../styles/aiAdvisorStyles.css";
import { auth } from "../firebase";
import { signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";

const AIAdvisor = () => {
  const [messages, setMessages] = useState([
    {
      id: 0,
      text: "Hello! I'm your BSCS AI advisor. How can I help you today?",
      sender: "ai",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [currentUser, setCurrentUser] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    const user = auth.currentUser;
    if (user) {
      setCurrentUser(user);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      navigate("/"); // Redirect to the login page after logout
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-top">
          <button className="new-chat-button">
            <Plus size={16} />
            New chat
          </button>
          <div className="chat-history">
            {/* Chat history would go here */}
          </div>
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
        </div>
      </main>
    </div>
  );
};

export default AIAdvisor;
