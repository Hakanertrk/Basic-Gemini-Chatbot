import React, { use, useState } from "react";
import axios from "axios";

export default function Register() {

  const [email, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault(); // Sayfa reload engelle
    setError("");
    setSuccess("");

    if ( !email || !password) {
      setError("Tüm alanlar zorunludur");
      return;
    }

    try {
      const payload = {
      
        username: email, // Backend'de username olarak email kullanılıyor
        password
      };

      console.log("Gönderilen veri:", payload); // Test için backend'e ne gidecek bak

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
    <form onSubmit={handleRegister}>
      
      <input
        type="username"
        placeholder="Username"
        value={email}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Şifre"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button type="submit">Kayıt Ol</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {success && <p style={{ color: "green" }}>{success}</p>}
    </form>
  );
}
