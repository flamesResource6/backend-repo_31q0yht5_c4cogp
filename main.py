import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import BlogPost, ContactMessage

app = FastAPI(title="Personal Site API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Personal Site Backend is running"}

# Blog endpoints
@app.post("/api/blogs", response_model=dict)
def create_blog(post: BlogPost):
    try:
        post_id = create_document("blogpost", post)
        return {"id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blogs", response_model=List[dict])
def list_blogs(tag: Optional[str] = None, limit: int = 10):
    try:
        filter_dict = {"published": True}
        if tag:
            filter_dict["tags"] = tag
        docs = get_documents("blogpost", filter_dict, limit)
        # Convert ObjectId to string
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blogs/{slug_or_id}", response_model=dict)
def get_blog(slug_or_id: str):
    try:
        # Try lookup by slug first, then by _id as string
        docs = get_documents("blogpost", {"slug": slug_or_id}, limit=1)
        if not docs:
            docs = get_documents("blogpost", {"_id": slug_or_id}, limit=1)
        if not docs:
            raise HTTPException(status_code=404, detail="Post not found")
        doc = docs[0]
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contact endpoint
@app.post("/api/contact", response_model=dict)
def submit_contact(msg: ContactMessage):
    try:
        msg_id = create_document("contactmessage", msg)
        return {"id": msg_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
