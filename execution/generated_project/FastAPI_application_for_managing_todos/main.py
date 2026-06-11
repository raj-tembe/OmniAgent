from fastapi import FastAPI, HTTPException, status
from typing import Dict, List, Optional
from models import Todo

app = FastAPI(
    title="Todo API",
    description="A simple FastAPI application for managing todos."
)

# In-memory data store for demonstration purposes
todos: Dict[int, Todo] = {}
next_id = 1

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Todo API!"}

@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED, tags=["Todos"])
async def create_todo(todo: Todo):
    global next_id
    todo.id = next_id
    todos[next_id] = todo
    next_id += 1
    return todo

@app.get("/todos", response_model=List[Todo], tags=["Todos"])
async def read_todos():
    return list(todos.values())

@app.get("/todos/{todo_id}", response_model=Todo, tags=["Todos"])
async def read_todo(todo_id: int):
    if todo_id not in todos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todos[todo_id]

@app.put("/todos/{todo_id}", response_model=Todo, tags=["Todos"])
async def update_todo(todo_id: int, updated_todo: Todo):
    if todo_id not in todos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    # Preserve the original ID
    updated_todo.id = todo_id
    todos[todo_id] = updated_todo
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
async def delete_todo(todo_id: int):
    if todo_id not in todos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos[todo_id]
    return # No content for 204 status
