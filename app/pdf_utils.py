# =============================================================================
# AI Resume Screener — app/pdf_utils.py
# Handles reading resumes from three input methods:
#   1. PDF upload (PyPDF2)
#   2. Word (.docx) upload (python-docx)
#   3. Plain text paste (no file processing needed)
# Validates file type and size BEFORE reading in all cases.
# =============================================================================

import PyPDF2                  # Reads PDF files
import docx                    # Reads Word .docx files (python-docx library)
import io                      # Wraps bytes as a file-like stream
import logging

logger = logging.getLogger(__name__)

# ── Security constants ────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """
    Security gate: validate any uploaded resume file before reading it.
    Accepts both .pdf and .docx files.

    Returns:
        (True, "") if file is safe to process
        (False, "reason") if file should be rejected

    Why validate first?
    - Extension check: blocks renamed executables (.exe → .pdf)
    - Size check: prevents memory exhaustion from huge files
    - Empty check: prevents silent failures downstream
    """

    filename: str = uploaded_file.name.lower()

    # Check 1: Is the extension allowed?
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, (
            f"Unsupported file type: {filename}. "
            f"Please upload a PDF or Word (.docx) file."
        )

    # Check 2: Is the file under the size limit?
    file_size = uploaded_file.size
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return False, (
            f"File is too large ({size_mb:.1f} MB). "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    # Check 3: Is the file non-empty?
    if file_size == 0:
        return False, "Uploaded file is empty."

    return True, ""


def extract_text_from_pdf(uploaded_file) -> tuple[str, str]:
    """
    Extracts plain text from an uploaded PDF file.

    Returns:
        (text, "") on success
        ("", error_message) on failure

    Note: scanned/image PDFs have no text layer and will return an error.
    """

    try:
        pdf_bytes = uploaded_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_stream)

        # Reject unreasonably long documents
        num_pages = len(reader.pages)
        if num_pages > 10:
            return "", f"Resume has {num_pages} pages. Maximum is 10."

        extracted_pages = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())
            else:
                logger.warning(f"Page {page_num + 1} had no extractable text.")

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            return "", (
                "No text could be extracted from this PDF. "
                "It may be a scanned image. Please upload a text-based PDF "
                "or paste your resume text directly."
            )

        logger.info(f"PDF: extracted {len(full_text)} characters from {num_pages} pages.")
        return full_text, ""

    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"PDF read error: {e}")
        return "", "The PDF file appears to be corrupted or unreadable."

    except Exception as e:
        logger.error(f"Unexpected PDF error: {e}", exc_info=True)
        return "", "An unexpected error occurred while reading the PDF."


def extract_text_from_docx(uploaded_file) -> tuple[str, str]:
    """
    Extracts plain text from an uploaded Word (.docx) file.

    How python-docx works:
        A .docx file is a zip archive containing XML. python-docx parses
        that XML and exposes paragraphs as Python objects. We loop through
        each paragraph and join their text content.

    Returns:
        (text, "") on success
        ("", error_message) on failure
    """

    try:
        # Read file bytes into memory and wrap as a stream for python-docx
        docx_bytes = uploaded_file.read()
        docx_stream = io.BytesIO(docx_bytes)

        # Open the Word document
        document = docx.Document(docx_stream)

        # Extract text from every paragraph
        # A paragraph in Word is any block of text separated by Enter
        paragraphs = []
        for para in document.paragraphs:
            text = para.text.strip()
            if text:  # Skip empty paragraphs
                paragraphs.append(text)

        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            return "", (
                "No text could be extracted from this Word document. "
                "Please try a different file or paste your resume text directly."
            )

        logger.info(f"DOCX: extracted {len(full_text)} characters from {len(paragraphs)} paragraphs.")
        return full_text, ""

    except Exception as e:
        logger.error(f"Unexpected DOCX error: {e}", exc_info=True)
        return "", "An unexpected error occurred while reading the Word document."


def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """
    Router function: detects file type and calls the correct extractor.

    This is the single function main.py calls — it doesn't need to know
    whether the file is PDF or DOCX, it just gets back text or an error.

    Args:
        uploaded_file: Streamlit file object from st.file_uploader()

    Returns:
        (text, "") on success
        ("", error_message) on failure
    """

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        # Should never reach here if validate_uploaded_file() ran first
        return "", f"Unsupported file type: {filename}"