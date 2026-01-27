# GraphRAG + 开源模型演示项目

本项目演示如何使用 **开源模型** (Qwen/Llama) 替代 OpenAI 来运行 Microsoft GraphRAG。

## 核心问题解答

> **Q: Microsoft GraphRAG 可以串接开源模型吗？**
>
> **A: 可以！** GraphRAG 使用 OpenAI 兼容的 API 接口，任何提供相同接口的服务都可以替换，包括：
> - Ollama (本地部署，推荐)
> - vLLM (高性能部署)
> - LMStudio (桌面应用)
> - 各种云端开源模型API

---

## 快速开始 (5分钟)

### Step 1: 安装依赖

```bash
# 安装 GraphRAG
pip install graphrag

# 安装 Ollama (macOS)
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: 下载开源模型

```bash
# 启动 Ollama 服务
ollama serve

# 新开终端，拉取模型
ollama pull qwen2.5:7b           # 中文推荐 (约4GB)
ollama pull nomic-embed-text     # Embedding模型 (约270MB)

# 验证
ollama list
```

### Step 3: 运行演示

```bash
cd demo
python run_demo.py
```

---

## 项目结构

```
demo/
├── README.md                 # 本文件
├── run_demo.py              # 一键运行脚本
├── settings.yaml            # 已配置好的开源模型设置
├── input/                   # 示例文档
│   └── sample_docs.txt
└── prompts/
    └── entity_extraction.txt # 中文优化提示词
```

---

## 关键配置说明

### 原版配置 (OpenAI)

```yaml
llm:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4-turbo
  api_base: https://api.openai.com/v1
```

### 开源模型配置 (Ollama)

```yaml
llm:
  api_key: "ollama"                          # 任意值即可
  model: qwen2.5:7b                          # Ollama模型名
  api_base: http://localhost:11434/v1        # Ollama API地址
```

**就这么简单！只需要改3个值。**

---

## 支持的开源模型

| 模型 | Ollama命令 | 显存需求 | 中文能力 |
|------|-----------|----------|----------|
| Qwen2.5-7B | `ollama pull qwen2.5:7b` | 8GB | 优秀 |
| Qwen2.5-14B | `ollama pull qwen2.5:14b` | 16GB | 优秀 |
| Llama3.1-8B | `ollama pull llama3.1:8b` | 8GB | 一般 |
| Mistral-7B | `ollama pull mistral:7b` | 8GB | 一般 |

**中文场景强烈推荐 Qwen2.5 系列！**

---

## 常见问题

### Q1: Ollama连接失败？
```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果失败，重启
ollama serve
```

### Q2: 显存不足？
```bash
# 使用更小的量化版本
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Q3: 实体提取效果差？
- 使用本项目提供的中文优化提示词
- 调低 temperature 到 0
- 增加 max_tokens

---

## 延伸阅读

- [Microsoft GraphRAG GitHub](https://github.com/microsoft/graphrag)
- [Ollama 官网](https://ollama.ai)
- [Qwen2.5 模型](https://github.com/QwenLM/Qwen2.5)
