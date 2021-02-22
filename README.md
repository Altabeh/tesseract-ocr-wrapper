# tesseract-ocr-wrapper
This is a python wrapper for tesseract-ocr. You can use the following code to extract text from a PDF:


```
from utils import ocr_to_text

OCR_CONFIG = {
            "grayscale": "true",
            "user_defined_dpi": "250",
            "oem": "1",
            }

numpage_text_bundle = sorted(
                    [page for page in ocr_to_text(pdf_path, **OCR_CONFIG)],
                    key=lambda x: x[1],
)
ocr_text = "\n".join([page[0] for page in numpage_text_bundle])
```
