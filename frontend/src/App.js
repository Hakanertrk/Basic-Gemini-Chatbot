import React from "react";
import ChatBox from "./ChatBox";
import "./App.css";

function App() {
  return (
    <div className="app">
      <h1 className="app-title">EMMIChat</h1>
      <h2 className="app-subtitle">Gemini ile Sohbet Et</h2>
      <ChatBox />
    </div>
  );
}

export default App;
