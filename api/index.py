"""
Vercel Serverless Function for CPSO MCP Server
使用 MCP SDK SSE Transport 实现标准协议
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.sse import SseServerTransport
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import json


def execute_strategy_impl(user_intent: str) -> list[TextContent]:
    """执行战略规划"""
    try:
        from cpsp_protocol.graph import create_graph
        from cpsp_protocol.state.schema import GlobalState, GlobalStateStatus
        import uuid
        
        state = GlobalState(
            request_id=str(uuid.uuid4()),
            status=GlobalStateStatus.SCOUTING,
            iteration_count=0,
            user_intent=user_intent,
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing="",
            technical_correction=None,
            strategy_draft="",
            audit_report="",
            input_attachments=[]
        )
        
        graph = create_graph()
        result_state = graph.invoke(state)
        
        result_text = f"""## 战略草案

{result_state["strategy_draft"]}

## 审计报告

{result_state["audit_report"]}

---
请求 ID: {result_state["request_id"]}
"""
    except Exception as e:
        print(f"CPSO execution error: {str(e)}")
        result_text = f"""## 战略分析结果

针对您的需求："{user_intent}"

### 1. 市场分析
- 目标市场规模和增长趋势
- 主要竞争对手分析
- 市场机会与威胁

### 2. 战略建议
- 短期目标（1-3个月）
- 中期目标（3-12个月）
- 长期目标（1-3年）

### 3. 实施路径
1. 第一阶段：市场调研与验证
2. 第二阶段：产品/服务开发
3. 第三阶段：市场推广与扩展

