from app.config import Settings


def test_cors_allow_origins_default() -> None:
    """Default CORS origins should be '*' (allow all)."""
    settings = Settings()
    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    assert origins == ["*"]


def test_cors_allow_origins_custom() -> None:
    """Custom CORS origins are parsed from a comma-separated string."""
    settings = Settings(cors_allow_origins="https://a.example.com,https://b.example.com")
    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    assert origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_middleware_registered_in_main() -> None:
    """main.py must register CORSMiddleware (verified by source inspection)."""
    import pathlib
    src = pathlib.Path(__file__).parent.parent / "app" / "main.py"
    content = src.read_text()
    assert "CORSMiddleware" in content, "CORSMiddleware not found in app/main.py"
    assert "add_middleware" in content, "add_middleware call not found in app/main.py"
