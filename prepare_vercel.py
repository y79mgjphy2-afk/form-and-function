"""Prepare browser assets for Vercel's public CDN."""
from pathlib import Path
from shutil import copy2


def main():
    root = Path(__file__).resolve().parent
    target = root / 'public' / 'static'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('app.js', 'style.css'):
        copy2(root / 'static' / name, target / name)


if __name__ == '__main__':
    main()
