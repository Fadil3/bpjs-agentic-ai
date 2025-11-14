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

from .prompt import DOCUMENTATION_AGENT_INSTRUCTION
from .tools.tools import format_soap_tool, recommend_icd_code_tool

documentation_agent = Agent(
    model='gemini-2.5-flash',
    name="documentation_agent",
    description="""Agent yang meringkas seluruh interaksi dengan pasien ke 
    format SOAP (Subjektif, Objektif, Asesmen, Plan) dan merekomendasikan 
    kode ICD-10/ICD-9 untuk dokumentasi medis.""",
    instruction=DOCUMENTATION_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[format_soap_tool, recommend_icd_code_tool],
    output_key="medical_documentation",  # Menyimpan hasil ke session state
)

