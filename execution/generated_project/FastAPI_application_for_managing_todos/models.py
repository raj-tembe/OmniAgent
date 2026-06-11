from pydantic import BaseModel, Field
from typing import Optional

class Todo(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, description="Title of the todo item")
    description: Optional[str] = Field(None, description="Optional description of the todo item")
    completed: bool = Field(False, description="Status of the todo item")

    class Config:
        schema_extra = {
            "example": {
                "title": "Buy groceries",
                "description": "Milk, Eggs, Bread, Fruits",
                "completed": false
            }
        }
