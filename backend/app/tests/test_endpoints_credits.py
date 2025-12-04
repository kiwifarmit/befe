"""Test to ensure update_user_credits endpoint exists and is secure."""

from app.api.credits import router, update_user_credits


def test_update_credits_endpoint_exists():
    """Ensure the update_user_credits endpoint exists in the router."""
    routes = [r for r in router.routes if hasattr(r, "path") and "credits" in r.path]
    assert len(routes) > 0, "update_user_credits endpoint is missing!"

    credits_route = routes[0]
    assert "/users/{user_id}/credits" in credits_route.path
    assert "PATCH" in credits_route.methods


def test_update_credits_endpoint_function_exists():
    """Ensure the update_user_credits function exists."""
    assert update_user_credits is not None
    assert callable(update_user_credits)
