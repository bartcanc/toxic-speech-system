from pydantic import BaseModel

#   INPUT
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

#   OUTPUT
class UserResponse(BaseModel):      #   after register
    id: int
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):             #   after login
    access_token: str
    token_type: str