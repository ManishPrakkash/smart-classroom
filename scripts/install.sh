#!/bin/bash
# Smart Classroom Installation Script
# Run this script on your Raspberry Pi 5

set -e  # Exit on error

echo "======================================"
echo "Smart Classroom Installation"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev git

# Setup project directory
PROJECT_DIR="$HOME/smart-classroom"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    echo "Please clone the repository first:"
    echo "  git clone https://github.com/ManishPrakkash/smart-classroom.git"
    exit 1
fi

cd "$PROJECT_DIR"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    
    # Generate random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    # Update .env file
    sed -i "s/your-secure-random-secret-key-here/$SECRET_KEY/" .env
    
    echo ""
    echo "⚠️  IMPORTANT: Default credentials created!"
    echo "   Username: admin"
    echo "   Password: classroom123"
    echo ""
    echo "   Please change these in the .env file:"
    echo "   nano $PROJECT_DIR/.env"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Set GPIO permissions
echo "🔧 Setting GPIO permissions..."
sudo usermod -a -G gpio,dialout,i2c,spi $USER

# Test lgpio installation
echo "🧪 Testing lgpio library..."
python3 << EOF
try:
    import lgpio
    print("✅ lgpio imported successfully")
except ImportError as e:
    print("❌ lgpio import failed:", e)
    exit(1)
EOF

echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review and update credentials in .env file"
echo "2. Connect your relay module according to wiring diagram"
echo "3. Test the application:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python3 app/app.py"
echo ""
echo "4. Access web interface at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "5. Setup auto-start service (optional):"
echo "   sudo ./scripts/setup_service.sh"
echo ""
echo "⚠️  You may need to logout/login for GPIO permissions to take effect"
echo ""
