# MVP Health Dashboard Backend

## 🎯 Overview

This MVP (Minimum Viable Product) backend provides a comprehensive health dashboard system with AI-powered insights, wearable device integration, and intelligent health assessments. The system uses a "data lake" approach to store and process health information from multiple sources.

## 🏗️ Architecture

### Data Lake Approach
- **Flexible Storage**: All health data is stored as JSON in PostgreSQL for maximum flexibility
- **Multi-Source Integration**: Supports lab results, wearable devices, manual entries, and more
- **Real-time Processing**: Data is processed and normalized as it enters the system
- **AI-Powered Insights**: Gemini AI provides contextual health recommendations

### Core Components

1. **Health Assessment Engine** - Calculates health scores and ratings
2. **Wearable Sync Service** - Integrates with Apple Watch, Fitbit, Garmin
3. **Chat Service** - AI-powered health consultations with context
4. **Data Processing Pipeline** - Normalizes and validates health data
5. **API Layer** - RESTful endpoints for all functionality

## 📊 Features

### Dashboard
- **Health Metrics**: Sleep, hydration, vitamin, and caloric intake scores (0-100)
- **Trend Analysis**: Track improvements and declines over time
- **Recommendations**: AI-generated health suggestions
- **Alerts**: Important health notifications

### Wearable Integration
- **Apple Watch**: Steps, heart rate, sleep, calories, workouts
- **Fitbit**: Activity tracking, sleep monitoring, heart rate
- **Garmin**: Comprehensive fitness and health metrics
- **Auto-Sync**: Configurable sync frequency and data types

### AI Health Chat
- **Context-Aware**: Uses your health data for personalized responses
- **Memory**: Maintains conversation history and context
- **Recommendations**: Provides actionable health advice
- **Follow-up Questions**: Suggests relevant topics to discuss

### Lab Results Processing
- **Multi-Format Support**: Handles various lab result formats
- **Normalization**: Standardizes analyte names and units
- **Reference Ranges**: Determines normal/high/low status
- **Confidence Scoring**: Rates data quality and reliability

## 🗄️ Database Schema

### Core Tables

#### User Profiles
```sql
user_profiles
├── id (UUID, Primary Key)
├── email (String, Unique)
├── name (String)
├── date_of_birth (DateTime)
├── gender (String)
├── height_cm (Float)
├── weight_kg (Float)
└── timestamps
```

#### Health Assessments
```sql
health_assessments
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── sleep_score (Float, 0-100)
├── hydration_score (Float, 0-100)
├── vitamin_score (Float, 0-100)
├── caloric_intake_score (Float, 0-100)
├── overall_health_score (Float, 0-100)
├── detailed_metrics (JSON)
├── data_sources (JSON)
└── confidence_score (Float, 0-1)
```

#### Wearable Data
```sql
wearable_data
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── device_type (String)
├── device_id (String)
├── sync_status (String)
├── raw_data (JSON)
├── processed_data (JSON)
└── data_types (JSON)
```

#### Health Data Lake
```sql
health_data_lake
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── data_type (String)
├── data_source (String)
├── raw_data (JSON)
├── processed_data (JSON)
├── confidence_score (Float)
├── validation_status (String)
└── tags (JSON)
```

#### Chat System
```sql
chat_sessions
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── session_name (String)
├── health_context (JSON)
└── is_active (Boolean)

chat_messages
├── id (UUID, Primary Key)
├── session_id (UUID, Foreign Key)
├── role (String: user/assistant/system)
├── content (Text)
├── health_context_used (JSON)
└── tokens_used (Integer)
```

## 🚀 API Endpoints

### User Management
- `POST /mvp/users/` - Create user profile
- `GET /mvp/users/{user_id}` - Get user profile
- `PUT /mvp/users/{user_id}` - Update user profile

### Dashboard
- `GET /mvp/dashboard/{user_id}` - Get comprehensive dashboard data

### Health Assessments
- `POST /mvp/health-assessments/` - Calculate new health assessment
- `GET /mvp/health-assessments/{user_id}` - Get assessment history

