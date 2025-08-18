import React, { useState } from "react";
import axios from "axios";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault(); // Sayfa reload engelle
    setError("");
    setSuccess("");

    if (!username || !password) {
      setError("Tüm alanlar zorunludur");
      return;
    }

    try {
      const payload = { username, password };
      console.log("Gönderilen veri:", payload);

      await axios.post("http://127.0.0.1:5000/register", payload);

      setSuccess("Kayıt başarılı! Giriş yapabilirsiniz.");
      setUsername("");
      setPassword("");
    } catch (err) {
      console.log(err.response?.data);
      setError(err.response?.data?.error || "Kayıt sırasında hata oluştu");
    }
  };

  return (
    <form className="auth-form" onSubmit={handleRegister}>
      <input
        type="text"
        placeholder="Username"
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
      {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}
      {success && <p style={{ color: "green", marginTop: "10px" }}>{success}</p>}
    </form>
  );
}
