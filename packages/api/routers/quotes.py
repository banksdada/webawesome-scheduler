"""Quote preview for a job (admin only)."""

from html import escape

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from .. import models
from ..db import get_session
from ..deps import require_admin

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/generate")
def generate_quote(job_id: int, admin: models.User = Depends(require_admin), session: Session = Depends(get_session)):
    job = session.get(models.Job, job_id)
    if not job or job.org_id != admin.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    customer = session.get(models.Customer, job.customer_id)
    org = session.get(models.Organisation, admin.org_id)
    price = job.price_estimate or 0
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Quote {job.id}</title>
<style>body{{font-family:sans-serif;padding:2rem}}.total{{font-weight:bold;font-size:1.2em;margin-top:1rem}}</style></head>
<body>
<h1>{escape(org.name)}</h1>
<p><strong>Quote:</strong> {job.id}</p>
<h2>Customer: {escape(customer.name)}</h2>
<p><strong>Service:</strong> {escape(job.title)}</p>
<p class="total">Total: &pound;{price:.2f}</p>
</body></html>"""
    return {"job_id": job.id, "html": html}
