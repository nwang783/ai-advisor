import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ScheduleBuilder from './pages/scheduleBuilder';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ScheduleBuilder />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;