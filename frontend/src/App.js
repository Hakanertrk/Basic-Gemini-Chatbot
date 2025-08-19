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
              <div className="form-toggle-wrapper">
                <p>Zaten üyeyim?</p>
                <button onClick={() => setShowRegister(false)}>Giriş Yap</button>
              </div>

            </>
          ) : (
            <>
              <Login setToken={setToken} />
                <div className="form-toggle-wrapper">
                  <p>Hesabın yok mu?</p>
                  <button onClick={() => setShowRegister(true)}>Kayıt Ol</button>
                </div>
            </>
          )}
        </>
      ) : (
        <>
          <h1 className="app-title">CHATDOC</h1>
          <h2 className="app-subtitle">Sağlığınız için AI.</h2>
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