---
*注意：当前为演示输出。完整 CPSO 系统需要配置环境变量*
"""
    return [TextContent(type="text", text=result_text)]


def analyze_intent_impl(user_intent: str) -> list[TextContent]:
    """分析用户战略意图并生成侦察指令"""
    try:
        from cpsp_protocol.nodes.cpso import intent_analysis
        from cpsp_protocol.state.schema import GlobalState, GlobalStateStatus
        import uuid
        
        # Initialize the state with user intent
        state = GlobalState(
            request_id=str(uuid.uuid4()),
            status=GlobalStateStatus.SCOUTING,
            iteration_count=0,
            user_intent=user_intent,
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing="",
            technical_correction=None,
            strategy_draft="",
            audit_report="",
            input_attachments=[]
        )
        
        # Create and run just the intent analysis part of the graph
        result_state = intent_analysis(state)
        
        # Convert ScoutInstruction objects to dictionaries
        scout_instructions_dicts = []
        for instruction in result_state.scout_instructions:
            scout_instructions_dicts.append({
                "id": instruction.id,
                "role": instruction.role,
                "topic": instruction.topic,
                "status": instruction.status
            })
        
        result_json = json.dumps(scout_instructions_dicts, ensure_ascii=False, indent=2)
        result_text = f"## 侦察指令\n\n```json\n{result_json}\n```"
        
    except Exception as e:
        print(f"Analyze intent error: {str(e)}")
        result_text = f"分析意图时出现错误: {str(e)}"
        
    return [TextContent(type="text", text=result_text)]


def search_market_impl(topic: str) -> list[TextContent]:
    """执行市场情报搜索"""
    try:
        from cpsp_protocol.tools.web_search import web_search
        
        # Perform web search for market intelligence
        search_results = web_search(topic, num_results=5)
        
        # Format results
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        
        result_json = json.dumps(formatted_results, ensure_ascii=False, indent=2)
        result_text = f"## 市场搜索结果\n\n```json\n{result_json}\n```"
        
    except Exception as e:
        print(f"Market search error: {str(e)}")
        result_text = f"市场搜索时出现错误: {str(e)}"
        
    return [TextContent(type="text", text=result_text)]


def search_competitor_impl(topic: str) -> list[TextContent]:
    """执行竞争对手分析搜索"""
    try:
        from cpsp_protocol.tools.web_search import web_search
        
        # Perform web search for competitor analysis
        search_results = web_search(topic, num_results=5)
        
        # Format results
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        
        result_json = json.dumps(formatted_results, ensure_ascii=False, indent=2)
        result_text = f"## 竞争对手搜索结果\n\n```json\n{result_json}\n```"
        
    except Exception as e:
        print(f"Competitor search error: {str(e)}")
        result_text = f"竞争对手搜索时出现错误: {str(e)}"
        
    return [TextContent(type="text", text=result_text)]


def generate_strategy_impl(intelligence_briefing: str) -> list[TextContent]:
    """基于情报简报生成战略草案"""
    try:
        from cpsp_protocol.nodes.cpso import strategy_generation
        from cpsp_protocol.state.schema import GlobalState, GlobalStateStatus
        import uuid
        
        # Initialize the state with consolidated briefing
        state = GlobalState(
            request_id=str(uuid.uuid4()),
            status=GlobalStateStatus.DRAFTING,
            iteration_count=0,
            user_intent="",
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing=intelligence_briefing,
            technical_correction=None,
            strategy_draft="",
            audit_report="",
            input_attachments=[]
        )
        
        # Create and run just the strategy generation part of the graph
        result_state = strategy_generation(state)
        
        result_text = f"## 战略草案\n\n{result_state.strategy_draft}"
        
    except Exception as e:
        print(f"Strategy generation error: {str(e)}")
        result_text = f"生成战略时出现错误: {str(e)}"
        
    return [TextContent(type="text", text=result_text)]


def audit_strategy_impl(strategy_draft: str, intelligence_briefing: str) -> list[TextContent]:
    """审计战略文档"""
    try:
        from cpsp_protocol.nodes.auditor import adversarial_audit
        from cpsp_protocol.state.schema import GlobalState, GlobalStateStatus
        import uuid
        
        # Initialize the state with strategy draft and consolidated briefing
        state = GlobalState(
            request_id=str(uuid.uuid4()),
            status=GlobalStateStatus.AUDITING,
            iteration_count=0,
            user_intent="",
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing=intelligence_briefing,
            technical_correction=None,
            strategy_draft=strategy_draft,
            audit_report="",
            input_attachments=[]
        )
        
        # Create and run just the audit part of the graph
        result_state = adversarial_audit(state)
        
        result_text = f"## 审计报告\n\n{result_state.audit_report}"
        
    except Exception as e:
        print(f"Strategy audit error: {str(e)}")
        result_text = f"审计战略时出现错误: {str(e)}"
        
    return [TextContent(type="text", text=result_text)]


# 初始化 MCP Server
server = Server("cpso-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="execute_strategy",
            description="执行战略规划流程，基于用户意图生成商业战略文档。支持市场分析、竞争对手研究、技术评估等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_intent": {
                        "type": "string",
                        "description": "用户的战略需求或业务问题描述"
                    }
                },
                "required": ["user_intent"],
            },
        ),
        Tool(
            name="analyze_intent",
            description="分析用户战略意图并生成侦察指令",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_intent": {
                        "type": "string",
                        "description": "用户的战略需求或业务问题描述"
                    }
                },
                "required": ["user_intent"],
            },
        ),
        Tool(
            name="search_market",
            description="执行市场情报搜索",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "要搜索的市场主题"
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="search_competitor",
            description="执行竞争对手分析搜索",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "要搜索的竞争对手主题"
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="generate_strategy",
            description="基于情报简报生成战略草案",
            inputSchema={
                "type": "object",
                "properties": {
                    "intelligence_briefing": {
                        "type": "string",
                        "description": "用于生成战略的情报简报"
                    }
                },
                "required": ["intelligence_briefing"],
            },
        ),
        Tool(
            name="audit_strategy",
            description="审计战略文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy_draft": {
                        "type": "string",
                        "description": "要审计的战略草案"
                    },
                    "intelligence_briefing": {
                        "type": "string",
                        "description": "战略基于的情报简报"
                    }
                },
                "required": ["strategy_draft", "intelligence_briefing"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用工具"""
    if name == "execute_strategy":
        user_intent = arguments.get("user_intent")
        if not user_intent:
            raise ValueError("缺少 user_intent 参数")
        return execute_strategy_impl(user_intent)
    elif name == "analyze_intent":
        user_intent = arguments.get("user_intent")
        if not user_intent:
            raise ValueError("缺少 user_intent 参数")
        return analyze_intent_impl(user_intent)
    elif name == "search_market":
        topic = arguments.get("topic")
        if not topic:
            raise ValueError("缺少 topic 参数")
        return search_market_impl(topic)
    elif name == "search_competitor":
        topic = arguments.get("topic")
        if not topic:
            raise ValueError("缺少 topic 参数")
        return search_competitor_impl(topic)
    elif name == "generate_strategy":
        intelligence_briefing = arguments.get("intelligence_briefing")
        if not intelligence_briefing:
            raise ValueError("缺少 intelligence_briefing 参数")
        return generate_strategy_impl(intelligence_briefing)
    elif name == "audit_strategy":
        strategy_draft = arguments.get("strategy_draft")
        intelligence_briefing = arguments.get("intelligence_briefing")
        if not strategy_draft:
            raise ValueError("缺少 strategy_draft 参数")
        if not intelligence_briefing:
            raise ValueError("缺少 intelligence_briefing 参数")
        return audit_strategy_impl(strategy_draft, intelligence_briefing)
    raise ValueError(f"未知的工具: {name}")


# SSE Transport
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    """处理 SSE 连接"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )


async def health_check(request):
    """健康检查"""
    return JSONResponse({
        "status": "healthy",
        "service": "cpso-mcp-server",
        "version": "1.0.0"
    })


async def homepage(request):
    """根路径"""
    return JSONResponse({
        "name": "CPSO MCP Server",
        "version": "1.0.0",
        "status": "running",
        "sse_endpoint": "/sse",
        "message_endpoint": "/messages/"
    })


# 创建 Starlette 应用
app = Starlette(
    debug=True,
    routes=[
        Route("/", endpoint=homepage),
        Route("/health", endpoint=health_check),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    ],
)


# 本地开发测试入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)