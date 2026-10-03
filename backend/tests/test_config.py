from app.config import settings

def test_settings_initialization():
    assert settings.PROJECT_NAME == "DocuMind"
    assert settings.EMBEDDING_DIMENSION == 768
    assert settings.TOP_K >= 1
    assert 0.0 <= settings.SIMILARITY_THRESHOLD <= 1.0
    assert settings.MAX_FILE_SIZE_MB > 0
    assert settings.UPLOAD_DIRECTORY is not None
