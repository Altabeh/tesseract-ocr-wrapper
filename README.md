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

Unlike [pytesseract](https://pypi.org/project/pytesseract/), there are two main advantages of the function `ocr_to_text` above
that make it perfect for extracting text from multiple PDFs.

* It is fully parallelized using `ProcessPoolExecutor` of the `concurrent.futures` module. `ocr_to_text` yields
a list of tuples where the first element of each tuple is the page text and the second element is the page number. In a real implementation of multiprocessing, we don't have to wait for all the tasks to yield the results. Likewise, the text extraction from each page is submitted as a task over to the multiprocessing pool that will then be returned without having to wait until all the tasks are completed. So we need the page numbers later to sort the results in ascending order (`key=lambda x: x[1]`).

* There is a severe memory issue in pytesseract stemming from the fact that it keeps dumping everything in RAM across possibly many iterations over the pages of a PDF file without controlled garbage collection. Here, however, every page is converted to an image sitting in a `TemporaryDirectory()` that is cleaned up and removed from the filesystem on completion of extraction. This leads to the release of the unused data every time we iterate over a single page of a PDF file that significantly reduces the memory usage not only for a single file, and therefore across thousands of PDF files. 


# Requirements

After cloning the repo, go to the directory `tesseract-ocr-wrapper` and then type
```
$ pip install -r requirements.txt
```
to download and install the required python packages. There are many other packages such as [leptonica](https://github.com/DanBloomberg/leptonica) and [poppler-utils](https://www.mankier.com/package/poppler-utils) that need to be installed.
Since these packages are system dependent, I have included a `_sys.py` file that allows you 
to directly download and install them if you are on Linux. For all other operating systems, you can modify this file, in particular the commands listed in `_sys.py` i.e.

```
commands = [
            "sudo yum install poppler-utils",
            "sudo yum install autoconf automake libpng-devel libtiff-devel libtool pkgconfig.x86_64 libpng12-devel.x86_64 libjpeg-devel libtiff-devel.x86_64 zlib-devel.x86_64",
            "cd /tmp",
            "wget http://www.leptonica.org/source/leptonica-1.79.0.tar.gz",
            "tar -zxvf leptonica-1.79.0.tar.gz",
            "cd leptonica-1.79.0",
            "./configure --prefix=/usr/local/",
            "make",
            "sudo make install",
            "export PKG_CONFIG_PATH=/usr/local/leptonica-1.79.0/lib/pkgconfig",
            "cd /tmp",
            "wget https://codeload.github.com/tesseract-ocr/tesseract/tar.gz/4.1.1",
            "tar -zxvf 4.1.1",
            "cd tesseract-4.1.1",
            "./autogen.sh",
            "LIBLEPT_HEADERSDIR=/usr/local/lib ./configure --prefix=/usr/local/ --with-extra-libraries=/usr/local/lib",
            "autoreconf --force --install",
            "./configure",
            "make",
            "sudo make install",
            "sudo ldconfig",
            "cd /tmp",
            "wget https://github.com/tesseract-ocr/tessdata_fast/blob/master/eng.traineddata?raw=true",
            "sudo mv /tmp/eng.traineddata?raw=true /usr/local/share/tessdata/eng_fast.traineddata",
            f"cd {current_dir}",
        ]
```
and then simply enter `$ python _sys.py` in the terminal. 
