# OmniSwarm Core - Module Entry Point
# Usage: python -m core

import asyncio
from core.node import main

if __name__ == "__main__":
    asyncio.run(main())
