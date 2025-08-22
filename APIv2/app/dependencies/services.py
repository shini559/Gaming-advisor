from app.adapters.auth.password_service import PasswordService
from app.adapters.auth.jwt_service import JWTService

def get_password_service() -> PasswordService:
  """Factory for PasswordService"""
  return PasswordService()

def get_jwt_service() -> JWTService:
  """Factory for JWTService"""
  return JWTService()
