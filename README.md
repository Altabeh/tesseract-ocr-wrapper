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

# Requirements

After cloning the repo, go to the directory `tesseract-ocr-wrapper` and then type
```
$ pip install -r requirements.txt
```
to download and install the required python packages. There are many other packages such as `leptonica` and `pdftotext` that need to be installed.
Since these packages are system dependent, I have included an example `_sys.py` file that allows you 
to directly download and install them for Linux. For all other operating systems, you can modify this file, in particular the commands listed in `_sys.py` i.e.

```
commands = [
            "cd /tmp",
            "wget https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip",
            "unzip chromedriver_linux64.zip",
            "sudo mv chromedriver /usr/bin/chromedriver",
            "chromedriver --version",
            "curl https://intoli.com/install-google-chrome.sh | bash",
            "sudo mv /usr/bin/google-chrome-stable /usr/bin/google-chrome",
            "google-chrome --version && which google-chrome",
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
and then simply use the command `$ python _sys.py` in the terminal. 
