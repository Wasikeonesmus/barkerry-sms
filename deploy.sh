#!/bin/bash

# Exit on error
set -e

echo "Starting Upendo Bakery deployment..."

# Create necessary directories
mkdir -p logs
mkdir -p staticfiles
mkdir -p media

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Create PostgreSQL database and user
echo "Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE upendo_bakery;"
sudo -u postgres psql -c "CREATE USER upendo_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "ALTER ROLE upendo_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE upendo_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE upendo_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE upendo_bakery TO upendo_user;"

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set up environment variables
echo "Setting up environment variables..."
cp .env.prod .env

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Set up SSL certificates (if not already done)
echo "Setting up SSL certificates..."
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up Nginx
echo "Setting up Nginx..."
sudo cp nginx/upendo_bakery.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/upendo_bakery.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up Gunicorn service
echo "Setting up Gunicorn service..."
sudo tee /etc/systemd/system/upendo_bakery.service << EOF
[Unit]
Description=Upendo Bakery Gunicorn Service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn -c gunicorn_config.py upendo_bakery.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable services
echo "Starting services..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start upendo_bakery
sudo systemctl enable upendo_bakery

echo "Deployment completed successfully!"
echo "Please make sure to:"
echo "1. Update the .env file with your actual values"
echo "2. Update the domain names in nginx configuration"
echo "3. Set up proper backup system"
echo "4. Monitor the logs in /var/log/nginx/ and logs/ directories" 