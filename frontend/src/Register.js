import React, { useState } from "react";
import axios from "axios";

export default function Register({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async () => {
    setError("");
    setSuccess("");
    if (!username || !password) {
      setError("Kullanıcı adı ve şifre boş olamaz");
      return;
    }

    try {
      await axios.post("http://127.0.0.1:5000/register", { username, password });
      setSuccess("Kayıt başarılı! Giriş yapabilirsiniz.");
      setUsername("");
      setPassword("");
    } catch (err) {
      setError(err.response?.data?.error || "Kayıt sırasında hata oluştu");
    }
  };

  return (
    <div>
      <input
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button onClick={handleRegister}>Kayıt Ol</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {success && <p style={{ color: "green" }}>{success}</p>}
    </div>
  );
}
