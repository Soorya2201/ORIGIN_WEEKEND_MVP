# 🚀 Clarity Health - Full Stack Demo

## Complete MVP Health Dashboard with AI-Powered Insights

This demo showcases the complete **Clarity Health** platform with both backend and frontend components, featuring luxury health UI, AI-powered lab processing, wearable integration, and 24/7 medical support.

## 🎯 Demo Features

### **Backend (FastAPI)**
- ✅ **Lab Processing**: Upload lab results, AI extraction with Gemini Vision
- ✅ **Health Assessment Engine**: Sleep, hydration, nutrition, activity scoring
- ✅ **Wearable Integration**: Apple Watch, Fitbit, Garmin sync
- ✅ **AI Chat Doctor**: 24/7 health support with medical context
- ✅ **Data Lake Architecture**: Flexible JSON storage for all health data
- ✅ **Rule-Based Insights**: Deterministic health recommendations
- ✅ **PII Redaction**: Privacy-focused data processing

### **Frontend (React + Material-UI)**
- ✅ **Luxury Health UI**: Clean, minimalist design with premium aesthetics
- ✅ **Dashboard**: Health metrics, trends, overall health score
- ✅ **Upload Page**: Drag-and-drop lab results with AI processing
- ✅ **Wearable Sync**: Device management and data synchronization
- ✅ **AI Chat**: Real-time health assistant with context awareness
- ✅ **Responsive Design**: Mobile-first, accessible interface

## 🚀 Quick Start (Single Command)

### **Option 1: Full Stack (Recommended)**
```bash
./start -local
```
This will:
- Start FastAPI backend on `http://127.0.0.1:8000`
- Start React frontend on `http://localhost:3000`
- Set up databases, dependencies, and all services
- Provide health check URLs and service status

### **Option 2: Backend Only**
```bash
cd backend
./start -local
```
This will:
- Set up virtual environment
- Install dependencies
- Start PostgreSQL and Redis
- Run database migrations
- Start FastAPI server on `http://127.0.0.1:8000`

### **Option 3: Frontend Only**
```bash
cd frontend
./start -local
```
This will:
- Check Node.js version (requires 18+)
- Install dependencies if needed
- Verify backend connection
- Start React dev server on `http://localhost:3000`

## 🛠️ Development Commands

### **Make Commands (Root Level)**
```bash
make start     # Start both backend and frontend
make stop      # Stop all services
make dev       # Start development servers
make build     # Build both backend and frontend
make test      # Run all tests
make clean     # Clean all build artifacts
make install   # Install all dependencies
make backend   # Start only backend
make frontend  # Start only frontend
make health    # Check service health
```

### **Individual Service Commands**
```bash
# Backend
cd backend && make dev      # Start backend
cd backend && make test     # Run backend tests
cd backend && make build    # Build backend

# Frontend  
cd frontend && make dev     # Start frontend
cd frontend && make test    # Run frontend tests
cd frontend && make build   # Build frontend
```

## 📱 Demo Flow

### **1. Dashboard Overview**
- Navigate to `http://localhost:3000`
- View health metrics: Sleep, Hydration, Nutrition, Activity
- See overall health score with trend indicators
- Review AI-generated recommendations

### **2. Upload Lab Results**
- Go to Upload page
- Drag and drop lab result files (PDF, JPG, PNG)
- Watch AI processing with Gemini Vision
- View extracted health data in data lake

### **3. Connect Wearables**
- Navigate to Wearables page
- Add Apple Watch, Fitbit, or Garmin device
- Sync health data automatically
- Monitor sync status and data types

### **4. AI Health Chat**
- Open AI Doctor page
- Ask health questions with full context
- Get personalized recommendations
- Use quick question buttons for common queries

## 🔧 API Endpoints Demo

### **User Management**
```bash
# Create demo user
curl -X POST "http://127.0.0.1:8000/mvp/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@clarityhealth.com", "name": "Demo User"}'

# Get dashboard data
curl "http://127.0.0.1:8000/mvp/dashboard/e9568735-bcaf-40fa-9b1d-0dda2255e6c4"
```

### **Health Assessment**
```bash
# Calculate health assessment
curl -X POST "http://127.0.0.1:8000/mvp/health-assessments/?user_id=e9568735-bcaf-40fa-9b1d-0dda2255e6c4"

# Get assessment history
curl "http://127.0.0.1:8000/mvp/health-assessments/e9568735-bcaf-40fa-9b1d-0dda2255e6c4"
```

### **Wearable Integration**
```bash
# Add wearable device
curl -X POST "http://127.0.0.1:8000/mvp/wearables/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "e9568735-bcaf-40fa-9b1d-0dda2255e6c4", "device_type": "apple_watch", "device_id": "demo-watch-001"}'

# Sync wearable data
curl -X POST "http://127.0.0.1:8000/mvp/wearables/sync?user_id=e9568735-bcaf-40fa-9b1d-0dda2255e6c4" \
  -H "Content-Type: application/json" \
  -d '{"device_type": "apple_watch", "device_id": "demo-watch-001", "sync_all_data": true}'
```

