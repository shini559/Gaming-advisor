# DEPRECATED: Utilisez app.adapters.database.connection à la place
from .connection import engine, AsyncSessionLocal, get_db

__all__ = ["engine", "AsyncSessionLocal", "get_db"]