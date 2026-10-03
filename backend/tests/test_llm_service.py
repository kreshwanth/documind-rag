from unittest.mock import MagicMock, patch
from app.services.llm_service import LLMService
from app.services.prompt_builder import FALLBACK_RESPONSE_STRING

def test_llm_service_offline_fallback():
    service = LLMService(api_key="")
    ans = service.generate_answer("Sample prompt")
    assert ans == FALLBACK_RESPONSE_STRING

def test_llm_service_with_mocked_gemini():
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Based on the provided documents, the revenue grew by 14%."
        mock_instance.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_instance

        service = LLMService(api_key="mock_key")
        answer = service.generate_answer("Prompt")
        assert "revenue grew by 14%" in answer
