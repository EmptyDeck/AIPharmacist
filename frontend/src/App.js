import React from "react";
import { Routes, Route } from "react-router-dom";
import MainPage from "./pages/MainPage";
import ChatPage from "./pages/ChatPage";


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/chat" element={<ChatPage />} />
    </Routes>
  );
}

