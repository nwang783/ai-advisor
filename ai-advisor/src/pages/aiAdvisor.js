import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Plus, LogOut } from "lucide-react";
import ReactMarkdown from "react-markdown";
import "../styles/aiAdvisorStyles.css";
import { auth, db } from "../firebase";
import { doc, setDoc, collection, query, where, orderBy, getDocs } from 'firebase/firestore';
import { signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";
import { Pencil } from "lucide-react";

// Separate ChatHistory component
const ChatHistory = ({ currentUser, onThreadClick }) => {
  const [threads, setThreads] = useState([]);

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

  return (
    <div className="chat-history">
      {threads.map((thread) => (
        <div
          key={thread.id}
          className="chat-history-item"
          onClick={() => onThreadClick(thread.id)}
        >
          <div className="chat-history-name">{thread.name}</div>
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
          text: "Hello! I'm your BSCS AI advisor. How can I help you today?",
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
  
      // Transform the messages from the API into our message format and reverse the order
      const formattedMessages = data.messages
        .reverse()
        .map((msg, index) => ({
          id: index,
          text: msg.content,
          sender: msg.role === 'assistant' ? 'ai' : 'user'
        }));
  
      // Update messages state with the thread history
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
          <ChatHistory currentUser={currentUser} onThreadClick={handleThreadClick} />
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
