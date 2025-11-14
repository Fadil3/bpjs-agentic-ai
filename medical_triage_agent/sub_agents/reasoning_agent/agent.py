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

from .prompt import REASONING_AGENT_INSTRUCTION
from .tools.tools import check_bpjs_criteria_tool

reasoning_agent = Agent(
    model='gemini-2.5-flash',
    name="reasoning_agent",
    description="""Agent yang melakukan analisis klinis berdasarkan gejala 
    dan memetakan ke Kriteria Gawat Darurat BPJS. Menentukan triage level 
    (Gawat Darurat / Mendesak / Non-Urgen) dengan justifikasi yang jelas.""",
    instruction=REASONING_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),  # Low temperature untuk konsistensi
    tools=[check_bpjs_criteria_tool],
    output_key="triage_result",  # Menyimpan hasil ke session state
)

