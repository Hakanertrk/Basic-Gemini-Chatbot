import React, { useState } from "react";
import axios from "axios";

export default function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!username || !password) {
      setError("Kullanıcı adı ve şifre boş olamaz");
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:5000/login", { username, password });
      localStorage.setItem("token", res.data.token);
      setToken(res.data.token);
    } catch (err) {
      setError(err.response?.data?.error || "Hata oluştu");
    }
  };

  return (
    <div className="auth-form">
      {error && <p style={{ color: "red" }}>{error}</p>}

      <input
        type="text"
        placeholder="E-posta"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Şifre"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />

      <button onClick={handleLogin}>Giriş Yap</button>
    </div>
  );
}
