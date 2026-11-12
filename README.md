# 第八章实战：食谱 RAG 问答

本仓库提取自 [Datawhale All-in-RAG 第八章](https://github.com/datawhalechina/all-in-rag/tree/cec956e80ae28d6c0ca84c9d39dddcf61ad633fd/docs/chapter8)。`code/C8` 保留原项目的全部源码和依赖清单。原项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)；本仓库添加了本地配置示例、忽略规则和运行说明。

## 本地运行

先在本仓库根目录获取 [HowToCook](https://github.com/Anduin2017/HowToCook) 菜谱数据。下列命令把菜谱放到原代码默认读取的位置；菜谱数据和生成的索引均由 Git 忽略。

```sh
mkdir -p data/C8
recipe_tmp=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse https://github.com/Anduin2017/HowToCook.git "$recipe_tmp/HowToCook"
git -C "$recipe_tmp/HowToCook" sparse-checkout set dishes
cp -R "$recipe_tmp/HowToCook/dishes" data/C8/cook
```

使用 Python 3.12，从本仓库根目录执行：

```sh
cd code/C8
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

在 `code/C8/.env` 填入自己的 `MOONSHOT_API_KEY`，随后在 `code/C8` 运行 `python main.py`。首次运行需要下载嵌入模型并构建索引；生成模型由 `config.py` 配置，如果原教程的模型 ID 已不可用，请换成你账号可用的 Moonshot 模型。
