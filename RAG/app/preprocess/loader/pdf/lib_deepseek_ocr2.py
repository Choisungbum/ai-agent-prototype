import fitz
import os
import torch
from transformers import AutoModel, AutoTokenizer

os.environ["CUDA_VISIBLE_DEVICES"] = ""


def pdf_to_images(pdf_path, out_dir, dpi=150):
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    images = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        path = f"{out_dir}/page_{i+1}.png"
        pix.save(path)
        images.append((i+1, path))
    return images

tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-OCR-2",
    trust_remote_code=True
)

# model = AutoModel.from_pretrained(
#     "deepseek-ai/DeepSeek-OCR-2",
#     trust_remote_code=True,
# ).eval().to("cuda").to(torch.float16)

model = AutoModel.from_pretrained(
    "deepseek-ai/DeepSeek-OCR-2",
    trust_remote_code=True,
).eval().to("cpu")


def ocr2_page(image_path):
    prompt = "<image>\n<|grounding|>Convert the document to markdown."

    return model.infer(
        tokenizer,
        prompt=prompt,
        image_file=image_path,
        base_size=512,
        image_size=512,
        crop_mode=True,
        save_results=False,
    )

def ocr2_pdf(pdf_path):
    pages = pdf_to_images(pdf_path, "images")
    results = []

    for page_num, img in pages:
        print(f"OCR page {page_num}")
        res = ocr2_page(img)
        results.append({
            "page": page_num,
            "raw": res
        })
        torch.cuda.empty_cache()

    return results

pdf_path = '/app/testfile/pdf/test_pdf.pdf'
result = ocr2_pdf(pdf_path)
print(result)