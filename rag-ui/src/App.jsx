import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import "./App.css";

function App() {
  const [conversationId, setConversationId] = useState(null);

  return (
    <div className="layout">
      <Sidebar onSelect={setConversationId} activeId={conversationId} />
      <Chat
        conversationId={conversationId}
        onMessageSent={setConversationId}
      />
    </div>
  );
}

export default App;
