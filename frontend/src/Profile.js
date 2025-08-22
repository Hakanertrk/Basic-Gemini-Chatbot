import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css"; // CSS dosyasını içe aktar
import avatarImg from './avatar.jpg';

export default function Profile({ token }) {
  const [userData, setUserData] = useState({
    firstname: "",
    lastname: "",
    username: "",
    age: "",
    height: "",
    weight: "",
    chronic_diseases: ""
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [popup, setPopup] = useState(false); // Popup state

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/profile", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUserData(res.data);
      } catch (err) {
        console.error("Profil bilgileri alınamadı:", err.response?.data || err.message);
      }
    };
    fetchProfile();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage("");
    try {
      await axios.post("http://127.0.0.1:5000/profile", userData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPopup(true); // popup aç
      setTimeout(() => setPopup(false), 3000); // 3 saniye sonra kaybol
    } catch (err) {
      setMessage("⚠️ Profil güncellenemedi.");
      console.error(err.response?.data || err.message);
    }
    setLoading(false);
  };

  return (
    <div className="profile-container">
      {popup && <div className="profile-popup">Profil başarıyla kaydedildi!</div>} {/* Popup */}
      
      <div className="profile-avatar">
        <img src={avatarImg} alt="Profil Avatarı" />
      </div>
      
      <h2 className="profile-title">Profil Bilgileri</h2>
      <div className="profile-column">
        <div className="profile-field">
          <label>Ad:</label>
          <input type="text" name="firstname" value={userData.firstname} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Soyad:</label>
          <input type="text" name="lastname" value={userData.lastname} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Kullanıcı Adı / E-posta:</label>
          <input type="text" name="username" value={userData.username} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Yaş:</label>
          <input type="text" name="age" value={userData.age} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Boy (cm):</label>
          <input type="text" name="height" value={userData.height} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Kilo (kg):</label>
          <input type="text" name="weight" value={userData.weight} onChange={handleChange} />
        </div>
        <div className="profile-field">
          <label>Kronik Rahatsızlıklar:</label>
          <input type="text" name="chronic_diseases" value={userData.chronic_diseases} onChange={handleChange} />
        </div>
      </div>
      <button onClick={handleSave} disabled={loading} className="save-btn">
        {loading ? "Kaydediliyor..." : "Kaydet"}
      </button>
      {message && <p className="profile-message">{message}</p>}
    </div>
  );
}
