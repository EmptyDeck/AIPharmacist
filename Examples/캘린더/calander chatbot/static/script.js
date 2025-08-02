class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        
        this.init();
    }
    
    init() {
        // 웰컴 메시지 시간 설정
        document.getElementById('welcomeTime').textContent = this.getCurrentTime();
        
        // 이벤트 리스너 설정
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // 자동 높이 조절
        this.messageInput.addEventListener('input', () => this.adjustTextareaHeight());
        
        // 초기 포커스
        this.messageInput.focus();
    }
    
    adjustTextareaHeight() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // UI 업데이트
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.showLoading(true);
        this.sendButton.disabled = true;
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.addMessage('ai', data.response);
            } else {
                this.addMessage('ai', data.error || '오류가 발생했습니다.');
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('ai', '네트워크 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            this.showLoading(false);
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }
    
    addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = sender === 'user' ? 
            `<strong>You:</strong> ${this.escapeHtml(content)}` : 
            `<strong>AI:</strong> ${this.escapeHtml(content)}`;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showLoading(show) {
        if (show) {
            this.loadingIndicator.classList.add('show');
        } else {
            this.loadingIndicator.classList.remove('show');
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
