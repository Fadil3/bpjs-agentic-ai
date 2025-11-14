import { useState, useEffect, useCallback, useRef } from "react";
import { ChatMessagesView } from "@/components/ChatMessagesView";

interface Message {
  type: "human" | "agent";
  content: string;
  id: string;
  timestamp?: string;
}

interface AgentTransition {
  name: string;
  badge: string;
  icon: string;
  description?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [activeAgent, setActiveAgent] = useState<AgentTransition | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const userIdRef = useRef(`user_${Date.now()}`);
  const sessionIdRef = useRef(`session_${Date.now()}`);
  const currentAgentRef = useRef<string | null>(null);

  const detectAgentTransition = useCallback((text: string) => {
    const lowerText = text.toLowerCase();
    const agentPatterns = [
      {
        pattern: /interview\s+agent|wawancara|mengumpulkan\s+informasi/i,
        name: "Interview Agent",
        badge: "interview",
        icon: "💬",
      },
      {
        pattern: /reasoning\s+agent|penalaran\s+klinis|menganalisis\s+gejala/i,
        name: "Reasoning Agent",
        badge: "reasoning",
        icon: "🧠",
      },
      {
        pattern: /execution\s+agent|eksekusi|mengambil\s+tindakan/i,
        name: "Execution Agent",
        badge: "execution",
        icon: "⚡",
      },
      {
        pattern: /documentation\s+agent|dokumentasi|soap/i,
        name: "Documentation Agent",
        badge: "documentation",
        icon: "📋",
      },
    ];

    for (const agent of agentPatterns) {
      if (
        agent.pattern.test(lowerText) &&
        currentAgentRef.current !== agent.name
      ) {
        currentAgentRef.current = agent.name;
        setActiveAgent(agent);
        setTimeout(() => setActiveAgent(null), 5000);
        break;
      }
    }
  }, []);

  const appendToAgentMessage = useCallback((text: string) => {
    if (!text || text.trim() === "") {
      return; // Skip empty text
    }

    setMessages((prev) => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage && lastMessage.type === "agent") {
        const lastContent = lastMessage.content.trim();
        const newText = text.trim();

        // 1. Exact match at the end - skip
        if (lastContent.endsWith(newText)) {
          console.log("Skipping duplicate: exact match at end");
          return prev;
        }

        // 2. Check if new text is already contained in last message (substring)
        if (lastContent.includes(newText) && newText.length > 15) {
          // Check position - if it's near the end, it's likely a duplicate
          const lastIndex = lastContent.lastIndexOf(newText);
          const distanceFromEnd =
            lastContent.length - lastIndex - newText.length;
          if (distanceFromEnd < 100) {
            console.log("Skipping duplicate: substring near end");
            return prev;
          }
        }

        // 3. Check if new text starts with content that's already in last message
        // This catches cases where agent sends "Baik, saya mengerti..." multiple times
        const newTextWords = newText.split(/\s+/).slice(0, 10).join(" "); // First 10 words
        if (newTextWords.length > 30 && lastContent.includes(newTextWords)) {
          const lastIndex = lastContent.lastIndexOf(newTextWords);
          const distanceFromEnd =
            lastContent.length - lastIndex - newTextWords.length;
          if (distanceFromEnd < 200) {
            console.log("Skipping duplicate: similar opening phrase");
            return prev;
          }
        }

        // 4. Check for high similarity (fuzzy match) - if >80% similar, likely duplicate
        if (newText.length > 30 && lastContent.length > 30) {
          const windowSize = 200;
          const lastWindow = lastContent.slice(
            -Math.min(windowSize, lastContent.length)
          );
          const newWindow = newText.slice(
            0,
            Math.min(windowSize, newText.length)
          );

          const words1 = new Set(lastWindow.toLowerCase().split(/\s+/));
          const words2 = new Set(newWindow.toLowerCase().split(/\s+/));
          const intersection = new Set(
            [...words1].filter((x) => words2.has(x))
          );
          const union = new Set([...words1, ...words2]);
          const similarity =
            union.size > 0 ? intersection.size / union.size : 0;
          if (similarity > 0.8) {
            console.log(
              `Skipping duplicate: high similarity (${(
                similarity * 100
              ).toFixed(0)}%)`
            );
            return prev;
          }
        }

        // Append new text to last message
        return prev.map((msg, idx) =>
          idx === prev.length - 1
            ? { ...msg, content: msg.content + text }
            : msg
        );
      } else {
        // Create new agent message
        return [
          ...prev,
          {
            type: "agent" as const,
            content: text,
            id: `agent_${Date.now()}`,
            timestamp: new Date().toISOString(),
          },
        ];
      }
    });
  }, []);

  const connect = useCallback(() => {
    // Determine WebSocket URL based on environment
    // In dev mode (Vite), use proxy. In production, use same host
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${userIdRef.current}/${sessionIdRef.current}`;

    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      setIsLoading(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received event:", data);

        setIsLoading(false);

        // Extract text content - prioritize data.text, fallback to data.content.parts
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

        // Only process if we have text content
        if (textContent) {
          // Detect agent transitions
          detectAgentTransition(textContent);
          // Append to message (deduplication handled in appendToAgentMessage)
          appendToAgentMessage(textContent);
        }
      } catch (e) {
        console.error("Error parsing event:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
      setIsLoading(false);
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed", event.code, event.reason);
      setIsConnected(false);
      setIsLoading(false);

      // Only reconnect if it wasn't a normal closure
      if (event.code !== 1000) {
        console.log("Reconnecting in 3 seconds...");
        setTimeout(() => connect(), 3000);
      }
    };
  }, [detectAgentTransition, appendToAgentMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const handleSubmit = useCallback(
    (query: string) => {
      if (!query.trim() || !isConnected || isLoading) return;

      // Add user message
      const userMessage: Message = {
        type: "human",
        content: query,
        id: `user_${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Create agent message placeholder
      const agentMessage: Message = {
        type: "agent",
        content: "",
        id: `agent_${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, agentMessage]);

      setIsLoading(true);

      // Send message via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "text",
            content: query,
          })
        );
      }
    },
    [isConnected, isLoading]
  );

  const handleClear = () => {
    setMessages([]);
    currentAgentRef.current = null;
    setActiveAgent(null);
  };

  return (
    <div className="h-screen w-screen overflow-hidden">
      <ChatMessagesView
        messages={messages}
        isLoading={isLoading}
        onSubmit={handleSubmit}
        onClear={handleClear}
        activeAgent={activeAgent}
        isConnected={isConnected}
      />
    </div>
  );
}

export default App;
