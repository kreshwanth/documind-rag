import uuid
from datetime import timedelta
from app.utils.security import verify_password, get_password_hash, create_access_token, decode_access_token

def test_password_hashing():
    raw = "EnterprisePassword!123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)

def test_expired_jwt_token():
    user_id = uuid.uuid4()
    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    payload = decode_access_token(expired_token)
    assert payload is None

def test_malformed_jwt_token():
    payload = decode_access_token("not.a.valid.jwt.token")
    assert payload is None
