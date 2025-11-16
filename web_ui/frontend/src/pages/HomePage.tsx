import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Stethoscope, ArrowRight } from "lucide-react";

export function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            🏥 Medical Triage Agent
          </h1>
          <p className="text-lg text-gray-600">
            Sistem Triase Medis Cerdas dengan AI
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Pilih mode akses sesuai kebutuhan Anda
          </p>
        </div>

        {/* Selection Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Patient Card */}
          <Card className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-blue-400 group">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                <User className="h-10 w-10 text-blue-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">
                Mode Pasien
              </h2>
              <p className="text-gray-600 leading-relaxed">
                Konsultasi medis dengan AI agent. Dapatkan rekomendasi triase,
                panduan perawatan, dan informasi fasilitas kesehatan terdekat.
              </p>
              <ul className="text-left text-sm text-gray-600 space-y-2 w-full">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Konsultasi gejala medis</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Riwayat chat konsultasi</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Rekomendasi triase level</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Panduan perawatan mandiri</span>
                </li>
              </ul>
              <Button
                onClick={() => navigate("/patient")}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white group-hover:shadow-lg transition-all"
                size="lg"
              >
                Masuk sebagai Pasien
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>

          {/* Doctor Card */}
          <Card className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-green-400 group">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center group-hover:bg-green-200 transition-colors">
                <Stethoscope className="h-10 w-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">
                Mode Dokter
              </h2>
              <p className="text-gray-600 leading-relaxed">
                Akses catatan medis pasien, SOAP notes, dan riwayat kunjungan.
                Pantau kondisi pasien dan review hasil triase AI.
              </p>
              <ul className="text-left text-sm text-gray-600 space-y-2 w-full">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Lihat catatan SOAP pasien</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Riwayat medis lengkap</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Review hasil triase AI</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Data diagnosis & ICD codes</span>
                </li>
              </ul>
              <Button
                onClick={() => navigate("/doctor")}
                className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white group-hover:shadow-lg transition-all"
                size="lg"
              >
                Masuk sebagai Dokter
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>
        </div>

        {/* Footer Info */}
        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500">
            Sistem ini menggunakan AI untuk membantu proses triase medis.
            <br />
            Untuk kondisi darurat, segera hubungi layanan darurat medis.
          </p>
        </div>
      </div>
    </div>
  );
}

