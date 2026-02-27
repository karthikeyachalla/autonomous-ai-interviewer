import fitz  # PyMuPDF
import base64
from backend.core.config import settings


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Try Grok-based extraction first (for small files), else fallback to PyMuPDF.

    Grok extraction encodes the PDF as base64 and sends it in a prompt to the
    Grok adapter. Large PDFs are not suitable for this method due to token
    limits; we only attempt Grok when the file is under 200KB.
    """
    # try Grok when key is available and file reasonably small
    try:
        if settings.GROK_API_KEY and len(pdf_bytes) <= 200_000:
            try:
                from backend.round1.ats_evaluator import call_grok

                b64 = base64.b64encode(pdf_bytes).decode("ascii")
                prompt = (
                    "Extract the plain text content from the following PDF file encoded in base64."
                    " Return only the extracted text, without commentary.\n\nBEGIN_BASE64\n"
                    f"{b64}\nEND_BASE64"
                )
                resp = call_grok(prompt)
                if resp:
                    return resp
            except Exception:
                # fall through to local extraction
                pass
    except Exception:
        # safety: any problem reading settings should fall back to local parser
        pass

    # Local extraction with PyMuPDF as fallback
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception:
        # last resort: try to decode as text
        try:
            return pdf_bytes.decode(errors="ignore")
        except Exception:
            return ""


def extract_text_from_file(file) -> str:
    content = file.read()
    return extract_text_from_pdf_bytes(content)
