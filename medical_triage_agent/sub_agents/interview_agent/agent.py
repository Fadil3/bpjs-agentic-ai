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
from .tools.tools import extract_symptoms_tool, query_interview_guide_tool

interview_agent = Agent(
    model='gemini-2.5-flash',
    name="interview_agent",
    description="""Agent yang melakukan wawancara dinamis dengan pasien untuk 
    mengumpulkan gejala, durasi, dan informasi medis relevan. Menggunakan NLP 
    untuk memahami keluhan dalam Bahasa Indonesia dan mengekstrak entitas medis.""",
    instruction=INTERVIEW_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.3),
    tools=[extract_symptoms_tool, query_interview_guide_tool],
    output_key="symptoms_data",  # Menyimpan hasil ke session state
)

