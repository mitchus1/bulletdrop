# Import Base from database module
from app.core.database import Base

# Import all models
from .user import User
from .upload import Upload
from .domain import Domain, UserDomain, UploadAnalytic

# Make models available for import
__all__ = ["Base", "User", "Upload", "Domain", "UserDomain", "UploadAnalytic"]