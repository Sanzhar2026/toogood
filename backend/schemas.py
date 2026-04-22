from pydantic import BaseModel

class FoodBase(BaseModel):
    name_ru: str
    name_kz: str
    price: float
    image: str
    discount: int

class Food(FoodBase):
    id: int

    class Config:
        orm_mode = True