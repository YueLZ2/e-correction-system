4# 对应文本描述：
# "The user login process includes an identity verification step. If the verification is successful, enter the panel; if it fails, return to the login page"
# digraph G {
#     login -> "Input Credentials"
#     "Input Credentials" -> "Verify Account"
#     "Verify Account" -> "Show Dashboard" [label="verify successfully"]
# }
import xml.etree.ElementTree as ET
from graphviz import Digraph
from pathlib import Path
from graphviz import Source
from typing import Optional
# 将DOT渲染为SVG文件
def extract_svg_from_dot(dot_code: str, output_path: str = "test_sample/sample/bpmn_diagram_3_1.svg") -> Optional[str]:
    """将 DOT 渲染为 SVG 文件"""

    src = Source(dot_code)
    svg_path = Path(output_path)
    src.render(svg_path.stem, directory=svg_path.parent, format='svg', cleanup=True)
    return str(svg_path)

extract_svg_from_dot(""" digraph G {    login -> "Input Credentials"
   "Input Credentials" -> "Verify Account"
     "Verify Account" -> "Show Dashboard" [label="verify successfully"]
 }
""")