### **AI Chat**
```bash
# Send chat message
curl -X POST "http://127.0.0.1:8000/mvp/chat/message?user_id=e9568735-bcaf-40fa-9b1d-0dda2255e6c4" \
  -H "Content-Type: application/json" \
  -d '{"message": "What do my recent lab results mean?", "include_health_context": true}'
```

### **Data Lake**
```bash
# Store health data
curl -X POST "http://127.0.0.1:8000/mvp/data-lake/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "e9568735-bcaf-40fa-9b1d-0dda2255e6c4", "data_type": "lab_results", "data_source": "uploaded_file", "raw_data": {"test": "value"}}'

# Get health data
curl "http://127.0.0.1:8000/mvp/data-lake/e9568735-bcaf-40fa-9b1d-0dda2255e6c4"
```

## 🧪 Testing

### **Backend Tests**
```bash
cd backend
pytest tests/test_mvp.py -v
```

### **Frontend Tests**
```bash
cd frontend
npm test
```

### **Full Integration Test**
```bash
cd backend
python run_full_test.py
```

## 📊 Demo Data

The system includes demo data for:
- **User Profile**: Demo user with health metrics
- **Health Assessments**: Sample sleep, hydration, nutrition scores
- **Wearable Data**: Mock Apple Watch and Fitbit data
- **Lab Results**: Sample lab data for AI processing
- **Chat Sessions**: AI conversation history

## 🎨 UI/UX Highlights

### **Luxury Health Design**
- **Color Palette**: Forest green primary, professional blue secondary
- **Typography**: Inter font family for premium readability
- **Animations**: Smooth transitions with Framer Motion
- **Responsive**: Mobile-first design with breakpoints
- **Accessibility**: WCAG compliant with proper contrast

### **Health-Focused Features**
- **Progress Indicators**: Visual health score representations
- **Trend Analysis**: Up/down/stable indicators for health metrics
- **Contextual Information**: Relevant health insights and recommendations
- **Real-time Updates**: Live data synchronization
- **Intuitive Navigation**: Clear page structure and user flow

## 🔍 Technical Architecture

### **Backend Stack**
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database with JSON support
- **SQLAlchemy 2.x**: ORM with Alembic migrations
- **Celery + Redis**: Asynchronous task processing
- **Google Gemini AI**: Multimodal AI for lab processing
- **Pydantic v2**: Data validation and serialization

### **Frontend Stack**
- **React 19**: Latest React with TypeScript
- **Material-UI**: Component library with custom theme
- **Framer Motion**: Animation and gesture library
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

## 🚀 Production Readiness

### **Security**
- ✅ PII redaction for sensitive data
- ✅ Input validation and sanitization
- ✅ Proper error handling
- ✅ Environment variable management

### **Performance**
- ✅ Database indexing and optimization
- ✅ Async processing with Celery
- ✅ Frontend code splitting
- ✅ Efficient API calls

### **Scalability**
- ✅ Microservices architecture
- ✅ Horizontal scaling support
- ✅ Database connection pooling
- ✅ Caching strategies

## 📝 Configuration

### **Environment Variables**
```bash
# Backend (.env)
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:pass@localhost:5434/health_db
REDIS_URL=redis://localhost:6379/0

# Frontend (built-in)
REACT_APP_API_URL=http://127.0.0.1:8000
```

## 🎯 Demo Scenarios

### **Scenario 1: New User Onboarding**
1. User visits dashboard
2. System creates demo user profile
3. User uploads lab results
4. AI processes and extracts data
5. Health assessment is calculated
6. Dashboard shows personalized insights

### **Scenario 2: Wearable Integration**
1. User adds Apple Watch device
2. System syncs health data
3. Data is stored in health data lake
4. Health scores are updated
5. Trends are calculated and displayed

### **Scenario 3: AI Health Consultation**
1. User asks health question in chat
2. AI accesses all health context
3. Personalized response is generated
4. Recommendations are provided
5. Follow-up questions are suggested

## 🏆 Success Metrics

- ✅ **All MVP Features**: Dashboard, Upload, Wearables, AI Chat
- ✅ **API Integration**: All 20+ endpoints working
- ✅ **AI Processing**: Gemini Vision lab extraction
- ✅ **Data Persistence**: PostgreSQL with proper schemas
- ✅ **Real-time Updates**: Live health data synchronization
- ✅ **Luxury UI**: Premium health-focused design
- ✅ **Mobile Responsive**: Works on all device sizes
- ✅ **Error Handling**: Graceful error management
- ✅ **Testing**: Comprehensive test coverage
- ✅ **Documentation**: Complete setup and usage guides

## 🎉 Demo Complete!

The **Clarity Health** platform is now fully functional with:
- **Backend**: FastAPI with AI processing, health assessment, and data lake
- **Frontend**: React with luxury health UI and comprehensive features
- **Integration**: Seamless API communication and real-time updates
- **Testing**: Full test coverage and validation
- **Documentation**: Complete setup and usage instructions

**Ready for production deployment and user testing!** 🚀
