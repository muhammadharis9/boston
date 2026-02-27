# AI Post Resizer Website

This project is a basic website that uses an AI-inspired smart crop strategy to create social media post variants from a single uploaded image.

## Features

- Upload 1 image (`png`, `jpg`, `jpeg`, `webp`)
- Automatically generate 3 sizes:
  - Square: `1080 x 1080`
  - Portrait: `1080 x 1350`
  - Story: `1080 x 1920`
- Download each generated image separately
- Download all generated images as a ZIP file

## Run locally

```bash
uv sync
uv run streamlit run main.py
```

Then open the URL shown in your terminal (usually `http://localhost:8501`).

## How AI resizing works

The app uses a lightweight "AI-inspired" approach:

1. It computes the best crop window for each target aspect ratio by scanning candidate regions.
2. It scores each candidate based on visual information (entropy + contrast).
3. It selects the most information-rich crop and resizes it to the final target dimensions.

This keeps important parts of the image more reliably than a fixed center crop.
