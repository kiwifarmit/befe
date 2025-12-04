from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db import get_async_session, init_db
from app.models import Base


@pytest.mark.asyncio
async def test_init_db():
    """Test database initialization."""
    mock_run_sync = AsyncMock()

    mock_conn = MagicMock()
    mock_conn.run_sync = mock_run_sync

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    mock_engine = MagicMock()
    mock_engine.begin = MagicMock(return_value=mock_context)

    with patch("app.db.engine", mock_engine):
        await init_db()
        mock_run_sync.assert_called_once_with(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_get_async_session():
    """Test async session generator."""
    from sqlalchemy.ext.asyncio import AsyncSession

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_sessionmaker = MagicMock(return_value=mock_session)

    with patch("app.db.sessionmaker", return_value=mock_sessionmaker):
        async for session in get_async_session():
            assert session is not None
            break
