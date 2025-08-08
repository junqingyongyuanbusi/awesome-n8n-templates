import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import datetime

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich import print


@dataclass
class Review:
    author: str
    rating: Optional[float] = None
    date: Optional[str] = None
    content: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)


@dataclass
class ArticleMeta:
    title: str
    slug: str
    description: Optional[str] = None
    date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    hero_image: Optional[str] = None
    cover_credit: Optional[str] = None


@dataclass
class ArticleData:
    article: ArticleMeta
    reviews: List[Review]
    gallery_dir: Optional[str] = None


class ArticleGenerator:
    def __init__(self, templates_dir: str, assets_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=False,
        )
        self.assets_dir = assets_dir

    def _load_styles(self) -> str:
        css_path = os.path.join(self.assets_dir, "styles.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def render_article(self, data: ArticleData, images_root: str) -> str:
        template = self.env.get_template("article.html.j2")
        styles = self._load_styles()

        # Validate and resolve image paths
        def resolve_image(path: Optional[str]) -> Optional[str]:
            if not path:
                return None
            full = os.path.join(images_root, path)
            if os.path.exists(full):
                return os.path.relpath(full, images_root)
            print(f"[yellow]Warn:[/yellow] missing image {full}")
            return None

        hero_image = resolve_image(data.article.hero_image)

        gallery_images: List[str] = []
        if data.gallery_dir:
            gallery_abs = os.path.join(images_root, data.gallery_dir)
            if os.path.isdir(gallery_abs):
                for name in sorted(os.listdir(gallery_abs)):
                    if name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        gallery_images.append(os.path.relpath(os.path.join(gallery_abs, name), images_root))

        for review in data.reviews:
            review.images = [p for p in (resolve_image(p) for p in review.images) if p]

        html = template.render(
            styles=styles,
            article=data.article,
            hero_image=hero_image,
            gallery_images=gallery_images,
            reviews=data.reviews,
        )
        return html

    def render_index(self, articles: List[ArticleMeta]) -> str:
        template = self.env.get_template("index.html.j2")
        styles = self._load_styles()
        return template.render(styles=styles, articles=articles)


# Public API

def _to_str_if_date(value: Any) -> Any:
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def load_article_data(file_path: str) -> ArticleData:
    with open(file_path, "r", encoding="utf-8") as f:
        if file_path.lower().endswith((".yaml", ".yml")):
            raw: Dict[str, Any] = yaml.safe_load(f)
        else:
            raw = json.load(f)

    art_raw = dict(raw["article"])  # type: ignore[index]
    # normalize date and tags
    if "date" in art_raw and art_raw["date"] is not None:
        art_raw["date"] = str(_to_str_if_date(art_raw["date"]))
    if "tags" in art_raw and art_raw["tags"] is not None:
        art_raw["tags"] = [str(t) for t in art_raw["tags"]]

    article_meta = ArticleMeta(**art_raw)  # type: ignore[arg-type]

    reviews: List[Review] = []
    for r in raw.get("reviews", []):
        r = dict(r)
        if "date" in r and r["date"] is not None:
            r["date"] = str(_to_str_if_date(r["date"]))
        if "rating" in r and r["rating"] is not None:
            try:
                r["rating"] = float(r["rating"])
            except Exception:
                r["rating"] = None
        if "pros" in r and r["pros"] is not None:
            r["pros"] = [str(p) for p in r["pros"]]
        if "cons" in r and r["cons"] is not None:
            r["cons"] = [str(c) for c in r["cons"]]
        reviews.append(Review(**r))

    gallery_dir = raw.get("gallery_dir")
    return ArticleData(article=article_meta, reviews=reviews, gallery_dir=gallery_dir)


def generate_article_html(input_path: str, templates_dir: str, assets_dir: str, images_root: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    data = load_article_data(input_path)
    generator = ArticleGenerator(templates_dir=templates_dir, assets_dir=assets_dir)
    html = generator.render_article(data, images_root=images_root)
    out_path = os.path.join(out_dir, f"{data.article.slug}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[green]Generated[/green] {out_path}")
    return out_path


def write_index(out_dir: str, templates_dir: str, assets_dir: str):
    # collect existing article *.html and infer minimal meta from sibling manifest.json if exists
    articles: List[ArticleMeta] = []

    manifest_path = os.path.join(out_dir, "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                stored = json.load(f)
                for item in stored:
                    articles.append(ArticleMeta(**item))
        except Exception:
            print("[yellow]Warn:[/yellow] unable to parse manifest.json, will rebuild if possible")

    # If no manifest, try to fallback by reading front-matter sidecars .meta.json
    if not articles:
        for name in os.listdir(out_dir):
            if name.endswith(".meta.json"):
                with open(os.path.join(out_dir, name), "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    try:
                        articles.append(ArticleMeta(**meta))
                    except TypeError:
                        pass

    generator = ArticleGenerator(templates_dir=templates_dir, assets_dir=assets_dir)
    html = generator.render_index(articles)
    index_path = os.path.join(out_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[green]Updated[/green] {index_path}")


def write_manifest(out_dir: str, article_meta: ArticleMeta):
    manifest_path = os.path.join(out_dir, "manifest.json")
    items: List[Dict[str, Any]] = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            items = []
    # upsert by slug
    filtered = [i for i in items if i.get("slug") != article_meta.slug]
    filtered.append({
        "title": article_meta.title,
        "slug": article_meta.slug,
        "description": article_meta.description,
        "date": str(article_meta.date) if article_meta.date is not None else None,
        "tags": article_meta.tags,
    })
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    sidecar = os.path.join(out_dir, f"{article_meta.slug}.meta.json")
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump({
            "title": article_meta.title,
            "slug": article_meta.slug,
            "description": article_meta.description,
            "date": str(article_meta.date) if article_meta.date is not None else None,
            "tags": article_meta.tags,
        }, f, ensure_ascii=False, indent=2)