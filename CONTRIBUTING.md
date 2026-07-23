# Contributing to Developer Analytics Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/developer-analytics-platform.git
cd developer-analytics-platform

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/developer-analytics-platform.git
```

### 2. Set Up Development Environment

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### 3. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

## Development Workflow

### Backend Development

```bash
# Install dependencies
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest

# Run with hot reload
uvicorn gateway.main:app --reload
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Adding a New Platform Connector

### 1. Create Connector Class

Create `backend/services/connector/your_platform.py`:

```python
from services.connector.base import BaseConnector, ProfileData, ProblemData

class YourPlatformConnector(BaseConnector):
    @property
    def platform_name(self) -> str:
        return "your_platform"
    
    async def authenticate(self) -> bool:
        # Implement authentication
        pass
    
    async def fetch_profile(self) -> ProfileData:
        # Fetch user profile
        pass
    
    async def fetch_problem_stats(self) -> List[ProblemData]:
        # Fetch solved problems
        pass
    
    async def fetch_contest_stats(self) -> List[ContestData]:
        # Fetch contest data
        pass
    
    async def fetch_activity(self, days: int = 30) -> List[Dict]:
        # Fetch recent activity
        pass
```

### 2. Register Connector

Update `backend/services/connector/registry.py`:

```python
from services.connector.your_platform import YourPlatformConnector

class ConnectorRegistry:
    _connectors: Dict[str, Type[BaseConnector]] = {
        "leetcode": LeetCodeConnector,
        "codeforces": CodeforcesConnector,
        "your_platform": YourPlatformConnector,  # Add here
    }
```

### 3. Test Your Connector

```python
# backend/tests/test_your_platform.py
import pytest
from services.connector.your_platform import YourPlatformConnector

@pytest.mark.asyncio
async def test_fetch_profile():
    connector = YourPlatformConnector("test_user")
    profile = await connector.fetch_profile()
    assert profile.username == "test_user"
```

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to functions and classes

```python
from typing import List, Optional

async def fetch_user_data(user_id: int, include_stats: bool = True) -> Optional[Dict]:
    """
    Fetch user data from database.
    
    Args:
        user_id: The user's ID
        include_stats: Whether to include statistics
        
    Returns:
        User data dictionary or None if not found
    """
    pass
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Define interfaces for data structures
- Use functional components with hooks
- Follow React best practices

```typescript
interface UserProfile {
  id: number;
  username: string;
  email: string;
}

const UserCard: React.FC<{ profile: UserProfile }> = ({ profile }) => {
  return <div>{profile.username}</div>;
};
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Frontend Tests

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Writing Tests

```python
# Backend test example
def test_user_registration(client, db):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "id" in response.json()
```

```typescript
// Frontend test example
import { render, screen } from '@testing-library/react';
import Login from './Login';

test('renders login form', () => {
  render(<Login />);
  expect(screen.getByText(/login/i)).toBeInTheDocument();
});
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include parameter descriptions and return types
- Provide usage examples for complex functions

### API Documentation

- Update `API_DOCUMENTATION.md` for new endpoints
- Include request/response examples
- Document error codes

### Architecture Documentation

- Update `ARCHITECTURE.md` for architectural changes
- Add diagrams for complex flows
- Explain design decisions

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(connector): add GitHub connector

Implement GitHub connector with repository tracking
and activity fetching capabilities.

Closes #123
```

```bash
fix(auth): resolve token expiration issue

Fixed bug where tokens were expiring prematurely
due to incorrect timezone handling.
```

## Pull Request Process

### 1. Ensure Quality

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] Commits are clean and descriptive

### 2. Create Pull Request

- Use a clear, descriptive title
- Reference related issues
- Describe changes in detail
- Add screenshots for UI changes
- List breaking changes if any

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Self-review completed
```

### 4. Review Process

- Address review comments promptly
- Keep discussions focused and professional
- Update PR based on feedback
- Request re-review after changes

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating a Release

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Tag the release
5. Deploy to production

## Getting Help

- 💬 Join our Discord community
- 📧 Email: dev@devanalytics.com
- 🐛 Open an issue on GitHub
- 📖 Read the documentation

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉
