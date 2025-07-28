
import asyncio
import datetime
import json
import logging
import re
from typing import Optional
from pathlib import Path
from metagpt.environment import Environment
from metagpt.schema import Message
from mutil_agent import CheckerAgent, BPMNTextAgent, ErrorCorrectorAgent, FastCorrectorAgent,ErrorInfo
from graphviz import Source
from typing import List, Dict, Union, Optional
from metagpt.config2 import Config
import xml.etree.ElementTree as ET
from graphviz import Digraph

# 日志设置
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,  # 调整为ERROR级别
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
# 禁用所有第三方库的日志
logging.getLogger("metagpt").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
Path("logs").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

# 新增模型映射配置
# spark=Config.from_home("spark.yaml") 
# gpt4t = Config.from_home("THUDM.yaml")  # 从`~/.metagpt`目录加载自定义配置`gpt-4-1106-preview.yaml`
deepseek = Config.default()  # 使用默认配置，即`config2.yaml`文件中的配置，
spark = Config.default() 
gpt4t = Config.default()

MODEL_MAP = {
    "GPT": gpt4t,  # 需确保从mutil_agent导入这些配置
    "Deepseek": deepseek,
    "Spark": spark
}

logger = logging.getLogger(__name__)

# 将DOT渲染为SVG文件
def extract_svg_from_dot(dot_code: str, output_path: str = "static/reports/bpmn_diagram.svg") -> Optional[str]:
    """将 DOT 渲染为 SVG 文件"""
    try:
        # 新增预处理步骤
        dot_code = re.sub(r'label="([\u4e00-\u9fa5]+)"', 
                          lambda m: 'label="' + ''.join('\\u{:04x}'.format(ord(c)) for c in m.group(1)) + '"', 
                          dot_code)
        
        src = Source(dot_code)
        svg_path = Path(output_path)
        src.render(svg_path.stem, directory=svg_path.parent, format='svg', cleanup=True)
        return str(svg_path)
    except Exception as e:
        logger.error(f"DOT图渲染失败: {e}\nProblematic DOT code:\n{dot_code}")  # 记录错误代码
def extract_publish_messages(log_text):
    """
    从日志中提取所有 publish_message: 后的内容。
    参数:
        log_text (str): 日志文本
    返回:
        List[str]: 所有提取出的 publish_message JSON 内容
    """
    pattern = r'publish_message:\s+(.*?)(?=\n\d{4}-\d{2}-\d{2}|\Z)'
    matches = re.findall(pattern, log_text, re.DOTALL)
    return [match.strip() for match in matches]
# 日志清空函数
def clear_log_file(log_path: str):
    try:
        with open(log_path, 'w') as f:
            f.truncate(0)
    except Exception as e:
        logger.error(f"日志清空失败: {str(e)}")
# 将SVG转换为DOT的函数（示例实现）

def svg_to_dot(svg_path: str) -> str:
    """
    将BPMN SVG文件转换为Graphviz DOT语言
    支持元素：任务(Task)、事件(Event)、网关(Gateway)、连接线(Sequence Flow)
    """
    # 加载SVG文件
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # 创建DOT图
    dot = Digraph(comment='BPMN Diagram', format='svg')
    dot.attr(rankdir='LR')  # 左右布局
    
    # 定义BPMN元素样式映射
    bpmn_styles = {
        'Task': {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#90EE90'},
        'Event': {'shape': 'circle', 'style': 'filled', 'fillcolor': '#FFD700'},
        'Gateway': {'shape': 'diamond', 'style': 'filled', 'fillcolor': '#FFA07A'},
        'SequenceFlow': {'arrowhead': 'normal', 'color': '#000000'}
    }
    
    # 元素ID映射表（解决重复ID问题）
    element_ids = {}
    
    # 处理所有SVG元素
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]  # 处理命名空间
        
        if tag in ['rect', 'circle', 'path']:
            # 提取BPMN元素属性
            bpmn_type = elem.get('{http://www.omg.org/spec/BPMN/20100524/MODEL}type', '')
            element_id = elem.get('id', f'element_{len(element_ids)}')
            element_ids[element_id] = element_id
            
            # 处理节点元素时添加引号转义
            if tag in ['rect', 'circle']:
                label = elem.get('name', element_id)
                # 添加DOT标签转义逻辑
                label = f'"{label}"'  # 确保标签用双引号包裹
                style = bpmn_styles.get(bpmn_type, {'shape': 'box'})
                
                dot.node(
                    element_id,
                    label=label,  # 使用转义后的标签
                    **style
                )
            
            # 处理连接线时添加有效性验证
            elif tag == 'path':
                if 'bpmnElement' in elem.attrib:
                    element_parts = elem.attrib['bpmnElement'].split('_')
                    if len(element_parts) >= 2:
                        source_id = element_parts[0]
                        target_id = element_parts[-1]
                        
                        # 验证节点存在性
                        if source_id in element_ids and target_id in element_ids:
                            style = bpmn_styles.get('SequenceFlow', {})
                            dot.edge(source_id, target_id, **style)

    # 优化DOT布局
    dot.attr(compound='true')
    dot.body.extend(['splines="ortho"', 'ranksep="1.5 equally"'])
    
    return dot.source

