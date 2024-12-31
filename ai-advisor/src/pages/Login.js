import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import '../styles/loginStyles.css';
import heroImage from '../assets/login-image.jpg';
import '../firebase'

const Login = () => {
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

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear any previous errors when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (isLogin) {
        // Handle login
        await signInWithEmailAndPassword(auth, formData.email, formData.password);
      } else {
        // Handle sign up
        await createUserWithEmailAndPassword(auth, formData.email, formData.password);
        // Note: If you need to store additional user data (firstName, lastName),
        // you would need to add it to Firestore or Realtime Database here
      }
      
      // If authentication is successful, navigate to aiAdvisor page
      navigate('/scheduleBuilder');
      
    } catch (err) {
      // Handle different Firebase auth errors
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
    <div className="login-container">
      <div className="content-wrapper">
        <div className="hero-section">
          <img 
            src={heroImage} 
            alt="Landscape" 
            className="hero-image" 
          />
          <div className="hero-text">
            <h2>Under Construction...,</h2>
            <h2>Pardon the bad UI</h2>
            <div className="hero-dots">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot active"></span>
            </div>
          </div>
        </div>

        <div className="form-section">
          <div className="form-container">
            <h2>{isLogin ? 'Welcome back' : 'Create an account'}</h2>
            <p className="form-switch">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button 
                className="switch-button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
              >
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </p>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleSubmit}>
              {!isLogin && (
                <div className="name-fields">
                  <div className="input-field">
                    <input
                      type="text"
                      name="firstName"
                      placeholder="First name"
                      value={formData.firstName}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="input-field">
                    <input
                      type="text"
                      name="lastName"
                      placeholder="Last name"
                      value={formData.lastName}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              )}
              <div className="input-field">
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>
              <div className="input-field">
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleInputChange}
                />
              </div>
              
              <button type="submit" className="submit-button">
                {isLogin ? 'Log in' : 'Create account'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
