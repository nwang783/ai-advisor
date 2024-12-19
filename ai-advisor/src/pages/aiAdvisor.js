import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import "../styles/aiAdvisorStyles.css";

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (inputMessage.trim() === "" || isLoading) return;

    // Add user message to the chat
    const newUserMessage = {
      id: messages.length,
      text: inputMessage,
      sender: "user",
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputMessage("")
    setIsLoading(true);

    try {
      // Instead of using httpsCallable, make a direct fetch to the Cloud Function URL
      const response = await fetch('https://cs-advisor-yjuaxbcwea-uc.a.run.app', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          threadId: threadId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);

      // Update threadId
      if (data.threadId) {
        setThreadId(data.threadId);
      }

      // Add AI response to the chat
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

  return (
    <div className="ai-advisor-container">
      <div className="chat-header">
        <h2>BSCS AI Advisor</h2>
      </div>
      <div className="chat-messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${
              message.sender === "user" ? "user-message" : "ai-message"
            }`}
          >
            {message.sender === "user" ? <User size={20} /> : <Bot size={20} />}
            <div className="message-content">
              {message.sender === "ai" ? (
                <ReactMarkdown>{message.text}</ReactMarkdown>
              ) : (
                message.text
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message ai-message">
            <Bot size={20} />
            <div className="message-content">
              <span className="loading-dots">Thinking</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button onClick={handleSendMessage} disabled={isLoading}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default AIAdvisor;
