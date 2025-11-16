# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.genai import types

from .prompt import INTERVIEW_AGENT_INSTRUCTION
from .tools.tools import extract_symptoms_tool
from medical_triage_agent.knowledge_base.chroma_tools import query_bates_guide_tool
from medical_triage_agent.sub_agents.execution_agent.tools.jkn_tools import query_jkn_medical_history_tool

interview_agent = Agent(
    model='gemini-2.5-flash',
    name="interview_agent",
    description="""Agent yang melakukan wawancara dinamis dengan pasien untuk 
    mengumpulkan gejala, durasi, dan informasi medis relevan. Menggunakan NLP 
    untuk memahami keluhan dalam Bahasa Indonesia dan mengekstrak entitas medis.
    Memiliki akses ke Chroma vector database untuk Bates Guide to Physical Examination.
    Memiliki akses ke sistem JKN/BPJS untuk query riwayat medis pasien.
    Setelah ekstraksi gejala selesai, mendelegasikan ke reasoning_agent untuk analisis.""",
    instruction=INTERVIEW_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.3),
    tools=[extract_symptoms_tool, query_bates_guide_tool, query_jkn_medical_history_tool],
    # NOTE: Tidak menggunakan output_key karena extract_symptoms menyimpan langsung ke state via ToolContext
    # output_key akan menimpa JSON hasil ekstraksi dengan text response agent
    # ToolContext akan otomatis disediakan oleh ADK sebagai parameter terakhir tool function
    # NOTE: reasoning_agent akan ditambahkan sebagai sub-agent di agent.py untuk menghindari circular import
)

