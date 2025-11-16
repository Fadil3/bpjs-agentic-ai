import { useState, useEffect } from "react";
import { ChatView } from "@/components/ChatView";
import { ArchivedChatView } from "@/components/ArchivedChatView";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Plus } from "lucide-react";

interface ChatRoom {
  id: string;
  sessionId: string;
  userId: string;
  createdAt: string;
  lastMessageAt: string;
  title: string;
  patientName?: string;
  isArchived?: boolean; // If true, chat is read-only
}

export function PatientPage() {
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [showRoomList, setShowRoomList] = useState(true);
  const [userId] = useState(`user_001`); // Use seeded user ID
  const [sessionId, setSessionId] = useState(`session_${Date.now()}`);
  const [isArchived, setIsArchived] = useState(false);

  // Load chat rooms from backend
  useEffect(() => {
    loadChatRooms();
  }, []);

  const loadChatRooms = async () => {
    try {
      const response = await fetch(`/api/chat-rooms?userId=${userId}`);
      if (response.ok) {
        const rooms = await response.json();
        setChatRooms(rooms);
      }
    } catch (error) {
      console.error("Error loading chat rooms:", error);
    }
  };

  // Load messages for selected room
  const loadRoomMessages = async (roomId: string) => {
    try {
      const room = chatRooms.find((r) => r.id === roomId);
      if (room) {
        setSessionId(room.sessionId);
        setSelectedRoomId(roomId);
        setShowRoomList(false);
        setIsArchived(room.isArchived || false);
      }
    } catch (error) {
      console.error("Error loading room messages:", error);
    }
  };

  // Create new chat room
  const createNewRoom = async () => {
    try {
      const response = await fetch(`/api/chat-rooms?userId=${userId}`, {
        method: "POST",
      });
      if (response.ok) {
        const room = await response.json();
        setSessionId(room.sessionId);
        setSelectedRoomId(room.id);
        setIsArchived(false); // New rooms are not archived
        setShowRoomList(false);
        loadChatRooms(); // Refresh room list
      }
    } catch (error) {
      console.error("Error creating chat room:", error);
    }
  };

  const handleSessionChange = (newSessionId: string) => {
    setSessionId(newSessionId);
  };

  // Show room list or chat interface
  if (showRoomList) {
    return (
      <div className="h-screen w-screen bg-gray-50 flex">
        {/* Sidebar - Chat Rooms */}
        <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Riwayat Chat</h2>
              <Button
                onClick={createNewRoom}
                size="sm"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Chat Baru
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-2">
              {chatRooms.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Belum ada riwayat chat</p>
                  <p className="text-sm">Klik "Chat Baru" untuk memulai</p>
                </div>
              ) : (
                chatRooms.map((room) => (
                  <Card
                    key={room.id}
                    className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedRoomId === room.id ? "bg-blue-50 border-blue-300" : ""
                    }`}
                    onClick={() => loadRoomMessages(room.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-sm truncate">
                            {room.title || "Konsultasi Medis"}
                          </h3>
                          {room.isArchived && (
                            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                              Terarsip
                            </span>
                          )}
                        </div>
                        {room.patientName && (
                          <p className="text-xs text-gray-500 mt-1">
                            Pasien: {room.patientName}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(room.lastMessageAt).toLocaleDateString("id-ID", {
                            day: "numeric",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Main Content - Empty State */}
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-semibold mb-2">Pilih Chat atau Buat Baru</h3>
            <p className="text-gray-500 mb-4">
              Pilih chat dari riwayat atau buat chat baru untuk konsultasi
            </p>
            <Button onClick={createNewRoom} className="flex items-center gap-2 mx-auto">
              <Plus className="h-4 w-4" />
              Mulai Chat Baru
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Show chat interface
  return (
    <div className="h-screen w-screen overflow-hidden">
      <div className="h-full flex">
        {/* Sidebar - Chat Rooms (Collapsible) */}
        <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Riwayat Chat</h2>
              <Button
                onClick={createNewRoom}
                size="sm"
                variant="outline"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Baru
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-2">
              {chatRooms.map((room) => (
                <Card
                  key={room.id}
                  className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedRoomId === room.id ? "bg-blue-50 border-blue-300" : ""
                  }`}
                  onClick={() => loadRoomMessages(room.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-sm truncate">
                          {room.title || "Konsultasi Medis"}
                        </h3>
                        {room.isArchived && (
                          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                            Terarsip
                          </span>
                        )}
                      </div>
                      {room.patientName && (
                        <p className="text-xs text-gray-500 mt-1">
                          Pasien: {room.patientName}
                        </p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(room.lastMessageAt).toLocaleDateString("id-ID", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Chat Interface */}
        <div className="flex-1">
          {isArchived ? (
            <ArchivedChatView
              roomId={selectedRoomId}
              userId={userId}
              sessionId={sessionId}
            />
          ) : (
            <ChatView
              userId={userId}
              sessionId={sessionId}
              roomId={selectedRoomId}
              onSessionChange={handleSessionChange}
            />
          )}
        </div>
      </div>
    </div>
  );
}
