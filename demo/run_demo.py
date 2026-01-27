#!/usr/bin/env python3
"""
GraphRAG + 开源模型 演示脚本
演示如何用 Ollama + Qwen 替代 OpenAI 运行 GraphRAG
"""

import subprocess
import sys
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"


def print_banner():
    print("""
╔════════════════════════════════════════════════════════════════╗
║         GraphRAG + 开源模型 演示                                ║
║                                                                ║
║  本演示展示如何用 Ollama + Qwen 替代 OpenAI 运行 GraphRAG       ║
╚════════════════════════════════════════════════════════════════╝
    """)


def check_ollama():
    """检查 Ollama 是否运行"""
    print("\n[1/4] 检查 Ollama 服务...")
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"  ✓ Ollama 运行中，已安装 {len(models)} 个模型:")
            for m in models:
                print(f"    - {m['name']}")
            return True
    except Exception as e:
        print(f"  ✗ Ollama 未运行: {e}")
        print("\n  请先启动 Ollama:")
        print("    ollama serve")
        return False


def check_models():
    """检查必要的模型是否已下载"""
    print("\n[2/4] 检查模型...")

    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m['name'] for m in resp.json().get("models", [])]
    except:
        return False

    # 检查 LLM
    llm_options = ['qwen2.5:7b', 'qwen2.5:14b', 'qwen2.5:7b-instruct', 'llama3.1:8b']
    llm_found = None
    for llm in llm_options:
        if any(llm in m for m in models):
            llm_found = llm
            break

    if llm_found:
        print(f"  ✓ LLM模型: {llm_found}")
    else:
        print("  ✗ 未找到LLM模型，请运行:")
        print("    ollama pull qwen2.5:7b")
        return False

    # 检查 Embedding
    embed_options = ['nomic-embed-text', 'bge', 'mxbai-embed']
    embed_found = None
    for emb in embed_options:
        if any(emb in m for m in models):
            embed_found = emb
            break

    if embed_found:
        print(f"  ✓ Embedding模型: {embed_found}")
    else:
        print("  ✗ 未找到Embedding模型，请运行:")
        print("    ollama pull nomic-embed-text")
        return False

    return True


def check_graphrag():
    """检查 GraphRAG 是否安装"""
    print("\n[3/4] 检查 GraphRAG...")
    try:
        import graphrag
        print(f"  ✓ GraphRAG 已安装")
        return True
    except ImportError:
        print("  ✗ GraphRAG 未安装，请运行:")
        print("    pip install graphrag")
        return False


def init_project():
    """初始化 GraphRAG 项目"""
    print("\n[4/4] 初始化项目...")

    # 检查是否已初始化
    if (ROOT_DIR / ".graphrag").exists() or (ROOT_DIR / "output").exists():
        print("  ✓ 项目已初始化")
        return True

    # 创建 input 目录和示例数据
    INPUT_DIR.mkdir(exist_ok=True)

    # 写入示例文档（如果不存在）
    sample_file = INPUT_DIR / "sample_docs.txt"
    if not sample_file.exists():
        sample_file.write_text(SAMPLE_DATA, encoding="utf-8")
        print(f"  ✓ 创建示例文档: {sample_file}")

    print("  ✓ 项目结构准备完成")
    return True


def run_indexing():
    """运行索引构建"""
    print("\n" + "="*60)
    print("开始构建索引 (这可能需要几分钟)")
    print("="*60 + "\n")

    cmd = [sys.executable, "-m", "graphrag", "index", "--root", str(ROOT_DIR)]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✓ 索引构建成功!")
        return True
    else:
        print("\n✗ 索引构建失败")
        return False


def run_query(query: str, method: str = "local"):
    """执行查询"""
    print(f"\n{'='*60}")
    print(f"查询方式: {method.upper()} Search")
    print(f"问题: {query}")
    print("="*60 + "\n")

    cmd = [
        sys.executable, "-m", "graphrag", "query",
        "--root", str(ROOT_DIR),
        "--method", method,
        "--query", query
    ]
    subprocess.run(cmd)


def compare_demo():
    """对比 Global 和 Local Search"""

    queries = [
        ("这些文档的主要内容是什么？请概括总结。", "global", "全局性问题"),
        ("GPT和Transformer有什么关系？", "local", "实体关系问题"),
    ]

    print("\n" + "="*60)
    print("Global Search vs Local Search 对比演示")
    print("="*60)

    for query, recommended, desc in queries:
        print(f"\n▶ 问题类型: {desc}")
        print(f"  问题: {query}")
        print(f"  推荐方法: {recommended.upper()}")

        input("\n按 Enter 继续...")
        run_query(query, recommended)


