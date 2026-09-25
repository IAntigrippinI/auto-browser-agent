import asyncio

from bootstrap.application import build_agent


async def run() -> None:
    async with build_agent() as agent:
        prompt = input("> ")
        await agent.run(prompt)
        print(f"Token usage: {agent.token_usage}")



if __name__ == "__main__":
    asyncio.run(run())