import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Loader2,
  Send,
  Mic,
  MicOff,
  Image as ImageIcon,
  X,
} from "lucide-react";

interface InputFormProps {
  onSubmit: (
    query: string,
    attachments?: { type: "image" | "audio"; data: string; mimeType: string }[]
  ) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function InputForm({
  onSubmit,
  isLoading,
  disabled = false,
}: InputFormProps) {
  const [inputValue, setInputValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [attachments, setAttachments] = useState<
    {
      type: "image" | "audio";
      data: string;
      mimeType: string;
      preview?: string;
    }[]
  >([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const hasContent = inputValue.trim() || attachments.length > 0;
    if (hasContent && !isLoading && !disabled) {
      onSubmit(inputValue.trim() || "Mengirim lampiran", attachments);
      setInputValue("");
      setAttachments([]);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onloadend = () => {
          const result = reader.result as string;
          setAttachments((prev) => [
            ...prev,
            {
              type: "image",
              data: result,
              mimeType: file.type,
              preview: result,
            },
          ]);
        };
        reader.readAsDataURL(file);
      }
    });

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        const reader = new FileReader();
        reader.onloadend = () => {
          const result = reader.result as string;
          setAttachments((prev) => [
            ...prev,
            {
              type: "audio",
              data: result,
              mimeType: "audio/webm",
            },
          ]);
        };
        reader.readAsDataURL(audioBlob);

        // Stop all tracks
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop());
          audioStreamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert(
        "Tidak dapat mengakses mikrofon. Pastikan izin mikrofon sudah diberikan."
      );
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {attachments.map((attachment, index) => (
            <div key={index} className="relative inline-block">
              {attachment.type === "image" && attachment.preview && (
                <div className="relative">
                  <img
                    src={attachment.preview}
                    alt={`Attachment ${index + 1}`}
                    className="h-20 w-20 object-cover rounded-lg border-2 border-gray-200"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                    onClick={() => removeAttachment(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              )}
              {attachment.type === "audio" && (
                <div className="relative bg-gray-100 rounded-lg p-2 pr-8">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-xs text-gray-600">Audio</span>
                  </div>
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                    onClick={() => removeAttachment(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end space-x-2">
        <Textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ketik keluhan Anda di sini..."
          rows={1}
          className="flex-1 resize-none min-h-[40px]"
          disabled={disabled || isLoading}
        />

        {/* Image Upload Button */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
          className="hidden"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isLoading}
          title="Unggah gambar"
        >
          <ImageIcon className="h-4 w-4" />
        </Button>

        {/* Voice Recording Button */}
        {!isRecording ? (
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={startRecording}
            disabled={disabled || isLoading}
            title="Rekam suara"
          >
            <Mic className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            type="button"
            variant="destructive"
            size="icon"
            onClick={stopRecording}
            title="Hentikan rekaman"
          >
            <MicOff className="h-4 w-4" />
          </Button>
        )}

        <Button
          type="submit"
          size="icon"
          disabled={
            isLoading ||
            (!inputValue.trim() && attachments.length === 0) ||
            disabled
          }
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </form>
  );
}
