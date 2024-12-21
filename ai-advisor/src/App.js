import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import AiAdvisor from './pages/aiAdvisor';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/aiAdvisor" element={<AiAdvisor />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;