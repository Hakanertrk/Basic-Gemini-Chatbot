import React, { useState } from "react";
import ChatBox from "./ChatBox";
import Login from "./Login";
import Register from "./Register";
import "./App.css";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="app">
      {!token ? (
        <>
          {showRegister ? (
            <>
              <Register setToken={setToken} />
              <p>
                Zaten üyeyim?{" "}
                <button onClick={() => setShowRegister(false)}>Giriş Yap</button>
              </p>
            </>
          ) : (
            <>
              <Login setToken={setToken} />
              <p>
                Hesabın yok mu?{" "}
                <button onClick={() => setShowRegister(true)}>Kayıt Ol</button>
              </p>
            </>
          )}
        </>
      ) : (
        <>
          <h1 className="app-title">EMMIChat</h1>
          <h2 className="app-subtitle">Gemini ile Sohbet Et</h2>
          <ChatBox token={token} />
          <button
            onClick={() => {
              localStorage.removeItem("token");
              setToken("");
            }}
          >
            Çıkış Yap
          </button>
        </>
      )}
    </div>
  );
}

export default App;
