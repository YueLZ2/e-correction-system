import json
import re
import random
import logging
import datetime
from metagpt.actions.run_code import PROMPT_TEMPLATE
from metagpt.roles import Role
from graphviz import Digraph

from metagpt.actions import Action
from metagpt.schema import Message

from metagpt.config2 import Config
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import asyncio
from metagpt.environment import Environment
from metagpt.schema import Message

# 配置日志
logger = logging.getLogger(__name__)


# # 以下是一些示例配置，分别为gpt-4-1106-preview、gpt-4-0613和gpt-3.5-turbo-1106。
# gpt4t = Config.from_home("THUDM.yaml")  # 从`~/.metagpt`目录加载自定义配置`gpt-4-1106-preview.yaml`
# deepseek = Config.default()  # 使用默认配置，即`config2.yaml`文件中的配置，
# spark=Config.from_home("deepseek.yaml") 

deepseek = Config.default()  # 使用默认配置，即`config2.yaml`文件中的配置，
spark = Config.default() 
gpt4t = Config.default()

class ErrorInfo(BaseModel):
    error_type: str  # 错误分类
    description: str    # 错误描述
    suggestion: str     # 错误修复建议
    source : str        # 错误来源

# 你是一个BPMN2.0流程检测专家。
#     只需认真检查以下BPMN流程中存在的问题,不需要进行纠正,重点关注:
#     1.死锁问题：两个或者两个以上的进程（线程）在执行过程中，因争夺资源而造成的一种互相等待的现象:
#     2.语法错误:是否符合BPMN2.0规范。
#     3.同步缺失问题:流程中存在未同步的并行路径，导致资源冲突或重复执行。
#     4.合格问题：流程是否符合企业规则或行业标准。
#
class ErrorChecker(Action):
    PROMPT_TEMPLATE: str = """
   You are a BPMN2.0 process flow validation expert.
Strictly analyze the following DOT code for workflow logic errors and structural violations. Output a JSON array of errors with:

1. **Process Structure Errors**
    - Orphaned nodes (nodes without input/output connections)
    - Unreachable paths (nodes inaccessible from start event)
    - Circular dependencies (A→B→C→A loops)
    - Parallel gateway branch/merge mismatch (e.g., 3 branches but only 2 merges)

2. **BPMN Element Usage Errors**
    - Start/End event shape violations (Start must be circle, End doublecircle)
    - Gateway type/flow mismatch (e.g., exclusive gateway missing condition expressions)
    - Undefined task types (Service Task missing implementation class)

3. **Process Control Flow Errors**
    - Conflicting conditional branches (overlapping/missing branch conditions)
    - Missing default path (uncovered conditional branches)
    - Unbound signal/message event triggers

4. **Organizational Policy Validation**
    - Ambiguous swimlane (Pool/Lane) ownership
    - Cross-swimlane flows without gateways
    - Resource contention nodes without locks
    BPMN content:
    {context}
    Respond in **JSON array** format:
    {{
        "error_type": "Deadlock issues",
        "errors": [
        {{
            "element_id": "start1",
            "description": "xxx",
            "suggestion": "xxx"
        }}
        ]
    }}
   
    """
    
    async def run(self, context: str) -> List[ErrorInfo]:
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        response = await self._aask(prompt)
        error_report = self._parse_response(response)
        return error_report

    @staticmethod
    def _parse_response(response: str):
        try:
            # 添加空响应过滤
            if not response.strip():
                return []
            # 清理JSON响应
            json_str = re.sub(r'```json|```', '', response).strip()
            data = json.loads(json_str)

            #解析错误条目
            error = []
            for e in data.get("errors", []):
                error.append(
                    ErrorInfo(
                        source = 'ErrorChecker',
                        error_type=e.get("error_type", data.get("error_type", "unknown")),  # 优先使用条目中的错误类型
                        description=e["description"],
                        suggestion=e["suggestion"],
                        
                    )
                )
            return error
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析响应失败: {str(e)}\n原始响应内容: {response}")  # 记录原始响应
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []

