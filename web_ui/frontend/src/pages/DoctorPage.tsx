import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Search,
  FileText,
  Calendar,
  User,
  Pill,
  Activity,
  AlertCircle,
  Clock,
} from "lucide-react";

interface Patient {
  id: string;
  name: string;
  nik: string;
  age: number;
  gender: string;
  lastVisit: string;
}

interface SOAPNote {
  id: string;
  patientId: string;
  patientName: string;
  createdAt: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  triageLevel: string;
  icdCodes?: Array<{ code: string; description: string }>;
}

interface MedicalHistory {
  visitDate: string;
  facility: string;
  diagnosis: string;
  icdCode: string;
  medications: Array<{ name: string; dosage: string; frequency: string }>;
  doctor: string;
}

export function DoctorPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [soapNotes, setSoapNotes] = useState<SOAPNote[]>([]);
  const [medicalHistory, setMedicalHistory] = useState<MedicalHistory[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/doctor/patients");
      if (response.ok) {
        const data = await response.json();
        setPatients(data);
      } else {
        console.error(
          "Failed to load patients:",
          response.status,
          response.statusText
        );
        // Set empty array on error to prevent undefined issues
        setPatients([]);
      }
    } catch (error) {
      console.error("Error loading patients:", error);
      // Set empty array on error to prevent undefined issues
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPatientData = async (patientId: string) => {
    try {
      setLoading(true);
      const [soapResponse, historyResponse] = await Promise.all([
        fetch(`/api/doctor/patients/${patientId}/soap`),
        fetch(`/api/doctor/patients/${patientId}/history`),
      ]);

      if (soapResponse.ok) {
        const soapData = await soapResponse.json();
        setSoapNotes(soapData || []);
      } else {
        console.error(
          "Failed to load SOAP notes:",
          soapResponse.status,
          soapResponse.statusText
        );
        setSoapNotes([]);
      }

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setMedicalHistory(historyData || []);
      } else {
        console.error(
          "Failed to load medical history:",
          historyResponse.status,
          historyResponse.statusText
        );
        setMedicalHistory([]);
      }
    } catch (error) {
      console.error("Error loading patient data:", error);
      setSoapNotes([]);
      setMedicalHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    loadPatientData(patient.id);
  };

  const filteredPatients = patients.filter((patient) => {
    const name = patient.name || "";
    const nik = patient.nik || "";
    return (
      name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      nik.includes(searchQuery)
    );
  });

  const getTriageBadgeColor = (level: string | undefined) => {
    if (!level) {
      return "bg-gray-100 text-gray-800 border-gray-300";
    }
    switch (level.toLowerCase()) {
      case "gawat darurat":
        return "bg-red-100 text-red-800 border-red-300";
      case "mendesak":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "non-urgen":
        return "bg-green-100 text-green-800 border-green-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  return (
    <div className="h-screen w-screen bg-gray-50 flex">
      {/* Sidebar - Patient List */}
      <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold mb-4">Daftar Pasien</h2>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Cari pasien..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {loading ? (
              <div className="text-center text-gray-500 py-8">Memuat...</div>
            ) : filteredPatients.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <User className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Tidak ada pasien ditemukan</p>
              </div>
            ) : (
              filteredPatients.map((patient) => (
                <Card
                  key={patient.id}
                  className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedPatient?.id === patient.id
                      ? "bg-blue-50 border-blue-300"
                      : ""
                  }`}
                  onClick={() => handleSelectPatient(patient)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">
                        {patient.name || "Nama tidak tersedia"}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        NIK: {patient.nik || "Tidak tersedia"}
                      </p>
                      <p className="text-xs text-gray-500">
                        {patient.age || "?"} tahun,{" "}
                        {patient.gender || "Tidak tersedia"}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Kunjungan terakhir:{" "}
                        {new Date(patient.lastVisit).toLocaleDateString(
                          "id-ID"
                        )}
                      </p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedPatient ? (
          <>
            {/* Patient Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">
                    {selectedPatient.name || "Nama tidak tersedia"}
                  </h2>
                  <p className="text-sm text-gray-500">
                    NIK: {selectedPatient.nik || "Tidak tersedia"} |{" "}
                    {selectedPatient.age || "?"} tahun,{" "}
                    {selectedPatient.gender || "Tidak tersedia"}
                  </p>
                </div>
              </div>
            </div>

            {/* Content Tabs */}
            <div className="flex-1 overflow-hidden flex">
              <ScrollArea className="flex-1 p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                  {/* SOAP Notes Section */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Catatan SOAP
                    </h3>
                    {soapNotes.length === 0 ? (
                      <Card className="p-6 text-center text-gray-500">
                        Belum ada catatan SOAP untuk pasien ini
                      </Card>
                    ) : (
                      <div className="space-y-4">
                        {soapNotes.map((note) => (
                          <Card key={note.id} className="p-6">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-gray-400" />
                                <span className="text-sm text-gray-500">
                                  {new Date(note.createdAt).toLocaleString(
                                    "id-ID"
                                  )}
                                </span>
                              </div>
                              <Badge
                                className={getTriageBadgeColor(
                                  note.triageLevel
                                )}
                              >
                                {note.triageLevel || "Tidak tersedia"}
                              </Badge>
                            </div>

                            <div className="space-y-4">
                              <div>
                                <h4 className="font-semibold text-sm text-blue-600 mb-2">
                                  S (Subjektif)
                                </h4>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {note.subjective}
                                </p>
                              </div>

                              <div>
                                <h4 className="font-semibold text-sm text-green-600 mb-2">
                                  O (Objektif)
                                </h4>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {note.objective}
                                </p>
                              </div>

                              <div>
                                <h4 className="font-semibold text-sm text-orange-600 mb-2">
                                  A (Asesmen)
                                </h4>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {note.assessment}
                                </p>
                                {note.icdCodes && note.icdCodes.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs font-medium text-gray-600 mb-1">
                                      Kode ICD:
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                      {note.icdCodes?.map((icd, idx) => (
                                        <Badge
                                          key={`${note.id}-icd-${idx}-${icd.code}`}
                                          variant="outline"
                                          className="text-xs"
                                        >
                                          {icd.code} - {icd.description}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              <div>
                                <h4 className="font-semibold text-sm text-purple-600 mb-2">
                                  P (Plan)
                                </h4>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {note.plan}
                                </p>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Medical History Section */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      Riwayat Medis
                    </h3>
                    {medicalHistory.length === 0 ? (
                      <Card className="p-6 text-center text-gray-500">
                        Belum ada riwayat medis untuk pasien ini
                      </Card>
                    ) : (
                      <div className="space-y-4">
                        {medicalHistory.map((history, idx) => (
                          <Card
                            key={`history-${idx}-${history.visitDate || idx}-${
                              history.facility || ""
                            }`}
                            className="p-6"
                          >
                            <div className="flex items-start justify-between mb-4">
                              <div>
                                <div className="flex items-center gap-2 mb-1">
                                  <Calendar className="h-4 w-4 text-gray-400" />
                                  <span className="font-medium">
                                    {new Date(
                                      history.visitDate
                                    ).toLocaleDateString("id-ID", {
                                      day: "numeric",
                                      month: "long",
                                      year: "numeric",
                                    })}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-600">
                                  {history.facility}
                                </p>
                                <p className="text-sm text-gray-500">
                                  Dokter: {history.doctor}
                                </p>
                              </div>
                            </div>

                            <div className="space-y-3">
                              <div>
                                <p className="text-sm font-medium text-gray-700">
                                  Diagnosis: {history.diagnosis}
                                </p>
                                <Badge
                                  variant="outline"
                                  className="mt-1 text-xs"
                                >
                                  ICD: {history.icdCode}
                                </Badge>
                              </div>

                              {history.medications &&
                                history.medications.length > 0 && (
                                  <div>
                                    <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                      <Pill className="h-4 w-4" />
                                      Obat-obatan:
                                    </p>
                                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                      {history.medications.map(
                                        (med, medIdx) => (
                                          <li
                                            key={`med-${idx}-${medIdx}-${
                                              med.name || medIdx
                                            }`}
                                          >
                                            {med.name} - {med.dosage},{" "}
                                            {med.frequency}
                                          </li>
                                        )
                                      )}
                                    </ul>
                                  </div>
                                )}
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </ScrollArea>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <User className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold mb-2">Pilih Pasien</h3>
              <p className="text-gray-500">
                Pilih pasien dari daftar untuk melihat catatan SOAP dan riwayat
                medis
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
