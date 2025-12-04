"""Tests for app/models.py to increase coverage."""

import uuid

from app.models import UserRead


def test_userread_with_dict_credits():
    """Test UserRead with dict input that already has credits."""
    data = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "credits": 25,
    }
    user_read = UserRead.model_validate(data)
    assert user_read.credits == 25


def test_userread_with_dict_user_credits():
    """Test UserRead with dict input containing user_credits object."""
    mock_user_credits = type("obj", (object,), {"credits": 30})()
    data = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "user_credits": mock_user_credits,
    }
    user_read = UserRead.model_validate(data)
    assert user_read.credits == 30


def test_userread_with_dict_no_credits():
    """Test UserRead with dict input without credits or user_credits."""
    data = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    }
    user_read = UserRead.model_validate(data)
    assert user_read.credits == 0


def test_userread_with_object_user_credits():
    """Test UserRead with object input containing user_credits."""
    mock_user_credits = type("obj", (object,), {"credits": 40})()
    user_obj = type(
        "obj",
        (object,),
        {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
            "user_credits": mock_user_credits,
        },
    )()
    user_read = UserRead.model_validate(user_obj)
    assert user_read.credits == 40


def test_userread_with_object_no_credits():
    """Test UserRead with object input without credits or user_credits."""
    user_obj = type(
        "obj",
        (object,),
        {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    )()
    user_read = UserRead.model_validate(user_obj)
    assert user_read.credits == 0


def test_userread_with_object_has_credits():
    """Test UserRead with object input that already has credits attribute."""
    user_obj = type(
        "obj",
        (object,),
        {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
            "credits": 50,
        },
    )()
    user_read = UserRead.model_validate(user_obj)
    assert user_read.credits == 50
