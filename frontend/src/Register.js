import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // CSS dosyasını import et

export default function Register({ onRegister }) {
  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();

    if (!firstname || !lastname || !username || !password) {
      setError("Tüm alanlar zorunludur");
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:5000/register", {
        firstname,
        lastname,
        username,
        password,
      });

      setSuccess(res.data.message || "Kayıt başarılı!");
      setError("");
      setFirstname("");
      setLastname("");
      setUsername("");
      setPassword("");
      if (onRegister) onRegister(); 
    } catch (err) {
      setError(err.response?.data?.error || "Kayıt sırasında hata oluştu");
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleRegister} className="auth-form">
        <h2>Kayıt Ol</h2>
        {error && <p className="error-text">{error}</p>}
        {success && <p className="success-text">{success}</p>}

        <input
          type="text"
          placeholder="Ad"
          value={firstname}
          onChange={(e) => setFirstname(e.target.value)}
        />
        <input
          type="text"
          placeholder="Soyad"
          value={lastname}
          onChange={(e) => setLastname(e.target.value)}
        />
        <input
          type="text"
          placeholder="E-posta"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Şifre"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button type="submit">Kayıt Ol</button>
      </form>
    </div>
  );
}
