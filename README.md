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
