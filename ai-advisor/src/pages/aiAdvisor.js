import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import '../styles/aiAdvisorStyles.css';

const AIAdvisor = () => {
  const [messages, setMessages] = useState([
    { 
      id: 0, 
      text: "Hello! I'm your AI assistant. How can I help you today?", 
      sender: 'ai' 
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (inputMessage.trim() === '') return;

    // Add user message
    const newUserMessage = {
      id: messages.length,
      text: inputMessage,
      sender: 'user'
    };

    // Simulate AI response (replace with actual AI logic)
    const newAIMessage = {
      id: messages.length + 1,
      text: `You said: "${inputMessage}". I'm still learning how to respond.`,
      sender: 'ai'
    };

    setMessages(prevMessages => [...prevMessages, newUserMessage, newAIMessage]);
    setInputMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="ai-advisor-container">
      <div className="chat-header">
        <h2>AI Advisor</h2>
      </div>
      <div className="chat-messages">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
          >
            {message.sender === 'user' ? <User size={20} /> : <Bot size={20} />}
            <div className="message-content">
              {message.text}
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
