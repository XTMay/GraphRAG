# GraphRAG 快速入门指南

## 课前准备清单

### 1. 软件环境

```bash
# Python 3.10+ (推荐使用 conda)
conda create -n graphrag python=3.11 -y
conda activate graphrag

# 安装 GraphRAG
pip install graphrag

# 安装 Ollama (macOS)
brew install ollama

# 或下载安装包: https://ollama.ai/download
```

### 2. 模型准备

```bash
# 启动 Ollama 服务
ollama serve

# 拉取所需模型 (新终端窗口)
ollama pull qwen2.5:14b              # 主模型 (约8GB)
ollama pull qwen2.5:7b               # 备选: 较小模型 (约4GB)
ollama pull nomic-embed-text          # Embedding模型

# 验证模型已安装
ollama list
```

### 3. 可选: Neo4j 安装

```bash
# macOS
brew install neo4j

# 或下载 Neo4j Desktop: https://neo4j.com/download/

# 启动 Neo4j
neo4j start
# 默认访问: http://localhost:7474
# 默认密码: neo4j/neo4j (首次需修改)
```

---

## 5分钟快速上手

### Step 1: 创建项目

```bash
# 创建工作目录
mkdir graphrag-demo && cd graphrag-demo

# 初始化项目
python -m graphrag init --root .
```

### Step 2: 配置开源模型

编辑 `settings.yaml`:

```yaml
llm:
  api_key: "ollama"
  type: openai_chat
  model: qwen2.5:14b
  api_base: http://localhost:11434/v1
  temperature: 0
  max_tokens: 4096
  request_timeout: 300

embeddings:
  llm:
    api_key: "ollama"
    type: openai_embedding
    model: nomic-embed-text
    api_base: http://localhost:11434/v1

chunks:
  size: 200
  overlap: 50
```

### Step 3: 准备测试文档

```bash
# 将文档放入 input 目录
# 支持: .txt, .pdf, .md 等格式
cp your_documents.txt ./input/
```

### Step 4: 构建索引

```bash
python -m graphrag index --root .

# 耐心等待，根据文档量可能需要几分钟到几小时
```

### Step 5: 测试查询

```bash
# Global Search - 全局性问题
python -m graphrag query \
    --root . \
    --method global \
    --query "这些文档的主要主题是什么？"

# Local Search - 具体实体问题
python -m graphrag query \
    --root . \
    --method local \
    --query "文档中提到了哪些技术？"
```

---

## 常见问题排查

### 问题1: Ollama 连接失败

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 如果失败，重启 Ollama
ollama serve
```

### 问题2: 显存不足

```bash
# 使用更小的模型
ollama pull qwen2.5:7b

# 或使用量化版本
ollama pull qwen2.5:14b-instruct-q4_K_M
```

### 问题3: 索引构建超时

```yaml
# 在 settings.yaml 中增加超时时间
llm:
  request_timeout: 600  # 10分钟

# 减少并发
  concurrent_requests: 2
```

### 问题4: 中文提取效果差

1. 确保使用 Qwen 系列模型
2. 检查 prompts/entity_extraction.txt 是否为中文提示词
3. 减小 chunk size 到 150-200

---

## 课程资料结构

```
GraphRAG/
├── lecture_notes.md          # 完整讲义
├── quickstart_guide.md       # 本快速指南
└── demo/
    ├── settings.yaml         # 配置模板
    ├── demo_graphrag.py      # 演示脚本
    ├── input/
    │   └── ai_development.txt  # 示例文档
    └── prompts/
        └── entity_extraction.txt  # 中文提示词
```

---

## 运行课程演示

```bash
cd demo
python demo_graphrag.py
```

演示程序提供交互式菜单:
1. 环境检查
2. 项目初始化
3. 准备示例数据
4. 构建索引
5. 执行查询
6. Global vs Local 对比演示

---

## 推荐学习路径

1. **第一步**: 跑通快速上手流程
2. **第二步**: 阅读完整讲义，理解原理
3. **第三步**: 用自己的中文文档测试
4. **第四步**: 调优配置和提示词
5. **第五步**: 完成课后作业

祝学习顺利!
