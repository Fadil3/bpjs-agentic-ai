import { useState, useEffect, useCallback, useRef } from "react";
import { ChatMessagesView } from "@/components/ChatMessagesView";

interface Reference {
  filename: string;
  chunks: number[];
}

interface Message {
  type: "human" | "agent";
  content: string;
  id: string;
  timestamp?: string;
  references?: Reference[];
  author?: string;
}

interface AgentTransition {
  name: string;
  badge: string;
  icon: string;
  description?: string;
}

interface ChatViewProps {
  userId: string;
  sessionId: string;
  roomId?: string | null; // Optional room ID for persistence
  onSessionChange?: (newSessionId: string) => void;
}

export function ChatView({ userId, sessionId, roomId, onSessionChange }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [activeAgent, setActiveAgent] = useState<AgentTransition | null>(null);
  const [patientLocation, setPatientLocation] = useState<string | null>(null);
  const [hasUserSentMessage, setHasUserSentMessage] = useState(false);
  
  const hasUserSentMessageRef = useRef(false);
  const locationSentRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const currentAgentRef = useRef<string | null>(null);
  const isConnectingRef = useRef(false);
  const shouldConnectRef = useRef(true);
  const connectedUserIdRef = useRef<string | null>(null);
  const connectedSessionIdRef = useRef<string | null>(null);

  // Load messages from localStorage on mount
  useEffect(() => {
    if (roomId) {
      // Try to load from backend first
      const loadFromBackend = async () => {
        try {
          const response = await fetch(`/api/chat-rooms/${roomId}/messages`);
          if (response.ok) {
            const backendMessages = await response.json();
            if (backendMessages && backendMessages.length > 0) {
              setMessages(backendMessages);
              return;
            }
          }
        } catch (error) {
          console.error("Error loading messages from backend:", error);
        }
        
        // Fallback to localStorage
        const storageKey = `chat_messages_${roomId}`;
        const savedMessages = localStorage.getItem(storageKey);
        if (savedMessages) {
          try {
            const parsed = JSON.parse(savedMessages);
            setMessages(parsed);
          } catch (e) {
            console.error("Error parsing saved messages:", e);
          }
        }
      };
      
      loadFromBackend();
    } else {
      // No roomId, try localStorage with sessionId
      const storageKey = `chat_messages_${sessionId}`;
      const savedMessages = localStorage.getItem(storageKey);
      if (savedMessages) {
        try {
          const parsed = JSON.parse(savedMessages);
          setMessages(parsed);
        } catch (e) {
          console.error("Error parsing saved messages:", e);
        }
      }
    }
  }, [roomId, sessionId]);

  // Save messages to localStorage and backend whenever messages change
  useEffect(() => {
    if (messages.length === 0) return;
    
    const storageKey = roomId ? `chat_messages_${roomId}` : `chat_messages_${sessionId}`;
    localStorage.setItem(storageKey, JSON.stringify(messages));
    
    // Also save to backend if we have a roomId
    if (roomId) {
      const saveToBackend = async () => {
        try {
          await fetch(`/api/chat-rooms/${roomId}/messages/batch`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(messages),
          });
        } catch (error) {
          console.error("Error saving messages to backend:", error);
        }
      };
      
      // Debounce backend saves to avoid too many requests
      const timeoutId = setTimeout(saveToBackend, 1000);
      return () => clearTimeout(timeoutId);
    }
  }, [messages, roomId, sessionId]);

  const extractReferences = useCallback((text: string): Reference[] => {
    const references: Reference[] = [];
    const referenceMap = new Map<string, Set<number>>();
    const pattern = /([\w\-]+\.pdf),?\s*Chunk\s*#(\d+)(?:\s*,\s*#(\d+))*/gi;

    let match;
    while ((match = pattern.exec(text)) !== null) {
      const filename = match[1];
      const chunks = [parseInt(match[2], 10)];
      if (match[3]) {
        chunks.push(parseInt(match[3], 10));
      }
      const uniqueChunks = Array.from(new Set(chunks)).sort((a, b) => a - b);
      if (!referenceMap.has(filename)) {
        referenceMap.set(filename, new Set());
      }
      uniqueChunks.forEach((chunk) => referenceMap.get(filename)!.add(chunk));
    }

    referenceMap.forEach((chunks, filename) => {
      references.push({
        filename,
        chunks: Array.from(chunks).sort((a, b) => a - b),
      });
    });

    return references;
  }, []);

  const detectAgentTransition = useCallback((text: string) => {
    const lowerText = text.toLowerCase();
    const agentPatterns = [
      {
        pattern: /interview\s+agent|wawancara|mengumpulkan\s+gejala/i,
        name: "Interview Agent",
        badge: "interview",
        icon: "interview",
        description: "Mengumpulkan gejala dari pasien",
      },
      {
        pattern: /reasoning\s+agent|penalaran|menganalisis|klasifikasi/i,
        name: "Reasoning Agent",
        badge: "reasoning",
        icon: "reasoning",
        description: "Menganalisis dan mengklasifikasikan triage level",
      },
      {
        pattern: /execution\s+agent|eksekusi|mengambil\s+tindakan/i,
        name: "Execution Agent",
        badge: "execution",
        icon: "execution",
        description: "Mengambil tindakan berdasarkan triage level",
      },
      {
        pattern: /documentation\s+agent|dokumentasi|soap/i,
        name: "Documentation Agent",
        badge: "documentation",
        icon: "documentation",
        description: "Membuat dokumentasi medis",
      },
    ];

    for (const agent of agentPatterns) {
      if (agent.pattern.test(lowerText)) {
        setActiveAgent({
          name: agent.name,
          badge: agent.badge,
          icon: agent.icon,
          description: agent.description,
        });
        currentAgentRef.current = agent.badge;
        return;
      }
    }
  }, []);

  const appendToAgentMessage = useCallback(
    (text: string, references?: Reference[], author?: string | null) => {
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        if (
          lastMessage &&
          lastMessage.type === "agent" &&
          lastMessage.id === `agent-${currentAgentRef.current}`
        ) {
          const updatedMessage = {
            ...lastMessage,
            content: lastMessage.content + text,
            references: references
              ? [...(lastMessage.references || []), ...references]
              : lastMessage.references,
          };
          
          // Save updated message to backend if we have roomId
          if (roomId) {
            // Update the last message in backend by saving all messages
            const updatedMessages = prev.slice(0, -1).concat(updatedMessage);
            fetch(`/api/chat-rooms/${roomId}/messages/batch`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(updatedMessages),
            }).catch((error) => {
              console.error("Error saving updated message to backend:", error);
            });
          }
          
          return prev.slice(0, -1).concat(updatedMessage);
        }
        
        const newMessage = {
          type: "agent" as const,
          content: text,
          id: `agent-${currentAgentRef.current || "unknown"}-${Date.now()}-${Math.random()}`,
          timestamp: new Date().toISOString(),
          references: references ? references : undefined,
          author: author || undefined,
        };
        
        // Save new message to backend if we have roomId
        if (roomId) {
          fetch(`/api/chat-rooms/${roomId}/messages`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(newMessage),
          }).catch((error) => {
            console.error("Error saving agent message to backend:", error);
          });
        }
        
        return [...prev, newMessage];
      });
    },
    [roomId]
  );

  const connect = useCallback(() => {
    // Prevent multiple connection attempts
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log("WebSocket already connecting or connected, skipping");
      return;
    }

    if (!shouldConnectRef.current) {
      console.log("Connection disabled, skipping");
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${userId}/${sessionId}`;

    console.log("Connecting to WebSocket:", wsUrl);
    isConnectingRef.current = true;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      isConnectingRef.current = false;
      setIsConnected(true);
      setIsLoading(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received event:", data);

        let textContent: string | null = null;
        if (data.text) {
          textContent = data.text;
        } else if (data.content?.parts) {
          const textParts = data.content.parts
            .filter((part: any) => part.text)
            .map((part: any) => part.text);
          if (textParts.length > 0) {
            textContent = textParts.join("");
          }
        }

        const hasFunctionCall = data.full_event?.content?.parts?.some(
          (part: any) => part.functionCall
        );
        const hasFunctionResponse = data.full_event?.content?.parts?.some(
          (part: any) => part.functionResponse
        );

        if (!textContent && !data.content && (hasFunctionCall || hasFunctionResponse)) {
          console.log("Agent delegation or tool call detected, keeping loading state");
          setIsLoading((prev) => prev ? prev : true); // Use functional update to avoid dependency
          return;
        }

        if (textContent) {
          const author = data.author || data.full_event?.author || null;
          const isThought = data.full_event?.content?.parts?.some(
            (part: any) => part.thought === true
          ) || false;

          if (isThought && author === "reasoning_agent") {
            console.log("Skipping thought message from reasoning_agent");
            return;
          }

          const isExecutionAgent = author === "execution_agent";
          const finishReason = data.full_event?.finishReason;
          const isComplete = finishReason === "STOP" || finishReason === "MAX_TOKENS";

          if (isExecutionAgent || isComplete) {
            console.log(`Text content received from ${author}, stopping loading state`);
            setIsLoading(false);
          } else {
            setIsLoading((prev) => prev ? prev : true); // Use functional update to avoid dependency
          }

          detectAgentTransition(textContent);
          const references = extractReferences(textContent);
          appendToAgentMessage(textContent, references, author);
        } else {
          const finishReason = data.full_event?.finishReason;
          if (finishReason === "STOP" || finishReason === "MAX_TOKENS") {
            console.log("Event indicates completion, stopping loading");
            setIsLoading(false);
            return;
          }

          if (hasFunctionResponse && !hasFunctionCall) {
            console.log("Tool response received, waiting for agent text response");
            setIsLoading((prev) => prev ? prev : true); // Use functional update to avoid dependency
            return;
          }

          if (hasFunctionCall) {
            setIsLoading((prev) => prev ? prev : true); // Use functional update to avoid dependency
            return;
          }
        }
      } catch (e) {
        console.error("Error parsing event:", e);
        setIsLoading(false);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      isConnectingRef.current = false;
      setIsConnected(false);
      setIsLoading(false);
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed", event.code, event.reason);
      isConnectingRef.current = false;
      setIsConnected(false);
      setIsLoading(false);
      // Don't try to reconnect if it was a normal closure or if component is unmounting
      if (event.code !== 1000 && event.code !== 1001 && shouldConnectRef.current) {
        // Abnormal closure, might want to reconnect after a delay
        console.log("WebSocket closed abnormally, code:", event.code);
      }
    };
  }, [userId, sessionId, detectAgentTransition, extractReferences, appendToAgentMessage]); // Removed isLoading - it's only read, not used in closure

  useEffect(() => {
    // Only connect if userId or sessionId changed, or if we don't have a connection
    const needsReconnect = 
      userId && 
      sessionId && 
      shouldConnectRef.current &&
      (connectedUserIdRef.current !== userId || connectedSessionIdRef.current !== sessionId);
    
    if (needsReconnect) {
      // Close existing connection if userId or sessionId changed
      if (wsRef.current && (connectedUserIdRef.current !== userId || connectedSessionIdRef.current !== sessionId)) {
        try {
          if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
            wsRef.current.close(1000, "Switching session");
          }
        } catch (e) {
          // Ignore errors
        }
        wsRef.current = null;
        isConnectingRef.current = false;
      }
      
      connectedUserIdRef.current = userId;
      connectedSessionIdRef.current = sessionId;
      connect();
    }
    
    return () => {
      // Only close on actual unmount (when userId/sessionId become null/undefined)
      if (!userId || !sessionId) {
        shouldConnectRef.current = false;
        if (wsRef.current) {
          try {
            if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
              wsRef.current.close(1000, "Component unmounting");
            }
          } catch (e) {
            // Ignore errors when closing
          }
          wsRef.current = null;
        }
        isConnectingRef.current = false;
        connectedUserIdRef.current = null;
        connectedSessionIdRef.current = null;
      }
    };
  }, [userId, sessionId]); // Removed 'connect' from dependencies to prevent unnecessary re-renders

  const handleSubmit = useCallback(
    (
      query: string,
      attachments?: {
        type: "image" | "audio";
        data: string;
        mimeType: string;
      }[]
    ) => {
      if (!query.trim() && (!attachments || attachments.length === 0)) return;
      if (isLoading || !isConnected) return;

      if (!hasUserSentMessageRef.current) {
        setHasUserSentMessage(true);
        hasUserSentMessageRef.current = true;
      }

      setMessages((prev) => [
        ...prev,
        {
          type: "human",
          content: query || "Mengirim lampiran",
          id: `msg-${Date.now()}-${Math.random()}`,
          timestamp: new Date().toISOString(),
        },
      ]);

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const message: any = {
          type: "text",
          content: query || "",
        };

        if (attachments && attachments.length > 0) {
          message.attachments = attachments.map((att) => ({
            type: att.type,
            data: att.data,
            mimeType: att.mimeType,
          }));
        }

        if (patientLocation && !locationSentRef.current) {
          message.location = patientLocation;
          locationSentRef.current = true;
        }

        wsRef.current.send(JSON.stringify(message));
        setIsLoading(true);
      }
    },
    [isConnected, isLoading, patientLocation]
  );

  const handleLocationUpdate = useCallback((location: string) => {
    if (patientLocation === location) return;
    setPatientLocation(location);
  }, [patientLocation]);

  const handleClear = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear localStorage
    const storageKey = roomId ? `chat_messages_${roomId}` : `chat_messages_${sessionId}`;
    localStorage.removeItem(storageKey);

    setMessages([]);
    currentAgentRef.current = null;
    setActiveAgent(null);
    locationSentRef.current = false;
    setHasUserSentMessage(false);
    hasUserSentMessageRef.current = false;
    setPatientLocation(null);
    setIsLoading(false);
    setIsConnected(false);

    const newSessionId = `session_${Date.now()}`;
    if (onSessionChange) {
      onSessionChange(newSessionId);
    }
  };

  return (
    <ChatMessagesView
      messages={messages}
      isLoading={isLoading}
      onSubmit={handleSubmit}
      onClear={handleClear}
      activeAgent={activeAgent}
      isConnected={isConnected}
      onLocationUpdate={handleLocationUpdate}
      hasUserSentMessage={hasUserSentMessage}
    />
  );
}

