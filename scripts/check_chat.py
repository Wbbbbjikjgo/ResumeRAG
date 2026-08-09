"""验证对话追问 Agent（含多轮记忆）。"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.agent.chat_agent import ChatAgent


async def main() -> None:
    r1 = await ChatAgent.chat("有哪些候选人熟悉 Java 和 Spring？")
    print("=== A1 ===")
    print(r1[:600])

    r2 = await ChatAgent.chat("5 年以上经验的候选人有哪些？")
    print("=== A2 ===")
    print(r2[:600])

    r3 = await ChatAgent.chat("刚才第一个问题里的候选人学历怎么样？")
    print("=== A3（记忆验证）===")
    print(r3[:400])


if __name__ == "__main__":
    asyncio.run(main())
