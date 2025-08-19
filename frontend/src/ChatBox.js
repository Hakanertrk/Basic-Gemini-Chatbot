import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import Message from "./Message";

export default function ChatBox({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // -----------------------
  // Sayfa yüklendiğinde mesaj geçmişini çek
  // -----------------------
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/history", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMessages(res.data); // Backend'den gelen geçmiş
      } catch (err) {
        console.error("Mesaj geçmişi alınamadı:", err.response?.data || err.message);
      }
    };

    fetchHistory();
  }, [token]);

  // -----------------------
  // Mesaj scroll
  // -----------------------
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  // -----------------------
  // Mesaj gönderme
  // -----------------------
  const sendMessage = async () => {
    if (!input.trim() || loading) return; // Bot cevaplamadan yeni mesaj engelle

    const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(
        "http://127.0.0.1:5000/chat",
        { message: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const botMsg = { sender: "bot", text: res.data.reply };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error("Backend Hatası:", error.response?.data || error.message);
      setMessages(prev => [...prev, { sender: "bot", text: "⚠️ Bir hata oluştu." }]);
    }
    setLoading(false);
  };

  return (
    <div className="chatbox">
      <div className="messages">
        {messages.map((m, i) => (
          <Message key={i} sender={m.sender} text={m.text} />
        ))}
        {loading && <div className="typing"><span></span><span></span><span></span></div>}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Bir şey sor..."
          onKeyDown={e => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage} disabled={loading}>
          Gönder
        </button>
      </div>
    </div>
  );
}
