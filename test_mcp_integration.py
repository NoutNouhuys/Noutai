import asyncio
import os
from types import SimpleNamespace
from mcp_integration import MCPIntegration

async def main():
    # 🔧 Dummy config om AnthropicConfig te vervangen
    config = SimpleNamespace(api_key="fake")

    # ✅ Zet de omgevingsvariabelen voor MCP-serverlocaties
    os.environ["MCP_SERVER_SCRIPT"] = "/Users/noutnouhuys/Documents/bitbucket-mcp-server/app.py"
    os.environ["MCP_SERVER_VENV_PATH"] = "/Users/noutnouhuys/Documents/bitbucket-mcp-server/venv"

    # 🧠 Maak MCP-integratie aan
    integration = MCPIntegration(config)

    # 📡 Verbind en haal tools op
    await integration.connect()

    print("\n🛠️ Tools gevonden op de server:")
    for name in integration.available_tool_names:
        print(f"– {name}")

    # 🧪 Test één specifieke tool, bv. list_repositories
    if "list_repositories" in integration.available_tool_names:
        result = await integration.list_repositories()
        print("\n📦 Repositories:")
        for repo in result:
            if isinstance(repo, dict):
                print(f"– {repo.get('name') or repo.get('slug')}")
            else:
                print(f"– {repo}")  # fallback als het iets anders is

    # 🔌 Verbreek de verbinding netjes
    await integration.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
