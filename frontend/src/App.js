import React, { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [showOptions, setShowOptions] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const chatEndRef = useRef(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showOptions]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMsg = { sender: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setShowOptions(false);

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, user_id: "demo_user" }),
      });

      const data = await res.json();
      const botText = data.response || "Sorry, I didn’t understand that.";

      setMessages((prev) => [...prev, { sender: "bot", text: botText }]);

      // Detect if a yes/no question needs to show options
      if (
        botText.toLowerCase().includes("do you want to cancel") ||
        botText.toLowerCase().includes("do you want to confirm")
      ) {
        setShowOptions(true);
        setPendingAction(botText);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Server error. Please try again later." },
      ]);
    }
  };

  const handleOption = (choice) => {
    setMessages((prev) => [...prev, { sender: "user", text: choice }]);
    sendMessage(choice);
    setShowOptions(false);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">Trip-Assistant</div>

      <div className="chat-area">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}

        {showOptions && (
          <div className="option-buttons">
            <button onClick={() => handleOption("yes")}>Yes</button>
            <button onClick={() => handleOption("no")}>No</button>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask about your booking, flight, or policy..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
        />
        <button onClick={() => sendMessage(input)}>Send</button>
      </div>
    </div>
  );
}

export default App;
