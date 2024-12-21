// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFunctions, httpsCallable } from "firebase/functions";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyC0ilBA-zmyMTVOpmMvahaWYoI-tB2uAoo",
  authDomain: "gpt-advisor.firebaseapp.com",
  projectId: "gpt-advisor",
  storageBucket: "gpt-advisor.firebasestorage.app",
  messagingSenderId: "534912686186",
  appId: "1:534912686186:web:81614ce3133e27947c5213",
  measurementId: "G-WV5WEMM2TS"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const functions = getFunctions(app);
export const auth = getAuth(app);