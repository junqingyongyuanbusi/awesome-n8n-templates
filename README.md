# 自动化：根据评价和图片生成 HTML 文章

## 快速开始

1) 安装依赖

```bash
python3 -m venv /workspace/.venv
source /workspace/.venv/bin/activate
pip install -r /workspace/requirements.txt
```

2) 生成示例文章

```bash
python -m article_generator.cli \
  --input /workspace/data/sample_article.yaml \
  --images-root /workspace/data/images \
  --out /workspace/out
```

生成后查看：`/workspace/out/product-x-review.html`，以及索引页：`/workspace/out/index.html`。

## 输入数据格式（YAML/JSON 二选一）

```yaml
article:
  title: 产品X 真实体验评测
  slug: product-x-review
  description: 对产品X的主观体验与客观表现的汇总
  date: 2025-08-08
  hero_image: hero.jpg  # 可选
  tags: [产品X, 评测]
  cover_credit: 摄影：张三

gallery_dir: gallery/product-x  # 相对 images_root 的路径，可选

reviews:
  - author: 张三
    rating: 4.5
    date: 2025-08-01
    content: |
      这是一段详细的评价……
    pros: [做工精致, 电池续航长]
    cons: [价格略高]
    images: [detail1.jpg, detail2.jpg]
  - author: 李四
    rating: 4.0
    date: 2025-08-02
    content: 电池给力，音质中规中矩
    pros: [续航, 便携]
    cons: []
    images: []
```

- `images-root`：图片根目录（CLI 参数）。YAML 中的 `hero_image`、`reviews[].images[]`、`gallery_dir` 都是相对该目录的路径。
- 未提供的图片会被跳过并打印提示，不会影响生成。

## 目录结构
- `article_generator/`：生成逻辑与 CLI
- `templates/`：Jinja2 模板（`base.html.j2`、`article.html.j2`、`index.html.j2`）
- `assets/`：静态资源（`styles.css`）
- `data/`：示例数据与图片
- `out/`：输出目录（自动生成）

## 命令参数
```bash
python -m article_generator.cli \
  --input <YAML_or_JSON_file> \
  --images-root <images_root_dir> \
  --out <output_dir> \
  [--index]  # 生成/更新索引页
```

- `--input`：一个文章数据文件（YAML/JSON）。
- `--images-root`：图片根目录。
- `--out`：输出目录。
- `--index`：可选。生成/更新 `index.html`（可多次运行合并）。

## 说明
- 不依赖你现有的 demo.json；这里采用通用的输入格式，可直接替换为你的真实数据。
- 模板和样式可根据需求自定义（如品牌色、布局等）。