### Wearable Integration
- `POST /mvp/wearables/` - Register wearable device
- `GET /mvp/wearables/{user_id}` - Get user's devices
- `POST /mvp/wearables/sync` - Sync wearable data
- `GET /mvp/wearables/{user_id}/sync-status` - Get sync status

### AI Chat
- `POST /mvp/chat/message` - Send message to AI health assistant
- `GET /mvp/chat/sessions/{user_id}` - Get chat sessions
- `GET /mvp/chat/history/{session_id}` - Get chat history

### Data Lake
- `POST /mvp/data-lake/` - Store health data
- `GET /mvp/data-lake/{user_id}` - Get health data

## 🔧 Health Assessment Engine

### Scoring Algorithm

#### Sleep Score (0-100)
- **Duration**: 7-9 hours optimal (8 hours = 100 points)
- **Efficiency**: >85% optimal
- **Deep Sleep**: 15-20% optimal
- **REM Sleep**: 20-25% optimal
- **Weighted Average**: Duration (40%) + Efficiency (30%) + Deep (15%) + REM (15%)

#### Hydration Score (0-100)
- **Water Intake**: 2.5L daily optimal
- **Urine Color**: Light color indicates good hydration
- **Activity Level**: Higher activity requires more hydration
- **Weighted Average**: Intake (70%) + Urine Color (30%)

#### Vitamin Score (0-100)
- **Vitamin D**: 30-100 ng/mL optimal
- **Vitamin B12**: 200-900 pg/mL optimal
- **Ferritin**: 15-150 ng/mL (women), 30-300 ng/mL (men)
- **Average Score**: Based on optimal ranges for each vitamin

#### Caloric Score (0-100)
- **Balance**: Calories consumed vs. burned
- **BMR Consideration**: Basal metabolic rate factored in
- **Activity Level**: Exercise calories included
- **Optimal Range**: Slight deficit for weight loss, maintenance for weight maintenance

### Overall Health Score
- **Weighted Average**: Sleep (30%) + Hydration (25%) + Vitamins (25%) + Calories (20%)
- **Confidence Score**: Based on data quality and quantity

## 🔄 Data Processing Pipeline

### Lab Results Processing
1. **Extract**: Parse lab data from various formats
2. **Normalize**: Standardize analyte names and units
3. **Validate**: Check reference ranges and data quality
4. **Score**: Calculate confidence and validation status
5. **Tag**: Add searchable tags for categorization
6. **Store**: Save to health data lake

### Wearable Data Processing
1. **Sync**: Connect to device APIs
2. **Extract**: Pull steps, heart rate, sleep, calories
3. **Normalize**: Convert to standard format
4. **Aggregate**: Calculate averages and totals
5. **Validate**: Check data quality and completeness
6. **Store**: Save to health data lake

### Manual Entry Processing
1. **Validate**: Check input format and values
2. **Categorize**: Determine entry type (symptoms, medications, vitals)
3. **Normalize**: Standardize data format
4. **Score**: Assign confidence based on entry type
5. **Store**: Save to health data lake

## 🤖 AI Chat System

### Context Building
- **User Profile**: Age, gender, height, weight
- **Health Assessment**: Latest scores and trends
- **Recent Data**: Summary of recent health data
- **Data Sources**: Active data sources and their reliability

### Response Generation
- **Gemini Integration**: Uses Google's Gemini AI model
- **Health Context**: Includes relevant health data in prompts
- **Personalization**: Tailors responses to user's specific situation
- **Safety**: Avoids medical diagnoses, focuses on general health advice

### Memory Management
- **Session Context**: Maintains conversation history
- **Health Context**: Tracks which health data was used
- **Recommendations**: Extracts and stores actionable advice
- **Follow-up**: Suggests relevant questions for continued conversation

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: Endpoint functionality testing
- **Mock Data**: Comprehensive test data sets

### Test Categories
1. **Health Assessment Engine**: Score calculations and algorithms
2. **Wearable Sync Service**: Device integration and data processing
3. **Chat Service**: AI responses and context management
4. **Data Processing Pipeline**: Data normalization and validation
5. **API Endpoints**: Request/response handling
6. **Data Lake Integration**: Storage and retrieval

