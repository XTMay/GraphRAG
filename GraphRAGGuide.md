# GraphRAG 教学讲解

## 一、为什么需要 GraphRAG

在传统 RAG（Retrieval-Augmented Generation）中，我们的核心流程是：

1. 文档切分（Chunking）
2. 向量化（Embedding）
3. 向量检索（Top-K 相似度搜索）
4. 将检索结果作为上下文交给 LLM 生成答案

**问题在于：**

* 文档被切碎后，结构信息丢失
* 实体之间的关系（谁属于谁、因果、时间顺序）无法表达
* 多跳推理（Multi-hop Reasoning）能力弱

GraphRAG 的核心目标是：

> 在“语义相似度检索”之上，引入“结构化关系推理”。

---

## 二、GraphRAG 的核心思想

GraphRAG = **Knowledge Graph + RAG + LLM**

它不是用“向量”替代“图”，而是：

* 向量负责：**找到相关内容**
* 图结构负责：**组织、连接、推理内容**

一句话总结：

> RAG 负责“找得到”，Graph 负责“想得通”。

---

## 三、GraphRAG 的整体流程（概念级）

1. 原始数据输入（PDF / 文档 / 代码 / 网页）
2. 信息抽取（实体、关系、事件）
3. 构建知识图谱（Graph）
4. 向量化（实体 / 文本 / 子图）
5. 查询阶段：

   * 向量召回相关节点
   * 图遍历 / 子图扩展
6. 构建 Prompt（Graph-aware Context）
7. LLM 生成答案

---

## 四、GraphRAG 的关键组成模块

### 1. 实体抽取（Entity Extraction）

常见实体类型：

* 人（Person）
* 组织（Organization）
* 产品 / 技术（Product / Technology）
* 概念（Concept）
* 事件（Event）

示例：

> “GraphRAG 由 Microsoft Research 提出”

* 实体：GraphRAG / Microsoft Research
* 关系：developed_by

实体抽取通常由 LLM 完成。

---

### 2. 关系抽取（Relation Extraction）

关系是 GraphRAG 的灵魂。

常见关系类型：

* is_a
* part_of
* developed_by
* depends_on
* causes
* used_for

示例：

```
(GraphRAG) -[extends]-> (RAG)
(RAG) -[uses]-> (Vector Database)
```

---

### 3. 知识图谱存储（Graph Store）

常见存储方式：

* Neo4j（最常见，教学友好）
* ArangoDB
* TigerGraph
* NetworkX（教学 / 小规模）

图中包含：

* Node（实体）
* Edge（关系）
* Properties（元数据）

---

### 4. 向量数据库（Vector Store）

GraphRAG **并不会抛弃向量检索**。

向量可以来自：

* 文本 chunk
* 实体描述
* 子图摘要（Graph Summary）

常见工具：

* FAISS
* Milvus
* Qdrant
* Chroma

---

## 五、查询阶段：GraphRAG 如何回答问题

以问题为例：

> “GraphRAG 和传统 RAG 的主要区别是什么？”

### Step 1：向量召回

* 使用 Query Embedding
* 找到最相关的实体 / 文本节点

### Step 2：图扩展（Graph Traversal）

* 从命中节点出发
* 扩展 1~2 跳关系
* 构建子图（Subgraph）

### Step 3：子图摘要（可选）

* 将子图压缩成 LLM 可读文本

### Step 4：Graph-aware Prompt

Prompt 中包含：

* 核心实体
* 关键关系
* 结构化事实

---

## 六、GraphRAG vs 传统 RAG（课堂对比）

| 维度    | 传统 RAG | GraphRAG |
| ----- | ------ | -------- |
| 数据结构  | 文本块    | 图结构 + 文本 |
| 关系建模  | 隐式     | 显式       |
| 多跳推理  | 弱      | 强        |
| 可解释性  | 低      | 高        |
| 实现复杂度 | 低      | 高        |

---

## 七、主流 GraphRAG 框架与工具

### 1. Microsoft GraphRAG

* 官方提出
* 强调：Entity-centric + Community Detection
* 适合研究 / 企业级知识库

### 2. LlamaIndex GraphRAG

* 上手最简单
* 支持 Neo4j / NetworkX
* 非常适合教学演示

### 3. LangChain + Knowledge Graph

* 高自由度
* 需要自己设计 schema
* 更偏工程实践

### 4. Neo4j + LLM

* 图数据库原生优势
* Cypher + LLM 结合

---

## 八、什么时候该用 GraphRAG

**适合：**

* 企业知识库
* 技术文档体系
* 法律 / 医疗 / 金融
* 需要可解释推理的系统

**不适合：**

* 小规模 FAQ
* 简单语义搜索
* 快速 MVP

---
> GraphRAG 不是“更聪明的搜索”，而是“让模型开始理解世界结构”。

这是从「语义相似」走向「结构化推理」的重要一步。
