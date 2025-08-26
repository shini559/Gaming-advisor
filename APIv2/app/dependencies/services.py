from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.services.password_service import IPasswordService
from app.services.password_service import PasswordService
from app.services.jwt_service import JWTService

def get_password_service() -> IPasswordService:
  """Factory for PasswordService"""
  return PasswordService()

def get_jwt_service() -> IJWTService:
  """Factory for JWTService"""
  return JWTService()
