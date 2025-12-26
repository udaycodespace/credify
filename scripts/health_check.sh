#!/bin/bash

# Health check script
URL=${1:-http://localhost:5000}

echo "🔍 Checking health of $URL..."

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $response -eq 200 ]; then
    echo "✅ Application is healthy (HTTP $response)"
    exit 0
else
    echo "❌ Application is unhealthy (HTTP $response)"
    exit 1
fi
