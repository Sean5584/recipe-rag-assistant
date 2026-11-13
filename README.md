# 食谱 RAG 助手

在终端里询问一道菜需要哪些食材、用量是多少，或者怎么做。助手会从 HowToCook 菜谱中检索相关内容，再用 Kimi 生成回答。比如：

> 西红柿炒鸡蛋需要什么食材？

菜谱和向量索引保存在本地。程序使用 FAISS 和 BM25 组合检索，并把相关菜谱内容交给 Moonshot API 生成回答。

## 本地运行

需要 Python 3.12、Git 和可调用 Kimi 的 Moonshot API Key。以下命令从项目根目录执行。

### 1. 准备菜谱

首次运行时下载 HowToCook 的菜谱。已有 `data/recipes/` 时可以跳过这一步。

```sh
recipe_tmp=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse https://github.com/Anduin2017/HowToCook.git "$recipe_tmp/HowToCook"
git -C "$recipe_tmp/HowToCook" sparse-checkout set dishes
mkdir -p data
cp -R "$recipe_tmp/HowToCook/dishes" data/recipes
cp "$recipe_tmp/HowToCook/LICENSE" data/recipes/HowToCook-LICENSE
```

### 2. 配置环境

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements.txt
cp -n app/.env.example app/.env
```

已有装好依赖的 Python 3.12 环境时，可以直接激活该环境。把 `MOONSHOT_API_KEY` 填在 `app/.env` 中。Git 会忽略该文件、菜谱和生成的索引。

### 3. 启动问答

```sh
python app/main.py
```

首次启动会下载嵌入模型并构建索引，后续会读取 `app/vector_index/citations-v1/` 中的缓存。旧索引缺少引用所需的元数据，升级后会自动重建一次。出现「您的问题」后输入菜谱问题，输入「退出」结束。

程序校验引用后再一次性显示答案。每条事实后有编号，来源区列出菜谱相对路径、章节、片段 ID 和对应原文。问题明确写出完整菜名时，优先使用对应菜谱；其他问题使用混合检索。同一问题只有部分内容能从原文确认时，会分别展示有依据的回答和缺少的信息。

默认生成模型为 `kimi-k2.6`。模型和生成参数可以在 `app/config.py` 修改。如果遇到 `429`，请稍后再问；一次问答可能需要多次 API 请求。

## 来源与许可

- 项目代码基于 [Datawhale All-in-RAG 的菜谱问答示例](https://github.com/datawhalechina/all-in-rag/tree/cec956e80ae28d6c0ca84c9d39dddcf61ad633fd/code/C8)，原项目使用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。
- 菜谱来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)，适用其仓库中的 [许可证](https://github.com/Anduin2017/HowToCook/blob/master/LICENSE)。

## 分块检索对照实验

从项目根目录运行（需要已准备菜谱和 Python 依赖，无需 Moonshot API Key）：

```sh
python app/compare_chunking.py --k 3 --size 400 --overlap 80 > chunking-results.json
```

脚本用相同语料、BGE 嵌入模型、问题和 top-k，对比 Markdown 标题分块与固定字符窗口分块（默认 400 字符、重叠 80 字符）。两者独立构建内存索引，只做向量相似度检索，不使用菜名直达、BM25、查询改写或 LLM 生成；日常问答仍使用原有 Markdown 索引。

- **文档 Hit@k**：前 k 个片段中至少一个来自标注菜谱。
- **证据 Hit@k**：前 k 个片段中至少一个来自标注菜谱，并在忽略空白后包含完整的标注原文。跨片段才能拼齐的证据不算命中。

默认使用 `experiments/retrieval_pilot.json` 的 8 道试验题，每题含参考答案、来源路径和证据。JSON 输出包含总体统计和逐题结果。可用 `--questions` 指定同格式的题集。试验题用于检查实验流程，正式评测还需至少 20 组问答及答案正确率。

## 正式评测：20 道可回答题和 4 道拒答题

`experiments/qa_benchmark.json` 含试验题及新增题。可回答题标有参考答案、菜谱路径和证据；拒答题不纳入检索命中率的分母。由于这 20 道题包含前期看过的 8 道试验题，它们不是独立留出的测试集，报告中应说明。

```sh
python app/compare_chunking.py --questions experiments/qa_benchmark.json > chunking-results.json
python app/evaluate_answers.py collect --results answer-eval-results.json
```

第一条命令比较两种分块的纯向量检索，第二条命令调用实际问答流程（包括完整菜名定位或混合检索），需要自己的 Moonshot API Key。采集默认在题目之间等待 61 秒以避开限流；可以用 `--limit 2` 先试两题。遇到限流时等一分钟后重跑同一命令，已有结果会保留，程序从下一题继续。不要在采集中同时运行交互问答。

打开 `answer-eval-results.json`，逐题对比 `actual`、参考答案和原文，把 `correct` 从 `null` 改为 `true` 或 `false`：

- 可回答题：关键事实、数量和单位正确，没有额外的无依据断言，并且引用的原文支持该答案，才标为正确。等价表述可以接受。
- 拒答题：明确说明知识库未提供所问信息且没有猜测，才标为正确。API 错误或「未能生成可核验的回答」不算正确拒答。

```sh
python app/evaluate_answers.py score --results answer-eval-results.json
```

脚本分别报告答案正确率和拒答正确率。未判完的分组只显示进度。两类结果文件默认由 Git 忽略，报告可另行记录最终统计。
