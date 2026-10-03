import unicodedata
from app.database import SessionLocal
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service

def clean_and_reembed():
    db = SessionLocal()
    chunks = db.query(DocumentChunk).all()
    print(f"Normalizing and re-embedding {len(chunks)} chunks in database...")
    for c in chunks:
        clean = unicodedata.normalize('NFKD', c.content)
        clean = (
            clean.replace('\ufb00', 'ff')
            .replace('\ufb01', 'fi')
            .replace('\ufb02', 'fl')
            .replace('\ufb03', 'ffi')
            .replace('\ufb04', 'ffl')
            .replace('’', "'")
            .replace('“', '"')
            .replace('”', '"')
            .replace('–', '-')
            .replace('—', '-')
        )
        c.content = clean
        c.embedding = embedding_service.embed_query(clean)
    db.commit()
    print("All chunks cleaned and re-embedded successfully!")

if __name__ == "__main__":
    clean_and_reembed()
