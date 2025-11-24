#!/bin/bash

# Quick Test Examples for AI Learning Coach
# Run these commands to test the application

API_URL="http://localhost:8000"
USER_ID="12345678-1234-1234-1234-123456789012"

echo "🧪 AI Learning Coach - Quick Test Examples"
echo "=========================================="
echo ""

# Example 1: Create a Learning Goal
echo "📝 Example 1: Create Learning Goal"
echo "-----------------------------------"
echo "Goal: Learn about Large Language Models and RAG"
echo ""
curl -X POST "$API_URL/api/goals" \
  -H "Content-Type: application/json" \
  -H "x-user-id: $USER_ID" \
  -d '{
    "goal_text": "Learn about Large Language Models, RAG systems, and vector databases",
    "difficulty_level": "intermediate",
    "frequency": "weekly"
  }' | jq '.'

echo ""
echo "✓ Goal created!"
echo ""

# Example 2: Add an RSS Source
echo "📰 Example 2: Add OpenAI Blog RSS Feed"
echo "---------------------------------------"
curl -X POST "$API_URL/api/sources" \
  -H "Content-Type: application/json" \
  -H "x-user-id: $USER_ID" \
  -d '{
    "source_type": "rss",
    "value": "https://openai.com/blog/rss.xml",
    "status": "active"
  }' | jq '.'

echo ""
echo "✓ RSS source added!"
echo ""

# Example 3: Add a YouTube Channel
echo "📺 Example 3: Add AI YouTube Channel"
echo "-------------------------------------"
curl -X POST "$API_URL/api/sources" \
  -H "Content-Type: application/json" \
  -H "x-user-id: $USER_ID" \
  -d '{
    "source_type": "youtube",
    "value": "channel:UCbfYPyITQ-7l4upoX8nvctg",
    "status": "active"
  }' | jq '.'

echo ""
echo "✓ YouTube channel added!"
echo ""

# Example 4: Get Active Goal
echo "🎯 Example 4: View Your Active Goal"
echo "------------------------------------"
curl -s "$API_URL/api/goals/active" \
  -H "x-user-id: $USER_ID" | jq '.'

echo ""

# Example 5: List All Sources
echo "📚 Example 5: View All Your Sources"
echo "------------------------------------"
curl -s "$API_URL/api/sources" \
  -H "x-user-id: $USER_ID" | jq '.sources | length'
echo "sources loaded"

echo ""
echo "=========================================="
echo "✅ All examples completed!"
echo ""
echo "🌐 Visit http://localhost:3000 to see your data in the UI"
echo "📖 API Docs: http://localhost:8000/docs"
echo "=========================================="
