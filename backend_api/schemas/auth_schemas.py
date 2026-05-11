from pydantic import BaseModel

#   INPUT
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class RoleUpdate(BaseModel):
    new_role: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    email: str
    reset_code: str
    new_password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

#   OUTPUT
class UserResponse(BaseModel):      #   after register
    id: int
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):             #   after login
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True 

class NewDevice(BaseModel):
    device_id: str