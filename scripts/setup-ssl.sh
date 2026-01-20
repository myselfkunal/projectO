#!/bin/bash
# SSL/TLS Certificate Setup with Let's Encrypt
# This script sets up automatic certificate renewal using Certbot

set -e

DOMAIN=${1:-"unilink.example.com"}
EMAIL=${2:-"admin@unilink.com"}
STAGING=${3:-"--staging"}  # Use --staging for testing, remove for production

echo "================================================"
echo "UniLink SSL/TLS Certificate Setup"
echo "================================================"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Mode: ${STAGING:---production}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: This script must be run as root"
  exit 1
fi

# Install Certbot if not present
echo "Installing Certbot..."
if ! command -v certbot &> /dev/null; then
    apt-get update
    apt-get install -y certbot python3-certbot-nginx python3-certbot-dns-cloudflare
fi

# Obtain certificate
echo ""
echo "Requesting certificate from Let's Encrypt..."

certbot certonly \
  --nginx \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  $STAGING \
  --preferred-challenges http

if [ $? -eq 0 ]; then
  echo ""
  echo "Certificate obtained successfully!"
  CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
  echo "Certificate: $CERT_PATH"
  echo "Private Key: $KEY_PATH"
else
  echo "ERROR: Failed to obtain certificate"
  exit 1
fi

# Setup automatic renewal
echo ""
echo "Setting up automatic certificate renewal..."

# Create renewal hook
mkdir -p /etc/letsencrypt/renewal-hooks/post

cat > /etc/letsencrypt/renewal-hooks/post/nginx-reload.sh <<'EOF'
#!/bin/bash
nginx -s reload
EOF

chmod +x /etc/letsencrypt/renewal-hooks/post/nginx-reload.sh

# Setup cron job for renewal
echo "Setting up cron job for daily renewal check..."
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
  (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet --renew-hook /etc/letsencrypt/renewal-hooks/post/nginx-reload.sh") | crontab -
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Update nginx configuration to use:"
echo "   - ssl_certificate: $CERT_PATH"
echo "   - ssl_certificate_key: $KEY_PATH"
echo ""
echo "2. Restart nginx:"
echo "   sudo nginx -s reload"
echo ""
echo "3. Test certificate renewal:"
echo "   sudo certbot renew --dry-run"
echo ""
echo "Certificates will automatically renew 30 days before expiration."
echo ""
