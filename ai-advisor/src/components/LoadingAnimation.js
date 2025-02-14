import React, { useState, useEffect } from 'react';
import { Calendar, Clock, BookOpen, GraduationCap } from 'lucide-react';

const LoadingAnimation = () => {
  const [iconIndex, setIconIndex] = useState(0);
  
  const icons = [
    <Calendar className="w-8 h-8" />,
    <Clock className="w-8 h-8" />,
    <BookOpen className="w-8 h-8" />,
    <GraduationCap className="w-8 h-8" />
  ];
  
  useEffect(() => {
    const interval = setInterval(() => {
      setIconIndex((prev) => (prev + 1) % icons.length);
    }, 600);
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="p-8 bg-white/90 rounded-lg shadow-md mx-auto max-w-sm">
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="text-gray-600 animate-spin transition-transform duration-300 hover:scale-110">
          {icons[iconIndex]}
        </div>
        <p className="text-black-600 text-center" style={{ color: '000000' }}>
          Building a schedule can take up to one minutes
        </p>
      </div>
    </div>
  );
};

export default LoadingAnimation;
