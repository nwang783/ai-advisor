import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import "../styles/aiAdvisorStyles.css";
import { functions } from "../firebase";
import { httpsCallable } from "firebase/functions";

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
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (inputMessage.trim() === "") return;

    // Add user message to the chat
    const newUserMessage = {
      id: messages.length,
      text: inputMessage,
      sender: "user",
    };

    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const csAdvisorChat = httpsCallable(functions, "csAdvisorChat");
      console.log(`Sending request:`, { user_message: inputMessage, thread_id: threadId });

      const result = await csAdvisorChat({
        user_message: inputMessage,
        thread_id: threadId,
      });

      const { response, thread_id } = result.data;

      // Update threadId
      setThreadId(thread_id);

      // Add AI response to the chat
      const newAIMessage = {
        id: messages.length + 1,
        text: response,
        sender: "ai",
      };

      setMessages((prev) => [...prev, newAIMessage]);
      setInputMessage("")
    } catch (error) {
      console.error("Error calling Firebase function:", error);
      const errorMessage = {
        id: messages.length + 1,
        text: "Sorry, there was an error processing your request.",
        sender: "ai",
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInputMessage("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
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
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
        />
        <button onClick={handleSendMessage}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default AIAdvisor;
