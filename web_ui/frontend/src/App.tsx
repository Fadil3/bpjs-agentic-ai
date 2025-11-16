import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { PatientPage } from "./pages/PatientPage";
import { DoctorPage } from "./pages/DoctorPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/patient" element={<PatientPage />} />
        <Route path="/doctor" element={<DoctorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