def main():
    print_banner()

    # 环境检查
    if not check_ollama():
        return
    if not check_models():
        return
    if not check_graphrag():
        return
    if not init_project():
        return

    print("\n" + "="*60)
    print("环境检查通过! 请选择操作:")
    print("="*60)

    while True:
        print("""
选项:
  1. 构建索引 (首次使用需要)
  2. Local Search 查询
  3. Global Search 查询
  4. 对比演示 (展示两种方法的区别)
  5. 查看配置说明
  0. 退出
        """)

        choice = input("请选择 (0-5): ").strip()

        if choice == "0":
            print("再见!")
            break
        elif choice == "1":
            run_indexing()
        elif choice == "2":
            query = input("请输入问题: ")
            run_query(query, "local")
        elif choice == "3":
            query = input("请输入问题: ")
            run_query(query, "global")
        elif choice == "4":
            compare_demo()
        elif choice == "5":
            show_config_guide()
        else:
            print("无效选择")


def show_config_guide():
    """显示配置说明"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    开源模型配置说明                              ║
╚════════════════════════════════════════════════════════════════╝

【核心配置】settings.yaml 中只需修改以下部分:

  原版 (OpenAI):
  ─────────────────────────────────
  llm:
    api_key: sk-xxxxx
    model: gpt-4-turbo
    api_base: https://api.openai.com/v1

  开源版 (Ollama):
  ─────────────────────────────────
  llm:
    api_key: "ollama"                    # 任意值
    model: qwen2.5:7b                    # Ollama模型名
    api_base: http://localhost:11434/v1  # Ollama地址

【支持的模型】

  中文推荐:
    ollama pull qwen2.5:7b      # 8GB显存
    ollama pull qwen2.5:14b     # 16GB显存

  英文推荐:
    ollama pull llama3.1:8b     # 8GB显存

  Embedding:
    ollama pull nomic-embed-text

【其他部署方式】

  vLLM (高性能):
    api_base: http://localhost:8000/v1

  LMStudio:
    api_base: http://localhost:1234/v1

  云端API (如 DeepSeek):
    api_key: your-api-key
    api_base: https://api.deepseek.com/v1
    model: deepseek-chat
""")


# 示例数据
SAMPLE_DATA = """人工智能与大语言模型发展综述

一、人工智能发展历程

人工智能（Artificial Intelligence，AI）是计算机科学的重要分支。1956年，约翰·麦卡锡在达特茅斯会议上首次提出"人工智能"这一术语，标志着AI作为独立学科的诞生。

早期的AI研究主要集中在符号推理和专家系统。MYCIN是早期著名的专家系统，用于医疗诊断。然而由于计算能力限制，AI在1970年代末进入第一次"AI寒冬"。

二、深度学习革命

2012年，杰弗里·辛顿带领的团队使用深度卷积神经网络AlexNet在ImageNet竞赛中取得突破。这一成就重新点燃了业界对神经网络的兴趣。辛顿与Yann LeCun、Yoshua Bengio被誉为"深度学习三巨头"，他们于2018年共同获得图灵奖。

三、Transformer架构的诞生

2017年，谷歌团队发表论文《Attention Is All You Need》，提出Transformer架构。Transformer摒弃了传统的循环神经网络结构，完全基于自注意力机制（Self-Attention），实现了高效的并行计算。

Transformer的核心创新包括：
- 多头注意力机制（Multi-Head Attention）
- 位置编码（Positional Encoding）
- 前馈神经网络层

四、GPT系列的崛起

OpenAI基于Transformer开发了GPT系列模型：

GPT-1（2018年）：首次证明生成式预训练的有效性
GPT-2（2019年）：15亿参数，展示了惊人的文本生成能力
GPT-3（2020年）：1750亿参数，引入了少样本学习能力
GPT-4（2023年）：多模态能力，性能大幅提升

2022年11月，OpenAI发布ChatGPT，基于GPT-3.5，在两个月内用户数突破1亿。

五、开源模型生态

Meta发布Llama系列，推动了开源大模型发展：
- Llama 2：7B/13B/70B三个规格，允许商用
- Llama 3：性能进一步提升

中文模型方面：
- 阿里巴巴的Qwen（通义千问）系列，中文能力出色
- 百度的文心大模型
- 清华的ChatGLM

六、RAG技术

检索增强生成（Retrieval-Augmented Generation，RAG）将信息检索与语言模型结合：
1. 将文档向量化存入向量数据库
2. 查询时检索相关文档
3. 将检索结果与问题一起输入LLM

GraphRAG是微软提出的增强方案，通过构建知识图谱和社区检测，支持全局理解和复杂推理。

七、主要研究机构

- OpenAI（美国）：GPT系列、ChatGPT
- DeepMind（英国/谷歌）：AlphaGo、Gemini
- Meta AI Research：Llama系列
- 阿里达摩院：通义千问
- 百度研究院：文心大模型
"""


if __name__ == "__main__":
    main()
