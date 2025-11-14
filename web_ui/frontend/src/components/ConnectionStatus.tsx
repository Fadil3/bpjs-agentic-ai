import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff } from "lucide-react";

interface ConnectionStatusProps {
  isConnected: boolean;
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <Badge
      variant={isConnected ? "default" : "destructive"}
      className="flex items-center gap-1.5"
    >
      {isConnected ? (
        <>
          <Wifi className="h-3 w-3" />
          <span>Terhubung</span>
        </>
      ) : (
        <>
          <WifiOff className="h-3 w-3" />
          <span>Menghubungkan...</span>
        </>
      )}
    </Badge>
  );
}

