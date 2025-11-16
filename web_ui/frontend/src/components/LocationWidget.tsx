import { useState, useEffect, useRef } from "react";
import { MapPin, Loader2, Edit2, Check, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface LocationWidgetProps {
  onLocationUpdate?: (location: string) => void;
}

export function LocationWidget({ onLocationUpdate }: LocationWidgetProps) {
  const [location, setLocation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const locationSentRef = useRef(false); // Prevent multiple calls to onLocationUpdate

  useEffect(() => {
    // Try to get location from geolocation API
    if (navigator.geolocation) {
      setIsLoading(true);
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            // Reverse geocoding to get city name
            const { latitude, longitude } = position.coords;
            
            // Use backend endpoint for reverse geocoding to avoid CORS
            const response = await fetch(
              `/api/reverse-geocode?lat=${latitude}&lon=${longitude}`,
              {
                method: 'GET',
              }
            );
            
            if (response.ok) {
              const data = await response.json();
              const address = data.address;
              
              // Try to get city or town name
              const cityName = 
                address.city || 
                address.town || 
                address.municipality || 
                address.county || 
                address.state_district ||
                address.state ||
                "Lokasi tidak diketahui";
              
              setLocation(cityName);
              // Update parent component's state so location can be sent with first message
              if (onLocationUpdate && !locationSentRef.current) {
                locationSentRef.current = true;
                onLocationUpdate(cityName);
              }
            } else {
              // Fallback: use coordinates
              const fallbackLocation = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
              setLocation(fallbackLocation);
              // Update parent component's state so location can be sent with first message
              if (onLocationUpdate && !locationSentRef.current) {
                locationSentRef.current = true;
                onLocationUpdate(fallbackLocation);
              }
            }
          } catch (err) {
            console.error("Error getting location name:", err);
            setError("Gagal mendapatkan nama lokasi");
            // Fallback: use coordinates
            const fallbackLocation = `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
            setLocation(fallbackLocation);
            // Update parent component's state so location can be sent with first message
            if (onLocationUpdate && !locationSentRef.current) {
              locationSentRef.current = true;
              onLocationUpdate(fallbackLocation);
            }
          } finally {
            setIsLoading(false);
          }
        },
        (err) => {
          console.error("Geolocation error:", err);
          setError("Tidak dapat mengakses lokasi");
          setIsLoading(false);
          
          // Don't set default location - let user enter manually
          // Only set a placeholder message
          setLocation(null);
          // Don't call onLocationUpdate - let user enter location manually
        },
        {
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 300000 // Cache for 5 minutes
        }
      );
    } else {
      // Geolocation not supported
      setError("Geolocation tidak didukung");
      setIsLoading(false);
      // Don't set default location - let user enter manually
      setLocation(null);
      // Don't call onLocationUpdate - let user enter location manually
    }
  }, [onLocationUpdate]);

  const handleEdit = () => {
    setEditValue(location || "");
    setIsEditing(true);
    // Focus input after state update
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleSave = () => {
    if (editValue.trim()) {
      const newLocation = editValue.trim();
      setLocation(newLocation);
      setError(null); // Clear error when user manually enters location
      // Update parent component's state so location can be sent with first message
      if (onLocationUpdate) {
        // Reset flag to allow updating location
        locationSentRef.current = false;
        locationSentRef.current = true;
        onLocationUpdate(newLocation);
      }
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditValue("");
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-1.5 bg-white border border-gray-200 rounded-md px-2 py-1">
        <MapPin className="h-3 w-3 text-blue-600" />
        <Input
          ref={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Masukkan lokasi"
          className="h-6 px-2 text-xs border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          style={{ width: "150px" }}
        />
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5"
          onClick={handleSave}
          title="Simpan"
        >
          <Check className="h-3 w-3 text-green-600" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5"
          onClick={handleCancel}
          title="Batal"
        >
          <X className="h-3 w-3 text-gray-500" />
        </Button>
      </div>
    );
  }

  return (
    <Badge
      variant="default"
      className="flex items-center gap-1.5 cursor-pointer hover:bg-primary/90 transition-colors"
      onClick={handleEdit}
      title="Klik untuk mengubah lokasi"
    >
      {isLoading ? (
        <>
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Mendeteksi lokasi...</span>
        </>
      ) : !location ? (
        <>
          <MapPin className="h-3 w-3" />
          <span>Klik untuk masukkan lokasi</span>
          <Edit2 className="h-3 w-3 ml-1 opacity-70" />
        </>
      ) : (
        <>
          <MapPin className="h-3 w-3" />
          <span>{location}</span>
          <Edit2 className="h-3 w-3 ml-1 opacity-70" />
        </>
      )}
    </Badge>
  );
}

