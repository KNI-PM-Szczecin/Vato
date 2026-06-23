---
name: architecture
description: Generate MVC/MVVM project structure, directory layout, and requirements.txt for this Python desktop app. Use before writing any application code.
---

Read Zalozenia/instruction.txt, then:

1. Propose a clean MVC/MVVM directory structure for this CustomTkinter + Python project (views, controllers/viewmodels, services, models, ai, utils)
2. Show which file goes in which directory with a one-line purpose for each
3. Generate a complete requirements.txt with minimum version pins
4. Explain the async strategy: how background threads and asyncio interact with CustomTkinter's main loop so the GUI never freezes
5. Note any key architectural decisions or open tradeoffs

Do NOT write application code yet. Focus on structure, dependencies, and async design. After presenting the proposal, ask for any clarifications before implementation begins.
