import strawberry
from dataclasses import dataclass

@strawberry.type
class RegularResponse:
    success: bool
    message: str

@strawberry.type
@dataclass
class DataclassResponse:
    success: bool
    message: str

print(RegularResponse(success=True, message="Regular"))
print(DataclassResponse(success=True, message="Dataclass"))
