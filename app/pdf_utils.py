# =============================================================================
# AI Resume Screener — pdf_utils.py
# Handles reading resume PDFs uploaded by the recruiter.
# Validates file type and size BEFORE reading, then extracts plain text.
# =============================================================================

import PyPDF2                  # Library that reads PDF files in Python
import io                      # Lets us read file bytes as a stream (no disk write needed)
import logging                 # Python's built-in logger — we use this instead of print()

# Set up a logger for this module.
# Best practice: each module gets its own named logger.
# In production, logs flow to a log aggregator (like Datadog or Render's log viewer).
logger = logging.getLogger(__name__)

# ── Security constants ──────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 5                         # Reject files larger than 5 MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPE = "application/pdf"        # Only PDFs allowed
ALLOWED_EXTENSION = ".pdf"


def validate_pdf_file(uploaded_file) -> tuple[bool, str]:
    """
    Security gate #1: Validate the uploaded file BEFORE reading it.
    
    Returns:
        (True, "") if file is safe to process
        (False, "reason") if file should be rejected
    
    Why do this?
    - File type check: prevents uploading .exe or .sh files renamed to .pdf
    - Size check: prevents memory exhaustion attacks (uploading a 500 MB file)
    """

    # Check 1: Does the filename end in .pdf?
    filename: str = uploaded_file.name.lower()
    if not filename.endswith(ALLOWED_EXTENSION):
        return False, f"File must be a PDF. Received: {filename}"

    # Check 2: Is the file under the size limit?
    # uploaded_file.size is provided by Streamlit in bytes
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
    Extracts all plain text from a PDF file uploaded via Streamlit.
    
    Args:
        uploaded_file: The file object from st.file_uploader()
    
    Returns:
        (text, "") on success — text is the extracted string
        ("", error_message) on failure

    How PyPDF2 works:
        PDF files store content in pages. PyPDF2 opens the PDF,
        loops through each page, and extracts the text layer.
        Note: scanned/image PDFs have no text layer — we handle that case.
    """

    try:
        # Read all bytes from the uploaded file into memory
        # io.BytesIO wraps raw bytes so PyPDF2 can read it like a file
        pdf_bytes = uploaded_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)

        # Open the PDF with PyPDF2
        reader = PyPDF2.PdfReader(pdf_stream)

        # Safety check: reject unreasonably long PDFs
        num_pages = len(reader.pages)
        if num_pages > 10:
            return "", f"Resume PDF has {num_pages} pages. Maximum is 10."

        # Extract text from each page and join with a newline
        extracted_pages = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())
            else:
                logger.warning(f"Page {page_num + 1} had no extractable text (may be an image).")

        full_text = "\n\n".join(extracted_pages).strip()

        # If no text at all was extracted, the PDF is likely a scanned image
        if not full_text:
            return "", (
                "No text could be extracted from this PDF. "
                "It may be a scanned image. Please upload a text-based PDF."
            )

        logger.info(f"Successfully extracted {len(full_text)} characters from {num_pages} pages.")
        return full_text, ""

    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"PDF read error: {e}")
        return "", "The PDF file appears to be corrupted or unreadable."

    except Exception as e:
        # Catch-all: log the full error internally, show a safe message to user
        logger.error(f"Unexpected error extracting PDF text: {e}", exc_info=True)
        return "", "An unexpected error occurred while reading the PDF."
