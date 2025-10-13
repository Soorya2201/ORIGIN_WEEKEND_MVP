#!/bin/bash

# Clarity Health - Complete Workflow Test
# This script tests the entire workflow: Upload -> AI Processing -> Data Lake -> Chat Context

echo "🧪 Testing Clarity Health Complete Workflow"
echo "=========================================="

# Configuration
BACKEND_URL="http://127.0.0.1:8000"
FRONTEND_URL="http://localhost:3000"
DEMO_USER_ID="e9568735-bcaf-40fa-9b1d-0dda2255e6c4"
SAMPLE_FILE="sample_lab_results.png"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_backend_health() {
    echo -e "\n${YELLOW}1. Testing Backend Health...${NC}"
    if curl -s "$BACKEND_URL/docs" > /dev/null; then
        echo -e "${GREEN}✅ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend is not running${NC}"
        return 1
    fi
}

test_frontend_health() {
    echo -e "\n${YELLOW}2. Testing Frontend Health...${NC}"
    if curl -s "$FRONTEND_URL" > /dev/null; then
        echo -e "${GREEN}✅ Frontend is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Frontend is not running${NC}"
        return 1
    fi
}

test_file_upload() {
    echo -e "\n${YELLOW}3. Testing File Upload...${NC}"
    if [ ! -f "$SAMPLE_FILE" ]; then
        echo -e "${RED}❌ Sample file $SAMPLE_FILE not found${NC}"
        return 1
    fi
    
    UPLOAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/upload/" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$SAMPLE_FILE")
    
    FILE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_id')
    
    if [ "$FILE_ID" != "null" ] && [ "$FILE_ID" != "" ]; then
        echo -e "${GREEN}✅ File uploaded successfully (ID: $FILE_ID)${NC}"
        echo "$FILE_ID" > /tmp/test_file_id
        return 0
    else
        echo -e "${RED}❌ File upload failed${NC}"
        echo "$UPLOAD_RESPONSE"
        return 1
    fi
}

test_ai_processing() {
    echo -e "\n${YELLOW}4. Testing AI Processing...${NC}"
    FILE_ID=$(cat /tmp/test_file_id 2>/dev/null)
    
    if [ -z "$FILE_ID" ]; then
        echo -e "${RED}❌ No file ID available for processing${NC}"
        return 1
    fi
    
    PROCESS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/labs/ingest_from_media?file_id=$FILE_ID" \
        -H "accept: application/json")
    
    LAB_COUNT=$(echo "$PROCESS_RESPONSE" | jq '.labs | length')
    HAS_PROVENANCE=$(echo "$PROCESS_RESPONSE" | jq -r '.provenance != null')
    
    if [ "$LAB_COUNT" -gt 0 ] || [ "$HAS_PROVENANCE" = "true" ]; then
        echo -e "${GREEN}✅ AI processing successful - extracted $LAB_COUNT lab results${NC}"
        return 0
    else
        echo -e "${RED}❌ AI processing failed${NC}"
        echo "$PROCESS_RESPONSE"
        return 1
    fi
}

test_data_lake_storage() {
    echo -e "\n${YELLOW}5. Testing Data Lake Storage...${NC}"
    FILE_ID=$(cat /tmp/test_file_id 2>/dev/null)
    
    if [ -z "$FILE_ID" ]; then
        echo -e "${RED}❌ No file ID available for data lake storage${NC}"
        return 1
    fi
    
    # Store in data lake
    STORAGE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/mvp/data-lake/" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$DEMO_USER_ID\",
            \"data_type\": \"lab_results\",
            \"data_source\": \"uploaded_file\",
            \"raw_data\": {
                \"file_id\": \"$FILE_ID\",
                \"file_name\": \"$SAMPLE_FILE\",
                \"file_type\": \"image/png\",
                \"file_size\": 2570223,
                \"extracted_data\": {\"test\": \"workflow_test\"}
            },
            \"confidence_score\": 0.9,
            \"validation_status\": \"validated\",
            \"tags\": [\"lab_results\", \"uploaded\", \"processed\", \"workflow_test\"]
        }")
    
    STORAGE_ID=$(echo "$STORAGE_RESPONSE" | jq -r '.id')
    
    if [ "$STORAGE_ID" != "null" ] && [ "$STORAGE_ID" != "" ]; then
        echo -e "${GREEN}✅ Data stored in data lake successfully (ID: $STORAGE_ID)${NC}"
        return 0
    else
        echo -e "${RED}❌ Data lake storage failed${NC}"
        echo "$STORAGE_RESPONSE"
        return 1
    fi
}

