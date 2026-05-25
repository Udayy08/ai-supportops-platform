import io
import pypdf
from fastapi import UploadFile, HTTPException

async def extract_text_from_upload(file: UploadFile) -> str:
    """
    Extracts raw text from an uploaded file (PDF, TXT, MD).
    Raises an AppException if the file format is unsupported or extraction fails.
    """
    filename = file.filename or ""
    content = await file.read()
    await file.seek(0)
    
    file_type = filename.split(".")[-1].lower() if "." in filename else ""
    
    if file_type == "pdf":
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            text_blocks = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_blocks.append(text)
            return "\n\n".join(text_blocks)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
            
    elif file_type in ("txt", "md", "csv"):
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to decode text file: {str(e)}"
                )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: .{file_type}. Supported formats: pdf, txt, md"
        )
