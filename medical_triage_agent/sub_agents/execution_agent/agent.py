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

from .prompt import EXECUTION_AGENT_INSTRUCTION
from .tools.tools import (
    call_emergency_service_tool,
    schedule_mobile_jkn_tool,
    get_self_care_guide_tool
)
from .tools.jkn_tools import (
    query_fktp_registered_tool,
    query_nearest_facility_tool,
    query_jkn_medical_history_tool
)
from medical_triage_agent.knowledge_base.chroma_tools import (
    query_bpjs_criteria_tool,
    query_ppk_kemenkes_tool,
    query_knowledge_base_tool
)

execution_agent = Agent(
    model='gemini-2.5-flash',
    name="execution_agent",
    description="""Agent yang mengambil tindakan nyata berdasarkan triage level. 
    Memanggil API untuk layanan darurat, penjadwalan Mobile JKN, atau mengambil 
    panduan self-care. Menyediakan justifikasi detail dengan referensi ke knowledge base.""",
    instruction=EXECUTION_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[
        call_emergency_service_tool,
        schedule_mobile_jkn_tool,
        get_self_care_guide_tool,
        query_fktp_registered_tool,
        query_nearest_facility_tool,
        query_jkn_medical_history_tool,
        query_bpjs_criteria_tool,
        query_ppk_kemenkes_tool,
        query_knowledge_base_tool
    ],
    output_key="execution_result",  # Menyimpan hasil ke session state
)

