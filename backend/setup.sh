#!/bin/bash

echo "🚀 Setting up AI Code Review Backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
echo "📦 Installing dependencies..."
pip install -r requirements/development.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file - please update with your configuration"
fi

echo ""
echo "🎉 Backend setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"  
echo "  python main.py"
echo ""
echo "The API will be available at:"
echo "  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
