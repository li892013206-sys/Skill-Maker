#!/usr/bin/env python3
"""Skill Maker - 专家访谈器：通过多轮对话提取隐性知识，生成结构化 SKILL.md"""

import argparse
import json
import os
import sys

from anthropic import Anthropic

INTERVIEW_SYSTEM_PROMPT = """你是一个资深的金融知识工程专家，你的目标是通过提问，提取用户脑中的隐性知识（逻辑、阈值、异常处理策略）。
你需要围绕以下维度进行深入访谈：角色定义、核心能力、决策链、约束条件、输出规范。
在访谈过程中，你必须覆盖以下关键问题：
1. 这个任务的成功标准是什么？
2. 有哪些绝对不能踩的红线？
3. 如果数据缺失，您通常如何判断？
当你认为信息已经足够时，回复 [访谈结束]。"""

GENERATION_SYSTEM_PROMPT = """你是一个技术文档生成专家。根据以下访谈对话记录，生成两部分内容：

1. 一份结构化的 SKILL.md，包含以下 5 个 section：
   - 角色定义
   - 核心能力
   - 决策链
   - 约束条件
   - 输出规范

2. 一段 JSON，包含 description（一句话描述该 Skill）和 tags（关键词标签列表）。

输出格式要求：
- Markdown 部分用 ---SKILL_MD_START--- 和 ---SKILL_MD_END--- 包裹
- JSON 部分用 ---MANIFEST_JSON_START--- 和 ---MANIFEST_JSON_END--- 包裹

示例：
---SKILL_MD_START---
# skill-name

## 角色定义
...
---SKILL_MD_END---

---MANIFEST_JSON_START---
{"description": "...", "tags": ["tag1", "tag2"]}
---MANIFEST_JSON_END---
"""


def validate_skill_dir(skill_dir: str):
    """校验 skill 目录存在且包含必要文件"""
    if not os.path.isdir(skill_dir):
        print(f"错误: 目录 '{skill_dir}' 不存在")
        sys.exit(1)
    for fname in ("manifest.json", "SKILL.md"):
        if not os.path.isfile(os.path.join(skill_dir, fname)):
            print(f"错误: '{skill_dir}' 中缺少 {fname}")
            sys.exit(1)


def run_interview(client: Anthropic) -> list:
    """运行多轮访谈对话，返回完整 messages 列表"""
    messages = []
    print("\n=== 专家访谈开始 ===")
    print("(输入 quit 或 exit 可随时结束访谈)\n")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=INTERVIEW_SYSTEM_PROMPT,
            messages=messages or [{"role": "user", "content": "请开始访谈。"}],
        )
        assistant_text = response.content[0].text
        messages.append({"role": "assistant", "content": assistant_text})

        # 首轮自动注入启动消息
        if len(messages) == 1:
            messages.insert(0, {"role": "user", "content": "请开始访谈。"})

        print(f"\n专家访谈官: {assistant_text}\n")

        if "[访谈结束]" in assistant_text:
            print("=== 访谈自动结束 ===")
            break

        user_input = input("您的回答: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("=== 访谈手动结束 ===")
            break

        messages.append({"role": "user", "content": user_input})

    return messages

def generate_documents(client: Anthropic, messages: list, skill_dir: str):
    """根据访谈记录生成 SKILL.md 和更新 manifest.json"""
    print("\n正在根据访谈内容生成结构化文档...")

    # 将对话历史格式化为文本
    conversation_text = ""
    for msg in messages:
        role = "专家" if msg["role"] == "user" else "访谈官"
        conversation_text += f"{role}: {msg['content']}\n\n"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=GENERATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"以下是访谈记录：\n\n{conversation_text}"}],
    )
    result_text = response.content[0].text

    # 解析 SKILL.md 内容
    skill_md = parse_between(result_text, "---SKILL_MD_START---", "---SKILL_MD_END---")
    if skill_md:
        path = os.path.join(skill_dir, "SKILL.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(skill_md.strip() + "\n")
        print(f"已更新: {path}")

    # 解析 manifest JSON 片段并合并
    manifest_str = parse_between(result_text, "---MANIFEST_JSON_START---", "---MANIFEST_JSON_END---")
    if manifest_str:
        manifest_path = os.path.join(skill_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        updates = json.loads(manifest_str.strip())
        manifest["description"] = updates.get("description", manifest["description"])
        manifest["tags"] = updates.get("tags", manifest["tags"])
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"已更新: {manifest_path}")

    print("\n文档生成完成！")


def parse_between(text: str, start_marker: str, end_marker: str) -> str | None:
    """提取两个标记之间的内容"""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1:
        return None
    return text[start + len(start_marker):end]


def main():
    parser = argparse.ArgumentParser(description="Skill Maker - 专家访谈器")
    parser.add_argument("--skill-dir", required=True, help="Skill 目录路径")
    args = parser.parse_args()

    skill_dir = os.path.abspath(args.skill_dir)
    validate_skill_dir(skill_dir)

    client = Anthropic()
    messages = run_interview(client)

    if len(messages) >= 2:
        generate_documents(client, messages, skill_dir)
    else:
        print("访谈内容不足，跳过文档生成。")


if __name__ == "__main__":
    main()
