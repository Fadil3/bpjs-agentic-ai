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

"""Tools for reading session state."""

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext


def get_patient_location(tool_context: ToolContext = None) -> str:
    """
    Membaca lokasi pasien dari session state.
    
    Returns:
        str: Lokasi pasien jika tersedia, atau string kosong jika tidak tersedia.
    """
    if tool_context and tool_context.state:
        location = tool_context.state.get("patient_location")
        if location:
            return f"Lokasi pasien: {location}"
        else:
            return "Lokasi pasien belum tersedia"
    return "Lokasi pasien belum tersedia"


get_patient_location_tool = FunctionTool(
    func=get_patient_location,
)