async def analyze_bpmn_flow(text_description: str, dot_input: Optional[str] = None, image_path: Optional[str] = None,
            agent_configs: dict = {
                "checker": "deepseek",
                "text_checker": "deepseek",
                "corrector": "gpt4",
                "fast_corrector": "gpt35"
            }):
    log_path = f"logs/{datetime.datetime.now().strftime('%Y%m%d')}.txt"

    env = Environment()
    env.add_roles([
        CheckerAgent(config=MODEL_MAP[agent_configs["checker"]]),
        BPMNTextAgent(config=MODEL_MAP[agent_configs["text_checker"]], text_description=text_description),
        ErrorCorrectorAgent(config=MODEL_MAP[agent_configs["corrector"]]),
        FastCorrectorAgent(config=MODEL_MAP[agent_configs["fast_corrector"]])
    ])

    dot_inputh = dot_input
    # Convert SVG to DOT using a placeholder function (to be implemented)
    print("dot_input地址:", dot_input)  # 打印 dot_input
    dot_input = svg_to_dot(dot_inputh)
    
    print("dot_input:", dot_input)  # 打印 dot_inpu
    print("text_description:", text_description)  # 打印 text_description
   
    env.publish_message(Message(
        content=dot_input,
        role="user",
        cause_by="metagpt.actions.add_requirement.AddRequirement",
        sent_from="SYSTEM",
        send_to=["Checker"]
    ))

    await env.run()

    # 提取结果
    # results = parse_agent_outputs(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        log_text = f.read()

    message_list = extract_publish_messages(log_text)
    suggestions = []
    corrected_bpmns = []
    # 修改为字典存储最新建议
    latest_suggestions = {}
    latest_corrections = {}

    # 处理每条消息
    for message in message_list:
        # 提取 JSON 部分（可能带有 Message N: 前缀）
        json_text = re.search(r'{.*}', message, re.DOTALL)
        if not json_text:
            continue
        data = json.loads(json_text.group())

        role = data.get("role", "")
        content = data.get("content", "")

        # 更新流程检测建议（只保留最后一次）
        if "流程检测专家" in role or "一致性检测专家" in role:
            try:
                suggestion_list = json.loads(content)
                for item in suggestion_list:
                    if isinstance(item, dict):
                        # 按专家类型存储最后一条建议
                        latest_suggestions[role] = {
                            "expert": role,
                            "error_type": item.get("error_type"),
                            "description": item.get("description"),
                            "suggestion": item.get("suggestion")
                        }
            except:
                pass

        # 更新修正专家结果（只保留最后一次）
        if "修正专家" in role:
            try:
                bpmn_info = json.loads(content)
                latest_corrections[role] = {
                    "expert": role,
                    "bpmn": bpmn_info.get("corrected_bpmn", ""),
                    "modifications": bpmn_info.get("modifications", {})
                }
            except:
                pass

    # 转换字典为列表
    suggestions = list(latest_suggestions.values())
    corrected_bpmns = list(latest_corrections.values())
            

    print("\n======= 修正后的BPMN图（最后一个专家） =======")
    # 在获取最终BPMN时增加清洗逻辑
    final_bpmn = corrected_bpmns[-1]["bpmn"] if corrected_bpmns else None
    if final_bpmn:
        # 移除DOT代码块标记和转义字符
        final_bpmn = re.sub(r'^```\w+\s*', '', final_bpmn, flags=re.MULTILINE)
        final_bpmn = final_bpmn.replace('\\n', '\n').replace('```', '').strip()

    report = {
        "diagram_svg": extract_svg_from_dot(final_bpmn) if final_bpmn else None,
        "suggestions": suggestions or ["没有发现问题"],
        "corrections": corrected_bpmns or ["没有发现修正"]
    }
    
    Path("static/reports/latest_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report

# 命令行入口
if __name__ == "__main__":
    import typer
    app = typer.Typer()

    @app.command()
    def main(
        bpmn_path: str = typer.Argument(..., help="BPMN文件路径"),
        description_path: str = typer.Argument(..., help="流程文本描述文件路径"),
        checker_model: str = typer.Option("spark", help="流程检测专家模型 (gpt4/deepseek/gpt35)"),
        text_model: str = typer.Option("deepseek", help="文本检测专家模型"),
        corrector_model: str = typer.Option("spark", help="综合修正专家模型"), 
        fast_model: str = typer.Option("spark", help="快速修正专家模型")
    ):
        async def _main():
            bpmn_content = Path(bpmn_path).read_text(encoding="utf-8")
            desc_content = Path(description_path).read_text(encoding="utf-8")
            report = await analyze_bpmn_flow(bpmn_content, desc_content,
             agent_configs={
                "checker": checker_model,
                "text_checker": text_model,
                "corrector": corrector_model,
                "fast_corrector": fast_model
            })
            print(json.dumps(report, ensure_ascii=False, indent=2))

        asyncio.run(_main())

    app()

