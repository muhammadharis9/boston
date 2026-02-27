import io
import zipfile
from dataclasses import dataclass

import numpy as np
import streamlit as st
from PIL import Image


@dataclass(frozen=True)
class PostSize:
    name: str
    width: int
    height: int


POST_SIZES = [
    PostSize("Square", 1080, 1080),
    PostSize("Portrait", 1080, 1350),
    PostSize("Story", 1080, 1920),
]


def _score_crop(gray_arr: np.ndarray) -> float:
    """Entropy-like score for a crop, favoring information-rich areas."""
    hist, _ = np.histogram(gray_arr, bins=32, range=(0, 255), density=True)
    hist = hist[hist > 0]
    entropy = -np.sum(hist * np.log2(hist))
    contrast = float(gray_arr.std())
    return float(entropy + 0.01 * contrast)


def smart_crop_resize(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """AI-inspired crop selection using a simple entropy scan, then resize."""
    rgb_img = image.convert("RGB")
    src_w, src_h = rgb_img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = int(crop_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(crop_w / target_ratio)

    # Fast path when crop equals source.
    if crop_w == src_w and crop_h == src_h:
        return rgb_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    gray = np.array(rgb_img.convert("L"))

    # Search along the long axis for the highest-information crop region.
    if src_ratio > target_ratio:
        max_offset = src_w - crop_w
        offsets = np.linspace(0, max_offset, num=min(25, max_offset + 1), dtype=int)
        best_x = 0
        best_score = float("-inf")
        for x in offsets:
            crop = gray[:, x : x + crop_w]
            score = _score_crop(crop)
            if score > best_score:
                best_score = score
                best_x = x
        cropped = rgb_img.crop((best_x, 0, best_x + crop_w, crop_h))
    else:
        max_offset = src_h - crop_h
        offsets = np.linspace(0, max_offset, num=min(25, max_offset + 1), dtype=int)
        best_y = 0
        best_score = float("-inf")
        for y in offsets:
            crop = gray[y : y + crop_h, :]
            score = _score_crop(crop)
            if score > best_score:
                best_score = score
                best_y = y
        cropped = rgb_img.crop((0, best_y, crop_w, best_y + crop_h))

    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def build_zip(images: dict[str, Image.Image]) -> bytes:
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for label, img in images.items():
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            zf.writestr(f"{label.lower()}.png", buffer.getvalue())
    memory_file.seek(0)
    return memory_file.getvalue()


def main() -> None:
    st.set_page_config(page_title="AI Post Resizer", page_icon="🖼️", layout="wide")
    st.title("🖼️ AI Post Resizer")
    st.write(
        "Upload one image and generate 3 social-media-ready sizes using "
        "an AI-inspired smart crop."
    )

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("Add an image to generate resized posts.")
        return

    image = Image.open(uploaded)
    st.subheader("Original")
    st.image(image, use_container_width=True)

    results: dict[str, Image.Image] = {}
    st.subheader("Generated sizes")
    cols = st.columns(3)

    for idx, post_size in enumerate(POST_SIZES):
        resized = smart_crop_resize(image, post_size.width, post_size.height)
        label = f"{post_size.name}_{post_size.width}x{post_size.height}"
        results[label] = resized
        with cols[idx]:
            st.image(resized, caption=label, use_container_width=True)
            img_bytes = io.BytesIO()
            resized.save(img_bytes, format="PNG")
            st.download_button(
                label=f"Download {post_size.name}",
                data=img_bytes.getvalue(),
                file_name=f"{label.lower()}.png",
                mime="image/png",
                use_container_width=True,
            )

    zip_data = build_zip(results)
    st.download_button(
        label="Download all as ZIP",
        data=zip_data,
        file_name="resized_posts.zip",
        mime="application/zip",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
