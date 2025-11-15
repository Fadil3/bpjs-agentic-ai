import { useState, useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { InputForm } from "@/components/InputForm";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import {
  Copy,
  CopyCheck,
  MessageSquare,
  Brain,
  Zap,
  FileText,
  Target,
  BookOpen,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/utils";

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
  author?: string; // Agent author name
}

interface AgentTransition {
  name: string;
  badge: string;
  icon: string;
  description?: string;
}

export interface ChatMessagesViewProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (query: string) => void;
  onClear: () => void;
  activeAgent?: AgentTransition | null;
  isConnected: boolean;
}

const agentIcons: Record<string, React.ReactNode> = {
  interview: <MessageSquare className="h-3 w-3" />,
  reasoning: <Brain className="h-3 w-3" />,
  execution: <Zap className="h-3 w-3" />,
  documentation: <FileText className="h-3 w-3" />,
  orchestrator: <Target className="h-3 w-3" />,
};

const agentColors: Record<string, string> = {
  interview: "bg-green-200 text-green-800 border-green-300",
  reasoning: "bg-blue-200 text-blue-800 border-blue-300",
  execution: "bg-orange-200 text-orange-800 border-orange-300",
  documentation: "bg-purple-200 text-purple-800 border-purple-300",
  orchestrator: "bg-pink-200 text-pink-800 border-pink-300",
  root_agent: "bg-gray-200 text-gray-800 border-gray-300",
};

const agentNames: Record<string, string> = {
  interview_agent: "Interview Agent",
  reasoning_agent: "Reasoning Agent",
  execution_agent: "Execution Agent",
  documentation_agent: "Documentation Agent",
  root_agent: "Root Agent",
};

const getAgentBadge = (author?: string): string => {
  if (!author) return "orchestrator";
  const lowerAuthor = author.toLowerCase();
  if (lowerAuthor.includes("interview")) return "interview";
  if (lowerAuthor.includes("reasoning")) return "reasoning";
  if (lowerAuthor.includes("execution")) return "execution";
  if (lowerAuthor.includes("documentation")) return "documentation";
  if (lowerAuthor.includes("root")) return "orchestrator";
  return "orchestrator";
};

