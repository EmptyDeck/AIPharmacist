#!/bin/bash

echo "🚀 DuckDNS + SSL 자동 설정 스크립트"
echo "=================================="

# 변수 설정
DOMAIN="dr-ibm.duckdns.org"
BACKEND_PORT="8001"

echo "📦 패키지 업데이트 및 Nginx 설치..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

echo "📝 Nginx 설정 파일 생성..."
sudo tee /etc/nginx/sites-available/dr-ibm > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "🔗 Nginx 설정 활성화..."
sudo ln -sf /etc/nginx/sites-available/dr-ibm /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "✅ Nginx 설정 테스트..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "📄 Nginx 재시작..."
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    echo "🔒 SSL 인증서 발급..."
    echo "주의: 이메일 입력 및 약관 동의가 필요합니다."
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || {
        echo "❌ SSL 인증서 발급 실패. 수동으로 실행하세요:"
        echo "sudo certbot --nginx -d $DOMAIN"
    }
    
    echo "⏰ SSL 인증서 자동 갱신 설정..."
    sudo systemctl enable certbot.timer
    
    echo ""
    echo "🎉 설정 완료!"
    echo "▶ HTTP: http://$DOMAIN"
    echo "▶ HTTPS: https://$DOMAIN"
    echo "▶ API Docs: https://$DOMAIN/docs"
    echo ""
    echo "📋 다음 단계:"
    echo "1. Docker 컨테이너 시작: docker-compose up -d"
    echo "2. Google OAuth에 https://$DOMAIN/auth/google/callback-enhanced 등록"
    echo ""
else
    echo "❌ Nginx 설정 오류. 설정을 확인하세요."
    exit 1
fi