# 在ErrorInfo类下方添加新检测器
class BPMNTextChecker(Action):
    PROMPT_TEMPLATE : str ="""
    Compare the following BPMN process with the text description to identify inconsistencies, The corrected result does not need to be given:
    
    BPMN content:
    {bpmn_xml}
    
    Text description:
    {text_description}
    
    Output requirements:
    1.Describe specific inconsistencies in a user-readable way
    2. Context information of specific elements needs to be included
    3. The format is free, as long as the final output is valid JSON
    4.Ensure the final output is a valid, machine-readable JSON array. Do not include any extra explanation or markdown formatting (no ```json).

    Respond in **JSON array** format:
    
    {{
        "error_type": "description_mismatch",
        "errors": [
            {{
                "element_id": "Element ID",
                "description": "Detailed issue description",
                "suggestion": "Correction recommendation"
            }}
        ]
    }}
    """
    
    async def run(self, bpmn_xml: str, text_description: str) -> List[ErrorInfo]:
        prompt = self.PROMPT_TEMPLATE.format(
            bpmn_xml=bpmn_xml,
            text_description=text_description
        )
        response = await self._aask(prompt)
        return self._parse_response(response)
        

    def _parse_response(self, response: str) -> List[ErrorInfo]:
        try:
            if not response.strip():
                return []
                
            # 增强型JSON提取
            json_str = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_str:
                raise ValueError("未找到有效JSON结构")
                
            data = json.loads(json_str.group())
            
            errors = []
            for e in data.get("errors", []):
                # 添加字段默认值
                element_id = e.get('element_id', '未知元素')
                desc = e.get('description', '').replace('"', "'")  # 统一引号处理
                
                errors.append(ErrorInfo(
                    source = 'BPMNTextChecker',
                    error_type=e.get('error_type', 'Inconsistent processes'),
                    description=f"{desc}",
                    suggestion=e.get('suggestion', 'No specific suggestions')
                ))
            return errors
            
        except json.JSONDecodeError as e:
            logger.error(f"响应解析失败，尝试提取纯文本错误：{str(e)}")
            return [ErrorInfo(
                source = 'BPMNTextChecker',
                error_type="解析错误",
                description=f"无法解析响应内容：{response[:100]}...",
                suggestion="请检查AI返回格式是否符合要求"
            )]
        except Exception as e:
            logger.error(f"意外错误: {str(e)}")
            return []
                

class ErrorCorrector(Action):
    PROMPT_TEMPLATE: str = """
    You are a Dot correction expert for the BPMN2.0 process. Please provide me with the modified flowchart in DOT language based on the following error report so that I can directly use the igraph library to convert it into an SVG image later
    Original BPMN DOT description:
    {context}
    
    Identified issues (prioritized):
    {error_report}
    Output requirements: Pay attention to the syntax of node definitions: Check whether the node definition part, such as A[Start], is correct. In the DOT language, node attributes should be wrapped in parentheses, and the attributes should be separated by commas. For example, the correct writing is A [label="Start"].
    1. Modify the DOT code to correct the identified issues.
    2. Ensure the modified DOT code is valid and can be directly used by the igraph library.
    3. The modified DOT code should not contain any extra explanation or markdown formatting (no ```json).
    4. Do not include any extra explanation or markdown formatting (no ```json).
    Respond with the modified DOT code only.
    
    """
    async def run(self, context: str, error_report: str) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            context=context,
            error_report=error_report
        )
        response = await self._aask(prompt)
        return response.strip()

# 流程检测专家
class CheckerAgent(Role):
    name: str = "Checker"
    profile: str = "BPMN2.0流程检测专家"

    def __init__(self,config: Optional[Config] = None, **kwargs):
        super().__init__(config = config,**kwargs)
        self.set_actions([ErrorChecker])
        self._watch([Message])  # 改为监听所有消息类型
    async def _act(self) -> Message:
        todo = self.rc.todo  # 获取待办事项
        msg = self.get_memories(k=1)[0]
     
        # 添加类型转换和错误处理
        try:
            error_report = await todo.run(msg.content)
            if error_report is not None:
                # 将ErrorInfo列表序列化为JSON字符串
                json_report = json.dumps([e.dict() for e in error_report], ensure_ascii=False)
                return Message(content=json_report, role=self.profile, cause_by=todo)
            else:
                logger.error("检测结果为空，无法生成报告")
                return Message(content="检测结果为空，无法生成报告", role=self.profile, cause_by=todo)
        except Exception as e:
            logger.error(f"检测流程失败: {str(e)}")
            return Message(content="检测失败", role=self.profile, cause_by=todo)

