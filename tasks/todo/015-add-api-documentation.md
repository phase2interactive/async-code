# Task: Add API Documentation

**Priority**: LOW
**Component**: Backend API
**Type**: Documentation

## Problem
No API documentation makes integration difficult and increases security risks.

## Required Documentation

### 1. OpenAPI/Swagger Specification
```python
from flask_restx import Api, Resource, fields

api = Api(app, version='1.0', title='Async Code API',
    description='Multi-agent code task management API',
    doc='/api/docs'
)

task_model = api.model('Task', {
    'id': fields.Integer(required=True, description='Task ID'),
    'status': fields.String(required=True, enum=['pending', 'running', 'completed', 'failed']),
    'agent': fields.String(required=True, enum=['claude', 'codex']),
    'repo_url': fields.String(required=True, description='GitHub repository URL'),
    'prompt': fields.String(required=True, description='Task prompt')
})
```

### 2. Endpoint Documentation
- Request/response schemas
- Authentication requirements
- Rate limits
- Error responses
- Example requests

### 3. Security Documentation
- Authentication flow
- Required headers
- CSRF token usage
- Rate limiting rules

### 4. Integration Guide
- Quick start guide
- Authentication setup
- Common workflows
- Error handling

## Implementation Steps
1. Install Flask-RESTX: `pip install flask-restx`
2. Define API models
3. Add decorators to endpoints
4. Configure Swagger UI
5. Document authentication
6. Add request/response examples
7. Create integration guide
8. Deploy documentation

## Example Endpoint Documentation
```python
@api.route('/tasks/create')
class CreateTask(Resource):
    @api.doc('create_task')
    @api.expect(create_task_model)
    @api.marshal_with(task_model, code=201)
    @api.response(400, 'Validation Error')
    @api.response(401, 'Unauthorized')
    @api.response(429, 'Rate Limit Exceeded')
    def post(self):
        """Create a new task"""
        # Implementation
```

## Acceptance Criteria
- [ ] OpenAPI spec complete
- [ ] All endpoints documented
- [ ] Interactive Swagger UI available
- [ ] Authentication documented
- [ ] Examples for all operations
- [ ] Integration guide written