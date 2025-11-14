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
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.interview_agent.agent import interview_agent
from .sub_agents.reasoning_agent.agent import reasoning_agent
from .sub_agents.execution_agent.agent import execution_agent
from .sub_agents.documentation_agent.agent import documentation_agent
from .prompt import ORCHESTRATOR_INSTRUCTION

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="""Smart Triage Agent - Sistem triase medis yang mengelola 
    alur kerja untuk membantu pasien mendapatkan perawatan sesuai tingkat urgensi.""",
    instruction=ORCHESTRATOR_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[
        AgentTool(agent=interview_agent),
        AgentTool(agent=reasoning_agent),
        AgentTool(agent=execution_agent),
        AgentTool(agent=documentation_agent),
    ],
)

