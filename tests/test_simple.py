"""
Простые тесты для проверки работоспособности pytest
"""

def test_imports():
    """Тест импортов"""
    import django
    from django.conf import settings
    assert settings.configured

def test_basic():
    """Базовый тест"""
    assert 1 + 1 == 2

def test_string():
    """Тест строк"""
    assert "hello".upper() == "HELLO"