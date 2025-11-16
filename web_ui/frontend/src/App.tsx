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
  author?: string; // Track which agent sent this message
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
  const [patientLocation, setPatientLocation] = useState<string | null>(null);
  const [hasUserSentMessage, setHasUserSentMessage] = useState(false);
  const hasUserSentMessageRef = useRef(false);
  const locationSentRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const userIdRef = useRef(`user_${Date.now()}`);
  const sessionIdRef = useRef(`session_${Date.now()}`);
  const currentAgentRef = useRef<string | null>(null);

  const extractReferences = useCallback((text: string): Reference[] => {
    const references: Reference[] = [];
    const referenceMap = new Map<string, Set<number>>();

    // Pattern untuk mendeteksi referensi: "filename.pdf, Chunk #X, #Y" atau "filename.pdf, Chunk #X"
    // Format yang didukung:
    // - "filename.pdf, Chunk #42, #43"
    // - "filename.pdf, Chunk #616"
    // - "filename.pdf (Chunk #X)"
    // - "filename.pdf, Chunk #4, #6"
    const pattern = /([\w\-]+\.pdf),?\s*Chunk\s*#(\d+)(?:\s*,\s*#(\d+))*/gi;

    let match;
    while ((match = pattern.exec(text)) !== null) {
      const filename = match[1];
      const startIndex = match.index;
      const matchLength = match[0].length;

      // Ambil chunk pertama
      const chunks = [parseInt(match[2], 10)];

      // Jika ada chunk kedua dalam match
      if (match[3]) {
        chunks.push(parseInt(match[3], 10));
      }

      // Cari semua chunk tambahan setelah match (format: ", #X, #Y")
      const afterMatch = text.substring(startIndex + matchLength);
      const additionalChunks = afterMatch.match(/#(\d+)/g);
      if (additionalChunks) {
        additionalChunks.forEach((chunk) => {
          const chunkNum = parseInt(chunk.replace("#", ""), 10);
          if (!chunks.includes(chunkNum)) {
            chunks.push(chunkNum);
          }
        });
      }

      // Hapus duplikat dan sort
      const uniqueChunks = Array.from(new Set(chunks)).sort((a, b) => a - b);

      if (!referenceMap.has(filename)) {
        referenceMap.set(filename, new Set());
      }
      uniqueChunks.forEach((chunk) => referenceMap.get(filename)!.add(chunk));
    }

    // Convert map to array
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

  const appendToAgentMessage = useCallback(
    (text: string, references?: Reference[], author?: string | null) => {
      if (!text || text.trim() === "") {
        return; // Skip empty text
      }

      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        // Only append to last message if:
        // 1. It's from an agent
        // 2. It's from the same author (same agent)
        // 3. The text is not a duplicate
        if (
          lastMessage &&
          lastMessage.type === "agent" &&
          lastMessage.author === author
        ) {
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

          // Append new text to last message and merge references
          return prev.map((msg, idx) => {
            if (idx === prev.length - 1) {
              const existingRefs = msg.references || [];
              const newRefs = references || [];
              // Merge references: combine chunks for same filename
              const mergedRefs = [...existingRefs, ...newRefs].reduce(
                (acc, ref) => {
                  const existing = acc.find((r) => r.filename === ref.filename);
                  if (existing) {
                    existing.chunks = [
                      ...new Set([...existing.chunks, ...ref.chunks]),
                    ].sort((a, b) => a - b);
                  } else {
                    acc.push({ ...ref });
                  }
                  return acc;
                },
                [] as Reference[]
              );
              return {
                ...msg,
                content: msg.content + text,
                references: mergedRefs.length > 0 ? mergedRefs : undefined,
              };
            }
            return msg;
          });
        } else {
          // Create new agent message (different agent or first agent message)
          return [
            ...prev,
            {
              type: "agent" as const,
              content: text,
              id: `agent_${Date.now()}_${author || "unknown"}`,
              timestamp: new Date().toISOString(),
              author: author || undefined,
              references:
                references && references.length > 0 ? references : undefined,
            },
          ];
        }
      });
    },
    []
  );

  // Removed sendLocationToBackend - location is now sent with first user message

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
      // Location will be sent with first user message, not here
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received event:", data);

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

        // Check if this is a delegation event (functionCall) with no text content
        const hasFunctionCall = data.full_event?.content?.parts?.some(
          (part: any) => part.functionCall
        );

        // If content and text are both null, but there's a functionCall, keep loading
        // This happens during agent delegation (e.g., root_agent calling interview_agent)
        if (!textContent && !data.content && hasFunctionCall) {
          console.log("Agent delegation detected, keeping loading state");
          // Keep loading state true - don't set it to false
          return;
        }

        // If we have text content, process it and stop loading
        if (textContent) {
          setIsLoading(false);

          // IMPORTANT: Don't process agent messages if user hasn't sent any message yet
          // This prevents agent from sending messages automatically (e.g., after location detection)
          // Use ref to get the latest value (closure issue)
          if (!hasUserSentMessageRef.current) {
            console.log(
              "Ignoring agent message - user hasn't sent any message yet"
            );
            return;
          }

          // Detect agent transitions
          detectAgentTransition(textContent);
          // Extract references from text
          const references = extractReferences(textContent);
          // Get author from event
          const author = data.author || data.full_event?.author || null;
          // Append to message (deduplication handled in appendToAgentMessage)
          appendToAgentMessage(textContent, references, author);
        } else {
          // No text content and no function call - might be completion or error
          // Check if event indicates completion
          const finishReason = data.full_event?.finishReason;
          if (finishReason === "STOP" || finishReason === "MAX_TOKENS") {
            console.log("Event indicates completion, stopping loading");
            setIsLoading(false);
          }
          // Otherwise, keep loading if we're already in loading state
        }
      } catch (e) {
        console.error("Error parsing event:", e);
        setIsLoading(false);
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
  }, [
    detectAgentTransition,
    appendToAgentMessage,
    extractReferences,
    patientLocation,
  ]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const handleSubmit = useCallback(
    (
      query: string,
      attachments?: {
        type: "image" | "audio";
        data: string;
        mimeType: string;
      }[]
    ) => {
      const hasContent =
        query.trim() || (attachments && attachments.length > 0);
      if (!hasContent || !isConnected || isLoading) return;

      // Add user message
      const userMessage: Message = {
        type: "human",
        content:
          query ||
          (attachments && attachments.length > 0 ? "Mengirim lampiran" : ""),
        id: `user_${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setHasUserSentMessage(true); // Mark that user has sent a message
      hasUserSentMessageRef.current = true; // Update ref immediately

      // Don't create empty agent message placeholder - it will be created when first content arrives
      setIsLoading(true);

      // Send message via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const message: any = {
          type: "text",
          content: query || "",
        };

        // Add attachments if present
        if (attachments && attachments.length > 0) {
          message.attachments = attachments.map((att) => ({
            type: att.type,
            data: att.data,
            mimeType: att.mimeType,
          }));
        }

        // Send location with first message if available and not yet sent
        if (patientLocation && !locationSentRef.current) {
          message.location = patientLocation;
          locationSentRef.current = true;
          console.log("Sending location with first message:", patientLocation);
        } else if (!patientLocation) {
          console.log("No location available to send with first message");
        }

        wsRef.current.send(JSON.stringify(message));
      }
    },
    [isConnected, isLoading, patientLocation]
  );

  const handleLocationUpdate = useCallback(
    (location: string) => {
      // Only update if location actually changed
      if (patientLocation === location) {
        return; // Skip if location hasn't changed
      }

      setPatientLocation(location);
      // Don't send to backend here - location will be sent with first user message
    },
    [patientLocation]
  );

  // Note: Location is now sent via handleLocationUpdate, not via useEffect
  // This prevents duplicate sends

  const handleClear = () => {
    setMessages([]);
    currentAgentRef.current = null;
    setActiveAgent(null);
    locationSentRef.current = false;
    setHasUserSentMessage(false); // Reset flag when clearing chat
    hasUserSentMessageRef.current = false; // Reset ref when clearing chat
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
        onLocationUpdate={handleLocationUpdate}
        hasUserSentMessage={hasUserSentMessage}
      />
    </div>
  );
}

export default App;
