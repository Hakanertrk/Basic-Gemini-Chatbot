import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import Message from "./Message";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Mesajlar değiştiğinde scroll en alta
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Kullanıcı mesajını ekle
    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Backend'e istek gönderiyoruz
      const res = await axios.post("http://127.0.0.1:5000/chat", {
        message: input
      });

      // Backend cevabı
      const botMsg = { sender: "bot", text: res.data.reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Backend Hatası:", error.response ? error.response.data : error.message);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Bir hata oluştu." }
      ]);
    }

    setLoading(false);
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

        {/* Scroll için boş div */}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Bir şey sor..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Gönder</button>
      </div>
    </div>
  );
}
