from pydantic import BaseModel

#   INPUT
class UserCreate(BaseModel):
    username: str
    email: str = "string@gmail.com"
    password: str

class UserLogin(BaseModel):
    email: str = "string@gmail.com"
    password: str

class RoleUpdate(BaseModel):
    new_role: str

class PasswordResetRequest(BaseModel):
    email: str = "string@gmail.com"

class PasswordResetConfirm(BaseModel):
    email: str = "string@gmail.com"
    reset_code: str
    new_password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

#   OUTPUT
class UserResponse(BaseModel):      #   after register
    id: int
    email: str = "string@gmail.com"

    class Config:
        from_attributes = True

class Token(BaseModel):             #   after login
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: int
    email: str = "string@gmail.com"
    role: str

    class Config:
        from_attributes = True 

class NewDevice(BaseModel):
    device_id: str