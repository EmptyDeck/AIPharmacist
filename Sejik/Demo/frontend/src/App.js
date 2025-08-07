import React from "react";
import { Routes, Route } from "react-router-dom";
import MailPage from "./pages/MailPage";
import ChatPage from "./pages/ChatPage";
import LoginPage from "./pages/LoginPage";
import MainPage from "./pages/MainPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/mail" element={<MailPage />} />
      </Routes>
  );
}