export function ChatMessagesView({
  messages,
  isLoading,
  onSubmit,
  onClear,
  activeAgent,
  isConnected,
}: ChatMessagesViewProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  };

  const formatTime = (timestamp?: string) => {
    if (!timestamp)
      return new Date().toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      });
    return new Date(timestamp).toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-border bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div>
            <h1 className="text-xl font-bold">🏥 Medical Triage Agent</h1>
            <p className="text-sm text-muted-foreground">
              Sistem Triase Medis Cerdas
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionStatus isConnected={isConnected} />
            {activeAgent && (
              <Badge
                variant="secondary"
                className={cn(
                  "flex items-center gap-2",
                  agentColors[activeAgent.badge]
                )}
              >
                {agentIcons[activeAgent.badge]}
                <span>{activeAgent.name}</span>
              </Badge>
            )}
            <Button variant="outline" size="sm" onClick={onClear}>
              Hapus Chat
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden bg-gray-50">
        <ScrollArea className="h-full">
          <div className="p-4 md:p-6 space-y-4 max-w-4xl mx-auto bg-gray-50">
            {/* Default Instruction Message */}
            {messages.length === 0 && (
              <div className="flex justify-start">
                <div className="flex flex-col items-start max-w-[85%]">
                  <div className="flex items-start gap-3">
                    <div className="rounded-2xl rounded-bl-sm bg-white border-2 border-gray-200 text-gray-900 px-4 py-2.5 shadow-lg">
                      <p className="text-sm text-foreground leading-relaxed">
                        👋 Halo! Saya adalah Smart Triage Agent. Saya akan
                        membantu Anda dalam proses triase medis.
                        <br />
                        <br />
                        Silakan ceritakan <strong>keluhan utama</strong> atau
                        gejala yang Anda rasakan saat ini.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {messages
              .filter(
                (message) => message.content && message.content.trim() !== ""
              )
              .map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex",
                    message.type === "human" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.type === "human" ? (
                    <div className="flex flex-col items-end max-w-[85%]">
                      <div className="rounded-2xl rounded-br-sm bg-blue-600 text-white px-4 py-2.5 shadow-lg border-2 border-blue-700/30">
                        <p className="text-sm whitespace-pre-wrap text-white font-medium leading-relaxed">
                          {message.content}
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground mt-1.5 px-2">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  ) : (
                    <div className="flex flex-col items-start max-w-[85%]">
                      {/* Agent Author Badge */}
                      {message.author && (
                        <div className="mb-1 px-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              "flex items-center gap-1.5 text-xs border",
                              agentColors[getAgentBadge(message.author)]
                            )}
                          >
                            {agentIcons[getAgentBadge(message.author)]}
                            <span>
                              {agentNames[message.author] || message.author}
                            </span>
                          </Badge>
                        </div>
                      )}
                      <div className="flex items-start gap-3">
                        <div className="rounded-2xl rounded-bl-sm bg-white border-2 border-gray-200 text-gray-900 px-4 py-2.5 shadow-lg">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            className="prose prose-sm max-w-none text-foreground"
                            components={{
                              p: ({ children }) => (
                                <p className="mb-3 last:mb-0 text-foreground leading-relaxed">
                                  {children}
                                </p>
                              ),
                              ol: ({ children }) => (
                                <ol className="list-decimal list-outside ml-5 mb-3 space-y-2 text-foreground">
                                  {children}
                                </ol>
                              ),
                              ul: ({ children }) => (
                                <ul className="list-disc list-outside ml-5 mb-3 space-y-2 text-foreground">
                                  {children}
                                </ul>
                              ),
                              li: ({ children }) => (
                                <li className="ml-2 text-foreground leading-relaxed">
                                  {children}
                                </li>
                              ),
                              strong: ({ children }) => (
                                <strong className="font-semibold text-foreground">
                                  {children}
                                </strong>
                              ),
                              em: ({ children }) => (
                                <em className="italic text-foreground">
                                  {children}
                                </em>
                              ),
                              code: ({ children }) => (
                                <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground">
                                  {children}
                                </code>
                              ),
                              pre: ({ children }) => (
                                <pre className="bg-muted p-3 rounded-lg overflow-x-auto my-2 text-foreground">
                                  {children}
                                </pre>
                              ),
                              a: ({ href, children }) => (
                                <a
                                  href={href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary underline hover:text-primary/80"
                                >
                                  {children}
                                </a>
                              ),
                              br: () => <br className="mb-2" />,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            handleCopy(message.content, message.id)
                          }
                        >
                          {copiedMessageId === message.id ? (
                            <CopyCheck className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      {/* References Section */}
                      {message.references && message.references.length > 0 && (
                        <div className="mt-2 px-2">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                            <BookOpen className="h-3 w-3" />
                            <span className="font-medium">
                              Referensi Dokumen:
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {message.references.map((ref, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                              >
                                <FileText className="h-3 w-3 mr-1" />
                                <span className="font-medium">
                                  {ref.filename}
                                </span>
                                <span className="ml-1 text-blue-600">
                                  (Chunk #{ref.chunks.join(", #")})
                                </span>
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      <span className="text-xs text-muted-foreground mt-1 px-2">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  )}
                </div>
              ))}

            {/* Loading Indicator - Inside Chat Bubble */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex flex-col items-start max-w-[85%]">
                  <div className="rounded-2xl rounded-bl-sm bg-white border-2 border-gray-200 text-gray-900 px-4 py-2.5 shadow-lg">
                    <div className="flex items-center gap-1">
                      <span className="text-sm text-foreground">Memproses</span>
                      <span className="loading-dots">
                        <span className="dot">.</span>
                        <span className="dot">.</span>
                        <span className="dot">.</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-white p-4 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <InputForm
            onSubmit={onSubmit}
            isLoading={isLoading}
            disabled={!isConnected}
          />
        </div>
      </div>
    </div>
  );
}