test_data_lake_retrieval() {
    echo -e "\n${YELLOW}6. Testing Data Lake Retrieval...${NC}"
    
    RETRIEVAL_RESPONSE=$(curl -s "$BACKEND_URL/mvp/data-lake/$DEMO_USER_ID?data_type=lab_results&limit=10")
    
    ENTRY_COUNT=$(echo "$RETRIEVAL_RESPONSE" | jq '.entries | length')
    
    if [ "$ENTRY_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Data lake retrieval successful - found $ENTRY_COUNT entries${NC}"
        return 0
    else
        echo -e "${RED}❌ Data lake retrieval failed${NC}"
        echo "$RETRIEVAL_RESPONSE"
        return 1
    fi
}

test_chat_context() {
    echo -e "\n${YELLOW}7. Testing Chat with Health Context...${NC}"
    
    CHAT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/mvp/chat/message?user_id=$DEMO_USER_ID" \
        -H "Content-Type: application/json" \
        -d '{
            "message": "What are my recent lab results?",
            "include_health_context": true
        }')
    
    MESSAGE_LENGTH=$(echo "$CHAT_RESPONSE" | jq -r '.message | length')
    HAS_CONTEXT=$(echo "$CHAT_RESPONSE" | jq -r '.health_context_used != null')
    
    if [ "$MESSAGE_LENGTH" -gt 50 ] && [ "$HAS_CONTEXT" = "true" ]; then
        echo -e "${GREEN}✅ Chat with health context successful${NC}"
        echo -e "${GREEN}   - Response length: $MESSAGE_LENGTH characters${NC}"
        echo -e "${GREEN}   - Health context included: $HAS_CONTEXT${NC}"
        return 0
    else
        echo -e "${RED}❌ Chat with health context failed${NC}"
        echo "$CHAT_RESPONSE"
        return 1
    fi
}

test_dashboard_data() {
    echo -e "\n${YELLOW}8. Testing Dashboard Data...${NC}"
    
    DASHBOARD_RESPONSE=$(curl -s "$BACKEND_URL/mvp/dashboard/$DEMO_USER_ID")
    
    HAS_METRICS=$(echo "$DASHBOARD_RESPONSE" | jq -r '.health_metrics != null')
    HAS_ACTIVITIES=$(echo "$DASHBOARD_RESPONSE" | jq -r '.recent_activities != null')
    
    if [ "$HAS_METRICS" = "true" ] && [ "$HAS_ACTIVITIES" = "true" ]; then
        echo -e "${GREEN}✅ Dashboard data retrieval successful${NC}"
        echo -e "${GREEN}   - Health metrics available: $HAS_METRICS${NC}"
        echo -e "${GREEN}   - Recent activities available: $HAS_ACTIVITIES${NC}"
        return 0
    else
        echo -e "${RED}❌ Dashboard data retrieval failed${NC}"
        echo "$DASHBOARD_RESPONSE"
        return 1
    fi
}

# Main test execution
main() {
    echo "Starting comprehensive workflow test..."
    
    TESTS_PASSED=0
    TESTS_TOTAL=8
    
    test_backend_health && ((TESTS_PASSED++))
    test_frontend_health && ((TESTS_PASSED++))
    test_file_upload && ((TESTS_PASSED++))
    test_ai_processing && ((TESTS_PASSED++))
    test_data_lake_storage && ((TESTS_PASSED++))
    test_data_lake_retrieval && ((TESTS_PASSED++))
    test_chat_context && ((TESTS_PASSED++))
    test_dashboard_data && ((TESTS_PASSED++))
    
    # Cleanup
    rm -f /tmp/test_file_id
    
    # Results
    echo -e "\n${YELLOW}=========================================="
    echo -e "WORKFLOW TEST RESULTS"
    echo -e "==========================================${NC}"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}/$TESTS_TOTAL"
    
    if [ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Complete workflow is working!${NC}"
        echo -e "\n${GREEN}✅ Upload → AI Processing → Data Lake → Chat Context${NC}"
        echo -e "\n${YELLOW}You can now:${NC}"
        echo -e "  • Upload lab results through the frontend"
        echo -e "  • View processed results in the Upload page"
        echo -e "  • Chat with AI about your health data"
        echo -e "  • View health metrics on the Dashboard"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed. Please check the errors above.${NC}"
        exit 1
    fi
}

# Run the tests
main "$@"
