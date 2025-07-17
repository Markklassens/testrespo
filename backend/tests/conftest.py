import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_db
from models import Base
from server import app
from models import User, Category, Tool, Blog, FreeTool
from auth import get_password_hash
import uuid

# Test database URL - use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        user_type="user",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_admin(db):
    """Create a test admin user"""
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        username="testadmin",
        full_name="Test Admin",
        hashed_password=get_password_hash("adminpass123"),
        user_type="admin",
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture
def test_superadmin(db):
    """Create a test superadmin user"""
    superadmin = User(
        id=str(uuid.uuid4()),
        email="superadmin@example.com",
        username="testsuperadmin",
        full_name="Test Superadmin",
        hashed_password=get_password_hash("superadminpass123"),
        user_type="superadmin",
        is_active=True,
        is_verified=True
    )
    db.add(superadmin)
    db.commit()
    db.refresh(superadmin)
    return superadmin

@pytest.fixture
def test_category(db):
    """Create a test category"""
    category = Category(
        id=str(uuid.uuid4()),
        name="Test Category",
        description="Test category description",
        icon="test-icon",
        color="#FF0000"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@pytest.fixture
def test_tool(db, test_category):
    """Create a test tool"""
    tool = Tool(
        id=str(uuid.uuid4()),
        name="Test Tool",
        description="Test tool description",
        short_description="Short description",
        website_url="https://testtool.com",
        pricing_model="Freemium",
        category_id=test_category.id,
        slug="test-tool"
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool

@pytest.fixture
def test_blog(db, test_user, test_category):
    """Create a test blog"""
    blog = Blog(
        id=str(uuid.uuid4()),
        title="Test Blog",
        content="Test blog content",
        author_id=test_user.id,
        category_id=test_category.id,
        status="published",
        slug="test-blog"
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog

@pytest.fixture
def test_free_tool(db):
    """Create a test free tool"""
    free_tool = FreeTool(
        id=str(uuid.uuid4()),
        name="Test Free Tool",
        description="Test free tool description",
        slug="test-free-tool",
        is_active=True
    )
    db.add(free_tool)
    db.commit()
    db.refresh(free_tool)
    # Ensure the free tool is attached to the session for the duration of the test
    db.expunge(free_tool)
    db.add(free_tool)
    return free_tool

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post("/api/auth/login", json={
        "email": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin):
    """Get authentication headers for test admin"""
    response = client.post("/api/auth/login", json={
        "email": test_admin.email,
        "password": "adminpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superadmin_headers(client, test_superadmin):
    """Get authentication headers for test superadmin"""
    response = client.post("/api/auth/login", json={
        "email": test_superadmin.email,
        "password": "superadminpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}