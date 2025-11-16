import { useState, useEffect } from "react";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Badge } from "@/components/ui/badge";
import { Lock } from "lucide-react";

interface Message {
  type: "human" | "agent";
  content: string;
  id: string;
  timestamp?: string;
  references?: any[];
  author?: string;
}

interface ArchivedChatViewProps {
  roomId: string | null;
  userId: string;
  sessionId: string;
}

export function ArchivedChatView({
  roomId,
  userId,
  sessionId,
}: ArchivedChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (roomId) {
      loadMessages();
    }
  }, [roomId]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/chat-rooms/${roomId}/messages`);
      if (response.ok) {
        const roomMessages = await response.json();
        setMessages(roomMessages || []);
      }
    } catch (error) {
      console.error("Error loading archived messages:", error);
    } finally {
      setLoading(false);
    }
  };

  // Read-only: don't allow submitting new messages
  const handleSubmit = () => {
    // Do nothing - chat is archived/read-only
  };

  return (
    <div className="h-full flex flex-col">
      {/* Read-only indicator */}
      <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2">
        <div className="flex items-center gap-2 max-w-6xl mx-auto">
          <Lock className="h-4 w-4 text-yellow-600" />
          <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-300">
            Chat Terarsip - Hanya Baca
          </Badge>
          <span className="text-sm text-yellow-700">
            Chat ini sudah selesai dan tidak dapat menerima pesan baru
          </span>
        </div>
      </div>

      {/* Chat Messages - Read-only */}
      <ChatMessagesView
        messages={messages}
        isLoading={loading}
        onSubmit={handleSubmit}
        onClear={() => {}}
        activeAgent={null}
        isConnected={false}
        onLocationUpdate={() => {}}
        hasUserSentMessage={true}
        isReadOnly={true}
      />
    </div>
  );
}

