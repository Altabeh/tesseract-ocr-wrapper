from utils import ocr_to_text
import platform


# OCR_CONFIG = {
#             "grayscale": "true",
#             "user_defined_dpi": "250",
#             "oem": "1",
#             }

# numpage_text_bundle = sorted(
#                     [page for page in ocr_to_text(r"/mnt/zac/Study/VS_CODE_STUFF/Learningfolders/tesseract_learn/tesseract-ocr-wrapper/EYresume.pdf", **OCR_CONFIG)],
#                     key=lambda x: x[1],
# )
# ocr_text = "\n".join([page[0] for page in numpage_text_bundle])
# print(ocr_text)

print(platform.freedesktop_os_release()['ID_LIKE'])