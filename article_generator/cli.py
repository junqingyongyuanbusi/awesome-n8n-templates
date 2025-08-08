import argparse
import os
from rich import print

from .generator import generate_article_html, load_article_data, write_manifest, write_index


def main():
    parser = argparse.ArgumentParser(description="Generate HTML article from reviews and images")
    parser.add_argument("--input", required=True, help="Path to YAML/JSON file with article data")
    parser.add_argument("--images-root", required=True, help="Root directory of images")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--templates", default="/workspace/templates", help="Templates directory")
    parser.add_argument("--assets", default="/workspace/assets", help="Assets directory")
    parser.add_argument("--index", action="store_true", help="Also generate/update index.html")

    args = parser.parse_args()

    out_path = generate_article_html(
        input_path=args.input,
        templates_dir=args.templates,
        assets_dir=args.assets,
        images_root=args.images_root,
        out_dir=args.out,
    )

    data = load_article_data(args.input)
    write_manifest(args.out, data.article)

    if args.index:
        write_index(args.out, templates_dir=args.templates, assets_dir=args.assets)

    print(f"[bold green]Done[/bold green]: {out_path}")


if __name__ == "__main__":
    main()