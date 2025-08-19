import React, { useState } from "react";
import axios from "axios";

export default function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault(); // sayfanın reload olmasını engeller
    setError("");
    setLoading(true);

    if (!username || !password) {
      setError("Kullanıcı adı ve şifre boş olamaz");
      setLoading(false);
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:5000/login", { username, password });
      localStorage.setItem("token", res.data.token);
      setToken(res.data.token);
    } catch (err) {
      setError(err.response?.data?.error || "Hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleLogin}>
      <h2>Giriş yap</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}

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

      <button type="submit" disabled={loading}>
        {loading ? "Giriş Yapılıyor..." : "Giriş Yap"}
      </button>
    </form>
  );
}
