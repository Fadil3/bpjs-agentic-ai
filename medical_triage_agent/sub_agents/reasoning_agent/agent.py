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
from google.adk.planners import BuiltInPlanner
from google.genai import types

from .prompt import REASONING_AGENT_INSTRUCTION
from .tools.tools import check_bpjs_criteria_tool
from medical_triage_agent.knowledge_base.chroma_tools import (
    query_bpjs_criteria_tool,
    query_ppk_kemenkes_tool,
    query_knowledge_base_tool
)
# Create thinking config for deep clinical reasoning
thinking_config = types.ThinkingConfig(
    include_thoughts=True,   # Include thinking process in response for transparency
    thinking_budget=16000,   # Allocate tokens for deep reasoning (0-24576)
)

# Create planner with thinking config
planner = BuiltInPlanner(thinking_config=thinking_config)

reasoning_agent = Agent(
    model='gemini-2.5-flash',
    name="reasoning_agent",
    description="""Agent yang melakukan analisis klinis berdasarkan gejala 
    dan memetakan ke Kriteria Gawat Darurat BPJS. Menentukan triage level 
    (Gawat Darurat / Mendesak / Non-Urgen) dengan justifikasi yang jelas.
    Memiliki akses ke Chroma vector database untuk BPJS criteria dan PPK Kemenkes guidelines.""",
    instruction=REASONING_AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,  # Low temperature untuk konsistensi
    ),
    planner=planner,  # Use planner for thinking mode (required by ADK)
    tools=[
        check_bpjs_criteria_tool,
        query_bpjs_criteria_tool,
        query_ppk_kemenkes_tool,
        query_knowledge_base_tool
    ],
    output_key="triage_result",  # Menyimpan hasil ke session state
)

# Add execution_agent as sub-agent after definition to avoid circular import
# This allows reasoning_agent to directly delegate to execution_agent
from medical_triage_agent.sub_agents.execution_agent.agent import execution_agent
reasoning_agent.sub_agents = [execution_agent]

