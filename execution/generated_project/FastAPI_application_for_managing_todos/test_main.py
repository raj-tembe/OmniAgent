from fastapi.testclient import TestClient
from main import app, todos, next_id
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_todos_before_each_test():
    """Fixture to clear the in-memory todos dictionary before each test."""
    todos.clear()
    global next_id
    next_id = 1
    yield

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Todo API!"}

def test_create_todo():
    response = client.post(
        "/todos",
        json={
            "title": "Test Todo",
            "description": "This is a test todo.",
            "completed": False
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["id"] == 1
    assert todos[1].title == "Test Todo"

def test_create_todo_missing_title():
    response = client.post(
        "/todos",
        json={
            "description": "Missing title.",
            "completed": False
        }
    )
    assert response.status_code == 422 # Unprocessable Entity

def test_read_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_read_todos_multiple():
    client.post("/todos", json={"title": "Todo 1"})
    client.post("/todos", json={"title": "Todo 2"})
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Todo 1"
    assert response.json()[1]["title"] == "Todo 2"

def test_read_single_todo():
    create_response = client.post("/todos", json={"title": "Single Todo"})
    todo_id = create_response.json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Single Todo"

def test_read_single_todo_not_found():
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

def test_update_todo():
    create_response = client.post("/todos", json={"title": "Original Todo", "completed": False})
    todo_id = create_response.json()["id"]
    
    update_data = {"title": "Updated Todo", "description": "New description", "completed": True}
    response = client.put(f"/todos/{todo_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Updated Todo"
    assert data["description"] == "New description"
    assert data["completed"] == True
    assert todos[todo_id].title == "Updated Todo"

def test_update_todo_not_found():
    response = client.put("/todos/999", json={"title": "Non Existent"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

def test_delete_todo():
    create_response = client.post("/todos", json={"title": "Todo to delete"})
    todo_id = create_response.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert todo_id not in todos

def test_delete_todo_not_found():
    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}
