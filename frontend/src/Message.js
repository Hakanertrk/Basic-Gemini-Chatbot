import React from "react";

export default function Message({ sender, text, type }) {
  // Farklı mesaj tiplerine göre class ekleyebiliriz
  const classes = `message ${sender} ${type || ""}`;

  return (
    <div className={classes}>
      {Array.isArray(text) ? (
        text.map((t, i) => <p key={i}>{t}</p>)  // Eğer bot çok parçalı cevap yollarsa liste gibi bas
      ) : (
        text
      )}
    </div>
  );
}
