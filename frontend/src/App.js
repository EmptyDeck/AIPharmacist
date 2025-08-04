import React from "react";
import { Routes, Route } from "react-router-dom";
import MailPage from "./pages/MailPage";
import ChatPage from "./pages/ChatPage";
import LoginPage from "./pages/LoginPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="/mail" element={<MailPage />} />
      <Route path="/login" element={<LoginPage />} />
    </Routes>
  );
}
