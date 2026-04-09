# Knowledge Sharing Platform

A modern knowledge sharing platform with content analysis and reliability scoring, similar to LinkedIn and Quora but with advanced content verification features.

## Features

### Core Features

- **User Authentication**: Secure registration and login with JWT tokens
- **Content Creation**: Create posts with different types (text, article, question, discussion)
- **Content Analysis**: AI-powered reliability scoring for all shared content
- **Badge System**: Earn badges based on content reliability and contribution
- **Social Features**: Like posts, comment, connect with other users
- **Search**: Search posts and users with advanced filtering

### Unique Features

- **Reliability Scoring**: Each post is analyzed and given a reliability score (0-100%)
- **Content Verification**: Automatic verification for high-quality content
- **Badge Progression**: 5-tier badge system (Newcomer → Knowledge Master)
- **Author Reputation**: Users build reputation through consistently sharing reliable content

## Tech Stack

### Backend

- **FastAPI**: Modern Python web framework
- **MongoDB**: NoSQL database for flexible data storage
- **Motor**: Async MongoDB driver
- **JWT**: Secure authentication
- **TextBlob & NLTK**: Natural language processing for content analysis
- **Scikit-learn**: Machine learning for content scoring

### Frontend

- **HTML5, CSS3, JavaScript**: Modern web technologies
- **Responsive Design**: Mobile-first approach
- **Font Awesome**: Icon library
- **Modern UI**: Clean, professional interface

## Project Structure

```
final/
├── README.md                    # Project documentation
├── setup.py                     # Python package setup
├── test.txt                     # Test file
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt         # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── database.py          # Database connection and configuration
│       ├── models/              # Database models
│       │   ├── __init__.py
│       │   ├── connection.py    # User connection model
│       │   ├── post.py          # Post model
│       │   └── user.py          # User model
│       ├── routers/             # API endpoints
│       │   ├── __init__.py
│       │   ├── admin.py         # Admin endpoints
│       │   ├── auth.py          # Authentication endpoints
│       │   ├── connections.py   # User connections endpoints
│       │   ├── posts.py         # Post management endpoints
│       │   └── users.py         # User management endpoints
│       ├── services/            # Business logic services
│       │   ├── __init__.py
│       │   ├── badge_service.py     # Badge evaluation logic
│       │   ├── connection_service.py # User connection management
│       │   ├── content_analysis.py  # AI content analysis
│       │   ├── post_service.py      # Post operations
│       │   └── user_service.py      # User operations
│       └── utils/               # Utility functions
│           ├── __init__.py
│           └── auth.py          # Authentication utilities
├── frontend/
│   ├── index.html               # Main application page
│   ├── admin.html               # Admin dashboard
│   ├── styles.css               # Main application styles
│   ├── admin-styles.css         # Admin dashboard styles
│   ├── script.js                # Main application logic
│   └── admin-script.js          # Admin dashboard logic
└── uploads/                     # File upload directories
    ├── 3c5433fa-6bc6-4bf1-9ec9-8345cdb5703b.txt
    ├── c77fe193-8d73-4a1f-921b-9f00f82b5f2b.txt
    └── 76b6e5c8-5eb0-448c-a435-43093a4a8196.txt
```

## Installation and Setup

### Prerequisites

- Python 3.8+
- MongoDB (local installation or MongoDB Atlas)
- Node.js (optional, for development tools)

### Backend Setup

1. **Install Python Dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Setup Environment Variables**
   - Copy `.env` file and update with your MongoDB connection string
   - Change JWT secret key for production

3. **Start MongoDB**
   - If using local MongoDB: `mongod`
   - Or update `.env` with MongoDB Atlas connection string

4. **Run Backend Server**
   ```bash
   cd backend
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Open Frontend**
   - Simply open `frontend/index.html` in your web browser
   - Or use a local server for better development experience

2. **API Documentation**
   - Visit `http://localhost:8000/docs` for interactive API documentation

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Posts

- `POST /api/posts/` - Create new post
- `GET /api/posts/` - Get posts with pagination
- `GET /api/posts/search` - Search posts
- `POST /api/posts/{id}/like` - Like/unlike post
- `POST /api/posts/{id}/comments` - Add comment

### Users

- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update profile
- `GET /api/users/{id}` - Get user profile
- `GET /api/users/{id}/badges` - Get user badges

### Connections

- `POST /api/connections/request` - Send connection request
- `POST /api/connections/{id}/accept` - Accept connection
- `POST /api/connections/{id}/reject` - Reject connection
- `GET /api/connections/pending` - Get pending requests

## Content Analysis System

The platform uses advanced NLP techniques to analyze content:

### Scoring Factors

- **Keyword Analysis**: Presence of research-oriented terms
- **Pattern Detection**: Identifies unreliable content patterns
- **Structure Analysis**: Evaluates content organization
- **Fact-Checking Indicators**: Looks for sources and citations
- **Sentiment Analysis**: Balanced perspective scoring
- **Readability**: Content clarity assessment

### Badge System

1. **Newcomer** (0+ score, 0+ posts)
2. **Reliable Source** (60+ score, 5+ posts)
3. **Expert Contributor** (75+ score, 15+ posts)
4. **Trusted Author** (85+ score, 25+ posts)
5. **Knowledge Master** (95+ score, 50+ posts)

## Usage Guide

### For Users

1. **Register**: Create an account with email and password
2. **Create Posts**: Share knowledge with proper sources and evidence
3. **Build Reputation**: Consistently share high-quality content
4. **Connect**: Network with other knowledgeable users
5. **Earn Badges**: Progress through the badge system

### Content Tips for High Reliability Scores

- Include research data and statistics
- Cite sources and references
- Use balanced, objective language
- Avoid sensationalism and clickbait
- Structure content clearly with proper formatting
- Provide evidence-based arguments

## Development

### Running in Development Mode

```bash
# Backend with auto-reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (optional local server)
cd frontend
python -m http.server 3000
```

### Environment Variables

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=knowledge_platform
JWT_SECRET_KEY=your-secure-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- Real-time notifications
- Advanced search with filters
- Content moderation system
- Mobile app
- AI-powered content recommendations
- Integration with external fact-checking APIs
- Advanced analytics dashboard
- Content versioning and editing history

## Support

For issues and questions, please open an issue on the GitHub repository.

---

**Built with ❤️ for reliable knowledge sharing**
