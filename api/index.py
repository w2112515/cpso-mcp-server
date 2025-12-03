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
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


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

{result_state.strategy_draft}

## 审计报告

{result_state.audit_report}

---
请求 ID: {result_state.request_id}
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用工具"""
    if name == "execute_strategy":
        user_intent = arguments.get("user_intent")
        if not user_intent:
            raise ValueError("缺少 user_intent 参数")
        return execute_strategy_impl(user_intent)
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


# 创建 Starlette 应用
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)


# 本地开发测试入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
