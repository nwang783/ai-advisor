import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import AiAdvisor from './pages/aiAdvisor';
import ScheduleBuilder from './pages/scheduleBuilder';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/aiAdvisor" element={<AiAdvisor />} />
        <Route path="/scheduleBuilder" element={<ScheduleBuilder />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;