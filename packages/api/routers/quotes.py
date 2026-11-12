"""Quote generation module (Feature‑gated by FEATURE_QUOTES)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
import tempfile
from pathlib import Path
from .. import models
from ..main import engine, get_current_user, FEATURE_QUOTES

# Guard: only include if quotes are enabled
if not FEATURE_QUOTES:
    raise RuntimeError("Quote router imported but FEATURE_QUOTES is disabled.")

router = APIRouter()

# Simple PDF generation via weasyprint (if available) or a placeholder
@router.post("/generate")
def generate_quote(job_id: int, current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        job = session.get(models.Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        customer = session.get(models.Customer, job.customer_id)
        if not customer or customer.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Create a minimal HTML representation of the quote
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quote for {customer.name}</title>
        <style>
            body {{ font-family: sans-serif; padding: 2rem; }}
            .header {{ display: flex; justify-content: space-between; }}
            .total {{ font-weight: bold; font-size: 1.2em; margin-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>WebAwesome Scheduler</h1>
            <div>
                <strong>Quote ID:</strong> {job.id}<br>
                <strong>Date:</strong> {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}
            </div>
        </div>
        <h2>Customer: {customer.name}</h2>
        <p><strong>Service:</strong> {job.title}</p>
        <p><strong>Price Estimate:</strong> ${job.price_estimate or 0:.2f}</p>
        <p class="total">Total Due: ${job.price_estimate or 0:.2f}</p>
        <p>Thank you for choosing WebAwesome!</p>
    </body>
    </html>
    """

    # Write temporary HTML file (we'll just return a placeholder for now)
    # In production, you would run `weasyprint` or a headless browser to generate PDF.
    # For this demo we simulate by returning a download link.
    # We'll store the HTML in a temp directory (for demonstration, we'll just return a message).
    temp_dir = Path(tempfile.mkdtemp())
    html_path = temp_dir / "quote.html"
    html_path.write_text(html)

    # Placeholder: we'll return a simple JSON with a "download_url" that points to /quotes/{job_id}/download
    # For now, we'll just return the HTML content so the frontend can preview it.
    return {
        "job_id": job.id,
        "html": html,
        "message": "Quote generated. Use the download endpoint to get PDF."
    }

# Download endpoint (PDF stub)
@router.get("/{job_id}/download")
def download_quote_pdf(job_id: int, current_user: models.User = Depends(get_current_user)):
    # Same permission check as generate
    with Session(engine) as session:
        job = session.get(models.Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        customer = session.get(models.Customer, job.customer_id)
        if not customer or customer.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quote for {customer.name}</title>
        <style>
            body {{ font-family: sans-serif; padding: 2rem; }}
            .header {{ display: flex; justify-content: space-between; }}
            .total {{ font-weight: bold; font-size: 1.2em; margin-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>WebAwesome Scheduler</h1>
            <div>
                <strong>Quote ID:</strong> {job.id}<br>
                <strong>Date:</strong> {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}
            </div>
        </div>
        <h2>Customer: {customer.name}</h2>
        <p><strong>Service:</strong> {job.title}</p>
        <p><strong>Price Estimate:</strong> ${job.price_estimate or 0:.2f}</p>
        <p class="total">Total Due: ${job.price_estimate or 0:.2f}</p>
        <p>Thank you for choosing WebAwesome!</p>
    </body>
    </html>
    """

    # For demo, we just return the HTML content as a downloadable plain text file.
    # You could replace this with a real PDF generation library.
    return {
        "content": html,
        "message": "Quote PDF download stub – replace with real PDF generation."
    }