### Running Tests
```bash
# Run all MVP tests
pytest tests/test_mvp.py -v

# Run specific test categories
pytest tests/test_mvp.py::TestHealthAssessmentEngine -v
pytest tests/test_mvp.py::TestWearableSyncService -v
pytest tests/test_mvp.py::TestChatService -v
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Gemini API Key

### Installation
```bash
# Clone and setup
git clone <repository>
cd backend

# Run setup script
./start -local

# Or manual setup
python -m venv .venv
source .venv/bin/activate
pip install -e .
make up
alembic upgrade head
make dev
```

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://health:health@127.0.0.1:5434/health
REDIS_URL=redis://127.0.0.1:6379

# Optional
DEBUG=true
LOG_LEVEL=INFO
```

### Quick Start
1. **Start Services**: `./start -local`
2. **Access API**: http://127.0.0.1:8000/docs
3. **Create User**: `POST /mvp/users/`
4. **Upload Data**: `POST /mvp/data-lake/`
5. **Get Assessment**: `POST /mvp/health-assessments/`
6. **Chat with AI**: `POST /mvp/chat/message`

## 📈 Usage Examples

### Creating a User Profile
```python
import requests

user_data = {
    "email": "user@example.com",
    "name": "John Doe",
    "date_of_birth": "1990-01-01T00:00:00Z",
    "gender": "male",
    "height_cm": 180.0,
    "weight_kg": 75.0
}

response = requests.post("http://127.0.0.1:8000/mvp/users/", json=user_data)
user = response.json()
```

### Syncing Wearable Data
```python
sync_data = {
    "device_type": "apple_watch",
    "device_id": "user_device_123",
    "sync_all_data": True
}

response = requests.post(
    "http://127.0.0.1:8000/mvp/wearables/sync?user_id={user_id}",
    json=sync_data
)
sync_result = response.json()
```

### Chatting with AI
```python
chat_data = {
    "message": "How is my sleep quality?",
    "include_health_context": True
}

response = requests.post(
    "http://127.0.0.1:8000/mvp/chat/message?user_id={user_id}",
    json=chat_data
)
chat_response = response.json()
```

### Getting Dashboard Data
```python
response = requests.get(f"http://127.0.0.1:8000/mvp/dashboard/{user_id}")
dashboard = response.json()

print(f"Overall Health Score: {dashboard['health_metrics']['overall_health_score']}")
print(f"Sleep Score: {dashboard['health_metrics']['sleep_score']}")
print(f"Recommendations: {dashboard['recommendations']}")
```

## 🔮 Future Enhancements

### Planned Features
- **More Wearable Devices**: Samsung Galaxy Watch, Oura Ring, Whoop
- **Advanced Analytics**: Machine learning for trend prediction
- **Integration APIs**: Connect with more health services
- **Mobile App**: Native iOS/Android applications
- **Real-time Alerts**: Push notifications for health concerns
- **Family Sharing**: Multi-user health tracking
- **Provider Integration**: Connect with healthcare providers

### Technical Improvements
- **Caching**: Redis caching for improved performance
- **Background Jobs**: Celery for async processing
- **Monitoring**: Health checks and metrics
- **Security**: Enhanced authentication and authorization
- **Scalability**: Horizontal scaling and load balancing

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update README for new features
- **Type Hints**: Use type annotations throughout
- **Error Handling**: Comprehensive error handling and logging

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- **API Docs**: http://127.0.0.1:8000/docs (when running)
- **Health Assessment**: See `app/services/health_assessment.py`
- **Wearable Sync**: See `app/services/wearable_sync.py`
- **Chat Service**: See `app/services/chat_service.py`

### Troubleshooting
- **Database Issues**: Check PostgreSQL connection and migrations
- **API Errors**: Review logs and check environment variables
- **Wearable Sync**: Verify device credentials and network connectivity
- **AI Chat**: Ensure Gemini API key is valid and has sufficient quota

### Contact
For questions or support, please open an issue in the repository or contact the development team.

---

**Built with ❤️ for better health insights**
