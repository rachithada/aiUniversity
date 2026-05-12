import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const startVoiceInput = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    setListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setMessage(transcript);
    };

    recognition.onend = () => {
      setListening(false);
    };
  };

  const uploadPDF = async (e) => {
    const file = e.target.files[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    await fetch("http://127.0.0.1:8000/upload-pdf", {
      method: "POST",
      body: formData,
    });

    alert("PDF uploaded successfully");
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = {
      text: message,
      sender: "user",
    };

    setMessages((prev) => [...prev, userMessage]);

    const currentMessage = message;
    setMessage("");
    setLoading(true);

    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: currentMessage,
      }),
    });

    const data = await res.json();

    const botMessage = {
      text: data.response,
      sender: "bot",
    };

    setMessages((prev) => [...prev, botMessage]);
    setLoading(false);
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem("chat_messages");
  };

  return (
    <div className="app">
      <div className="chat-container">
        <h1>AI University Assistant</h1>

        <button className="clear-btn" onClick={clearChat}>
          Clear Chat
        </button>

        <div className="upload-area">
          <input type="file" accept=".pdf" onChange={uploadPDF} />
        </div>

        {listening && (
          <div
            style={{
              textAlign: "center",
              padding: "8px",
              color: "red",
              fontWeight: "bold",
            }}
          >
            Listening...
          </div>
        )}

        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {msg.sender === "bot" ? (
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              ) : (
                msg.text
              )}
            </div>
          ))}

          {loading && <div className="message bot">Thinking...</div>}

          <div ref={chatEndRef}></div>
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder="Ask something..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
          />

          <button onClick={startVoiceInput}>🎤</button>

          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;