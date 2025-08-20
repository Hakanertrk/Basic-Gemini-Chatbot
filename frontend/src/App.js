import React, { useState } from "react";
import ChatBox from "./ChatBox";
import Login from "./Login";
import Register from "./Register";
import Profile from "./Profile";
import "./App.css";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [showRegister, setShowRegister] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  // Başlık için ekran tipi belirleme
  const screen = !token ? "login" : showProfile ? "profile" : "chat";

  return (
    <div className="app">
      {/* Başlık */}
      <h1 className={`app-title ${screen === "login" ? "center-title" : "top-left-title"}`}>
        CHATDOC 🩺
      </h1>
      {screen === "login" && <h2 className="app-subtitle">Sağlığınız için AI.</h2>}

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
          {/* Sağ üst köşe menü */}
          <div className="top-right-menu">
            <button onClick={() => setShowProfile(!showProfile)}>
              {showProfile ? "Chat" : "Profil"}
            </button>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                setToken("");
                setShowProfile(false);
              }}
            >
              Çıkış Yap
            </button>
          </div>

          {showProfile ? <Profile token={token} /> : <ChatBox token={token} />}
        </>
      )}
    </div>
  );
}

export default App;
