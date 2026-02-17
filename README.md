Skill Maker Infra
Empowering Domain Experts to Transform Know-how into Executable AI Skills.
Skill Maker Infra is a specialized framework designed to bridge the gap between human expertise—particularly in the financial sector—and AI Agents. It provides a structured pipeline to extract implicit logic from experts, modularize business code, and compile them into standardized "Professional Skills" that any AI Agent can immediately understand and execute.
🚀 Key Features
Standardized Skill Architecture: A rigorous file structure (manifest.json, SKILL.md, tools/, knowledge/) that ensures consistency across all generated skills.
Expert Interviewer Agent: A built-in "Knowledge Engineer" that uses interactive dialogue to extract decision chains, risk thresholds, and edge-case strategies from domain experts.
Code-to-Skill Suggester: An intelligent scanner that identifies complex business logic within your existing codebase and automatically suggests refactoring it into a reusable Skill Package.
Skill Compiler: Automatically translates natural language prompts and Python logic into Anthropic Tool Use (JSON Schema) specifications.
🛠️ How to Use
Initialize the Project:
Run python skill_init.py to set up your skill registry and create your first standardized skill directory.
Extract Knowledge:
Execute python expert_interviewer.py. Follow the prompts to answer key questions about your professional logic (e.g., "What are the red flags in this credit risk assessment?"). This generates the SKILL.md prompt.
Encapsulate Tools:
Drop your specialized Python scripts into the tools/ folder, or use python scan_code.py to automatically detect and move business logic from your existing scripts into the skill structure.
Compile & Deploy:
Run python skill_compiler.py. This generates a tools_schema.json which can be loaded directly into any LLM-powered Agent to grant it your professional capabilities.
