# SPDX-License-Identifier: GPL-3.0
"""OCR worker — extracts text from images/PDFs in a QThread."""

from PySide6.QtCore import QObject, Signal


class OCRWorker(QObject):
    """Runs OCR text extraction in a background thread."""
    finished = Signal(str, str)  # (text, error)
    progress = Signal(int)

    def __init__(self, file_path: str, engine: str = "auto", language: str = "spa+eng"):
        super().__init__()
        self.file_path = file_path
        self.engine = engine
        self.language = language

    def run(self):
        try:
            ext = self.file_path.rsplit(".", 1)[-1].lower()

            if ext == "pdf":
                text = self._ocr_pdf()
            else:
                text = self._ocr_image()

            self.finished.emit(text, "")
        except Exception as e:
            self.finished.emit("", str(e))

    def _ocr_image(self) -> str:
        """Extract text from an image file."""
        if self.engine in ("auto", "tesseract"):
            try:
                return self._tesseract_ocr(self.file_path)
            except ImportError:
                pass

        if self.engine in ("auto", "paddleocr"):
            try:
                return self._paddle_ocr(self.file_path)
            except ImportError:
                pass

        raise RuntimeError(
            "No OCR engine available. Install pytesseract or paddleocr:\n"
            "  pip install pytesseract  (requires Tesseract OCR)\n"
            "  pip install paddleocr paddlepaddle"
        )

    def _ocr_pdf(self) -> str:
        """Extract text from a PDF (OCR if needed)."""
        import fitz  # PyMuPDF
        doc = fitz.open(self.file_path)
        text_parts = []
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)
            else:
                # Page has no text — needs OCR
                pix = page.get_pixmap(dpi=300)
                img_path = f"/tmp/splatsdb_ocr_page_{page.number}.png"
                pix.save(img_path)
                ocr_text = self._ocr_image_file(img_path)
                text_parts.append(ocr_text)
        doc.close()
        return "\n\n".join(text_parts)

    def _tesseract_ocr(self, image_path: str) -> str:
        """Use Tesseract for OCR."""
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang=self.language.replace("+", "+"))

    def _paddle_ocr(self, image_path: str) -> str:
        """Use PaddleOCR for OCR."""
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang=self.language.split("+")[0])
        result = ocr.ocr(image_path, cls=True)
        texts = []
        for line in result[0]:
            texts.append(line[1][0])
        return "\n".join(texts)
