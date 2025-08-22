import React, { useState, useEffect } from "react";
import ChatBox from "./ChatBox";
import Login from "./Login";
import Register from "./Register";
import Profile from "./Profile";
import "./App.css";
import axios from "axios";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [showRegister, setShowRegister] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const [appointments, setAppointments] = useState([]);
  const [newAppt, setNewAppt] = useState("");

  // Kullanıcı çıkış yaptığında profil ekranı sıfırlansın
  useEffect(() => {
    if (!token) {
      setShowProfile(false);
    }
  }, [token]);

  // Ekran belirleme
  let screen = "login";
  if (token) {
    screen = showProfile ? "profile" : "chat";
  }

  // Randevu listesini backend’den çek
  useEffect(() => {
    if (token && screen === "chat") {
      const fetchAppointments = async () => {
        try {
          const res = await axios.get("http://127.0.0.1:5000/appointments", {
            headers: { Authorization: `Bearer ${token}` },
          });
          setAppointments(res.data);
        } catch (err) {
          console.error("Randevu çekme hatası:", err.response?.data || err.message);
        }
      };
      fetchAppointments();
    }
  }, [token, screen]);

  const addAppointment = async () => {
    if (!newAppt.trim()) return;

    try {
      const res = await axios.post(
        "http://127.0.0.1:5000/appointments",
        { title: newAppt, datetime: newAppt },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setAppointments((prev) => [...prev, { id: res.data.id, title: newAppt, datetime: newAppt }]);
      setNewAppt("");
    } catch (err) {
      console.error("Randevu ekleme hatası:", err.response?.data || err.message);
    }
  };

  const deleteAppointment = async (id) => {
    try {
      await axios.delete(`http://127.0.0.1:5000/appointments/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAppointments((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error("Randevu silme hatası:", err.response?.data || err.message);
    }
  };

  return (
    <div className="app">
      <h1 className={`app-title ${screen === "login" ? "center-title" : "top-left-title"}`}>
        CHATDOC 🩺
      </h1>
      {screen === "login" && <h2 className="app-subtitle">Sağlığınız için AI.</h2>}

      {/* ---------------- Login/Register ekranı ---------------- */}
      {screen === "login" && (
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
      )}

      {/* ---------------- Chat ve Profil ekranı ---------------- */}
      {screen !== "login" && (
        <>
          <div className="top-right-menu">
            <button onClick={() => setShowProfile(!showProfile)}>
              {showProfile ? "Chat" : "Profil"}
            </button>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                setToken("");
              }}
            >
              Çıkış Yap
            </button>
          </div>

          {showProfile ? (
            <Profile token={token} />
          ) : (
            <div className="app-container">
              {/* Randevu Paneli */}
              <div className="appointment-panel">
                <h3>📅 Randevular</h3>
                <ul className="appt-list">
                  {appointments.map((a) => (
                    <li key={a.id} className="appt-item">
                      {new Date(a.datetime).toLocaleString()}
                      <button
                        onClick={() => deleteAppointment(a.id)}
                        className="appt-delete-button"
                      >
                        Sil
                      </button>
                    </li>
                  ))}
                </ul>
                <input
                  type="datetime-local"
                  value={newAppt}
                  onChange={(e) => setNewAppt(e.target.value)}
                  className="appt-input"
                />
                <button onClick={addAppointment} className="appt-button">
                  Ekle
                </button>
              </div>

              {/* ChatBox */}
              <ChatBox token={token} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