# 文本一致性检测专家
# 在CheckerAgent类下方添加新角色
class BPMNTextAgent(Role):
    name: str = "TextChecker"
    profile: str = "BPMN文本一致性检测专家"
    
    def __init__(self, text_description: str,config = None,**kwargs):
        super().__init__(config = config, **kwargs)
        self.set_actions([BPMNTextChecker])
        self.text_description = text_description
        self._watch([ErrorChecker])  # 添加对CheckerAgent消息的监听

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # 获取BPMN内容
        
        try:
            error_report = await todo.run(msg.content, self.text_description)
            json_report = json.dumps([e.dict() for e in error_report], ensure_ascii=False)
            return Message(content=json_report, role=self.profile, cause_by=todo)
        except Exception as e:
            logger.error(f"文本对比失败: {str(e)}")
            return Message(content="对比失败", role=self.profile, cause_by=todo)
  

class BaseCorrectorAgent(Role):
    """修正专家基类"""
    def __init__(self,  **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ErrorCorrector()])
        self._watch([ErrorChecker, BPMNTextChecker])
        self.modification_history = []
    async def _act(self) -> Message:
        todo = self.rc.todo
        # 收集所有错误报告
        reports = [msg for msg in self.get_memories() if "error_type" in msg.content]
        
        if not reports:
            logger.info("未发现需要修正的错误")
            return Message(content="流程无需修正", role=self.profile)
            
        try:
            combined_report = "\n".join([msg.content for msg in reports])
            original_bpmn = self.get_memories(k=1)[-1].content
            
            # 参数修正（context -> bpmn_xml 改为保持context）
            corrected_bpmn = await todo.run(
                context=original_bpmn,
                error_report=combined_report
            )
            
            # 生成修改摘要
            modification_summary = self._generate_summary(original_bpmn, corrected_bpmn)
            self.modification_history.append(modification_summary)
            # print(corrected_bpmn)
            # print("_______________________________")
            # 返回包含修正内容和修改摘要的消息
            return Message(
                content=json.dumps({
                    "corrected_bpmn": corrected_bpmn,
                    "modifications": modification_summary,
                    'expert':self.profile
                }, ensure_ascii=False),
                role=self.profile,
                cause_by=todo
            )
            
        except Exception as e:
            logger.error(f"综合修正失败: {str(e)}")
            return Message(content="修正失败", role=self.profile)

    def _generate_summary(self, original: str, corrected: str) -> dict:
        """生成修改摘要的对比逻辑"""
        diff_count = sum(1 for o, c in zip(original, corrected) if o != c)
        return {
            "modified_elements": diff_count,
            "change_details": self._find_xml_changes(original, corrected)
        }

    def _find_xml_changes(self, original: str, corrected: str) -> List[str]:
        """简单的XML差异对比实现"""
        # 这里可以集成专业的XML diff工具
        return ["检测到流程结构修改", "元素属性更新"]

class ErrorCorrectorAgent(BaseCorrectorAgent):
    """GPT-4修正专家"""
    name: str = "ErrorCorrector"
    profile: str = "BPMN2.0综合修正专家"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  

class FastCorrectorAgent(BaseCorrectorAgent):
    """GPT-3.5快速修正专家""" 
    name: str = "FastCorrector"
    profile: str = "BPMN快速修正专家"
    
    def __init__(self, **kwargs):
        super().__init__( **kwargs)  


  # llm:
  #   api_type: 'spark'
  #   app_id: 'd9629018'
  #   api_key: '0de643709424185d218dc66266625a11'
  #   api_secret: 'YjkyYzM3NTc0ZjdkNzIwMTA4NjZkNjJj'
  #   domain: 'generalv3'
  #   base_url: 'wss://spark-api.xf-yun.com/v3.1/chat'