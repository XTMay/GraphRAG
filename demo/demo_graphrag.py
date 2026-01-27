#!/usr/bin/env python3
"""
GraphRAG 演示脚本
用于课程教学演示 GraphRAG 的基本使用流程
"""

import asyncio
import os
import sys
from pathlib import Path

# ============================================================
#                     1. 环境检查
# ============================================================

def check_environment():
    """检查运行环境是否满足要求"""
    print("=" * 60)
    print("GraphRAG 环境检查")
    print("=" * 60)

    # 检查Python版本
    py_version = sys.version_info
    print(f"Python版本: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 10):
        print("警告: 建议使用 Python 3.10+")

    # 检查graphrag是否安装
    try:
        import graphrag
        print(f"GraphRAG: 已安装")
    except ImportError:
        print("GraphRAG: 未安装")
        print("请运行: pip install graphrag")
        return False

    # 检查ollama是否运行
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"Ollama: 运行中 (已安装 {len(models)} 个模型)")
            for model in models[:5]:  # 只显示前5个
                print(f"  - {model['name']}")
        else:
            print("Ollama: 未响应")
            return False
    except Exception as e:
        print(f"Ollama: 连接失败 ({e})")
        print("请确保Ollama正在运行: ollama serve")
        return False

    print("=" * 60)
    return True


# ============================================================
#                     2. 项目初始化
# ============================================================

