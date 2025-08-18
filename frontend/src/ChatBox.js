import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import Message from "./Message";

export default function ChatBox({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false); // Bot cevabı bekleniyor mu
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return; // Eğer bot cevabı bekleniyorsa mesaj gönderme

    const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true); // Mesaj gönderildi, bot cevabı bekleniyor

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
    } finally {
      setLoading(false); // Bot cevabı geldikten sonra tekrar mesaj gönderilebilir
    }
  };

  return (
    <div className="chatbox">
      <div className="messages">
        {messages.map((m, i) => (
          <Message key={i} sender={m.sender} text={m.text} />
        ))}
        {loading && (
          <div className="typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={loading ? "Bot cevap veriyor..." : "Bir şey sor..."}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          disabled={loading} // Bot cevap verirken input devre dışı
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "Bekleyin..." : "Gönder"}
        </button>
      </div>
    </div>
  );
}