def init_project(root_dir: str = "./ragtest"):
    """初始化GraphRAG项目"""
    import subprocess

    root_path = Path(root_dir)

    # 创建目录结构
    (root_path / "input").mkdir(parents=True, exist_ok=True)

    # 检查是否已初始化
    if (root_path / "settings.yaml").exists():
        print(f"项目已存在于 {root_dir}")
        return root_path

    # 运行graphrag init
    print(f"正在初始化项目于 {root_dir}...")
    result = subprocess.run(
        ["python", "-m", "graphrag", "init", "--root", root_dir],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("项目初始化成功!")
    else:
        print(f"初始化失败: {result.stderr}")

    return root_path


# ============================================================
#                     3. 准备示例数据
# ============================================================

SAMPLE_DOCUMENTS = [
    {
        "filename": "ai_history.txt",
        "content": """人工智能发展简史

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。

1956年，约翰·麦卡锡在达特茅斯会议上首次提出"人工智能"这一术语。这次会议被认为是人工智能作为独立学科的开端。艾伦·图灵、马文·明斯基等先驱也参与了早期AI研究。

2012年，深度学习迎来重大突破。杰弗里·辛顿带领的团队使用深度卷积神经网络AlexNet在ImageNet图像识别竞赛中取得革命性成果。这一突破标志着深度学习时代的到来，神经网络重新成为AI研究的核心。

2017年，谷歌团队发表了具有里程碑意义的论文《Attention Is All You Need》，提出了Transformer架构。这一架构摒弃了传统的循环神经网络，完全基于自注意力机制，大大提高了并行计算效率。

2022年11月，OpenAI发布了ChatGPT，这是一个基于GPT-3.5的对话系统。ChatGPT展现了惊人的语言理解和生成能力，发布两个月内用户数突破1亿，成为历史上增长最快的消费者应用。

2023年，大型语言模型百花齐放。Meta发布了开源的Llama系列模型；阿里巴巴推出通义千问（Qwen）；百度发布文心一言。OpenAI则推出了GPT-4，在多项基准测试中展现了超越GPT-3.5的能力。

2024年，多模态AI成为新趋势。OpenAI的GPT-4V、谷歌的Gemini、Anthropic的Claude都具备了图像理解能力。AI Agent和RAG（检索增强生成）技术也得到广泛应用。"""
    },
    {
        "filename": "llm_tech.txt",
        "content": """大型语言模型技术解析

大型语言模型（Large Language Model，LLM）是一类基于深度学习的自然语言处理模型，通过在海量文本数据上训练来学习语言的统计规律。

Transformer架构是现代LLM的基础。由Vaswani等人于2017年提出，其核心是自注意力机制（Self-Attention），允许模型在处理序列时直接关注任意位置的信息，解决了RNN的长程依赖问题。

GPT系列是OpenAI开发的代表性LLM。GPT使用仅解码器（Decoder-only）架构，通过自回归方式生成文本。GPT-3拥有1750亿参数，GPT-4则采用了混合专家（MoE）架构，性能进一步提升。

BERT是谷歌开发的双向语言模型，使用掩码语言建模（MLM）进行预训练，适合理解类任务。BERT启发了后续众多模型如RoBERTa、ALBERT等。

开源模型方面，Meta的Llama系列影响深远。Llama 2提供7B、13B、70B三个规格，允许商用。Llama 3进一步提升了性能，8B和70B版本在多项基准上超越了同规模的其他开源模型。

中文LLM领域，阿里的Qwen（通义千问）表现突出。Qwen2.5系列提供0.5B到72B多个规格，在中文理解和生成方面表现优异，支持32K上下文长度。清华的ChatGLM、百度的文心大模型也是重要的中文LLM。

模型优化技术包括：量化（Quantization）可将模型压缩至4-bit，显著减少显存占用；LoRA（Low-Rank Adaptation）实现高效微调；Flash Attention优化注意力计算效率。"""
    },
    {
        "filename": "rag_intro.txt",
        "content": """检索增强生成技术详解

检索增强生成（Retrieval-Augmented Generation，RAG）是一种将信息检索与语言模型生成相结合的技术，旨在解决LLM的知识更新和幻觉问题。

传统RAG的工作流程包括三个阶段：首先，将文档切分成chunks并使用embedding模型转换为向量；然后，将向量存入向量数据库如Milvus、Pinecone、Chroma等；查询时，将用户问题同样转换为向量，检索相似的文档chunks，最后将检索结果与问题一起输入LLM生成答案。

RAG的核心优势在于：知识可更新，无需重新训练模型；答案可溯源，便于验证；减少幻觉，基于真实文档生成。

然而传统RAG存在局限：难以理解全局信息，无法回答"这些文档的主要主题是什么"类问题；多跳推理困难，当答案需要综合多个文档的信息时效果不佳；关系理解弱，难以处理实体间复杂关系。

GraphRAG是微软提出的增强方案。它在传统RAG基础上引入知识图谱，通过实体关系提取构建图结构，使用社区检测算法发现主题聚类，并为每个社区生成摘要。查询时，GraphRAG提供两种模式：Global Search利用社区摘要回答全局性问题；Local Search通过实体检索和图遍历回答具体问题。

向量数据库是RAG的重要组件。Milvus由Zilliz开发，支持万亿级向量；Qdrant使用Rust开发，性能优异；Chroma轻量易用，适合原型开发；Pinecone是托管服务，免运维。

embedding模型方面，OpenAI的text-embedding-3系列是常用选择；开源方案中，BGE系列在中文场景表现出色，bge-large-zh-v1.5是中文embedding的优选。"""
    }
]


def prepare_sample_data(root_dir: str = "./ragtest"):
    """准备示例数据"""
    input_dir = Path(root_dir) / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    print("正在准备示例数据...")
    for doc in SAMPLE_DOCUMENTS:
        file_path = input_dir / doc["filename"]
        file_path.write_text(doc["content"], encoding="utf-8")
        print(f"  已创建: {file_path}")

    print(f"共创建 {len(SAMPLE_DOCUMENTS)} 个示例文档")


# ============================================================
#                     4. 运行索引构建
# ============================================================

def run_indexing(root_dir: str = "./ragtest"):
    """运行索引构建"""
    import subprocess

    print("=" * 60)
    print("开始构建索引 (这可能需要几分钟)")
    print("=" * 60)

    result = subprocess.run(
        ["python", "-m", "graphrag", "index", "--root", root_dir],
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print("索引构建成功!")
    else:
        print("索引构建过程中出现问题，请检查日志")


# ============================================================
#                     5. 执行查询
# ============================================================

def run_query(root_dir: str, query: str, method: str = "local"):
    """执行查询"""
    import subprocess

    print("=" * 60)
    print(f"执行 {method.upper()} 查询")
    print(f"问题: {query}")
    print("=" * 60)

    result = subprocess.run(
        ["python", "-m", "graphrag", "query",
         "--root", root_dir,
         "--method", method,
         "--query", query],
        capture_output=True,
        text=True
    )

    print("\n查询结果:")
    print("-" * 40)
    print(result.stdout)

    if result.stderr:
        print("\n错误信息:")
        print(result.stderr)


# ============================================================
#                     6. 对比演示
# ============================================================

def compare_search_methods(root_dir: str = "./ragtest"):
    """对比 Global Search 和 Local Search"""

    queries = [
        {
            "query": "这些文档的主要主题是什么？请总结核心内容。",
            "description": "全局性问题 - 需要理解整体",
            "recommended": "global"
        },
        {
            "query": "GPT系列模型有哪些？它们之间有什么关系？",
            "description": "实体关系问题 - 需要理解实体间联系",
            "recommended": "local"
        },
        {
            "query": "Transformer架构是什么？由谁提出的？",
            "description": "具体事实问题 - 针对特定实体",
            "recommended": "local"
        },
        {
            "query": "人工智能领域的主要发展阶段有哪些？",
            "description": "综合分析问题 - 需要全局视角",
            "recommended": "global"
        }
    ]

    print("\n" + "=" * 60)
    print("Global Search vs Local Search 对比演示")
    print("=" * 60)

    for i, q in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"问题 {i}: {q['query']}")
        print(f"类型: {q['description']}")
        print(f"推荐方法: {q['recommended'].upper()}")
        print("=" * 60)

        # 先运行推荐的方法
        print(f"\n--- 使用 {q['recommended'].upper()} Search ---")
        run_query(root_dir, q['query'], q['recommended'])

        # 询问是否对比另一种方法
        print(f"\n按 Enter 查看另一种方法的结果，或输入 'skip' 跳过...")
        user_input = input()
        if user_input.lower() != 'skip':
            other_method = "global" if q['recommended'] == "local" else "local"
            print(f"\n--- 使用 {other_method.upper()} Search ---")
            run_query(root_dir, q['query'], other_method)


# ============================================================
#                     7. 主函数
# ============================================================

def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              GraphRAG 课程演示程序                        ║
    ║                                                          ║
    ║  1. 检查环境                                             ║
    ║  2. 初始化项目                                           ║
    ║  3. 准备示例数据                                         ║
    ║  4. 构建索引                                             ║
    ║  5. 执行查询                                             ║
    ║  6. 对比演示                                             ║
    ║  0. 退出                                                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    root_dir = "./ragtest"

    while True:
        choice = input("\n请选择操作 (1-6, 0退出): ").strip()

        if choice == "0":
            print("再见!")
            break
        elif choice == "1":
            check_environment()
        elif choice == "2":
            init_project(root_dir)
        elif choice == "3":
            prepare_sample_data(root_dir)
        elif choice == "4":
            run_indexing(root_dir)
        elif choice == "5":
            query = input("请输入查询问题: ")
            method = input("选择查询方法 (local/global): ").strip().lower()
            if method not in ["local", "global"]:
                method = "local"
            run_query(root_dir, query, method)
        elif choice == "6":
            compare_search_methods(root_dir)
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    main()
