class ChatBot {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.clearButton = document.getElementById('clearChat');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Clear chat
        this.clearButton.addEventListener('click', () => this.clearChat());
        
        // Auto-resize input and update send button state
        this.messageInput.addEventListener('input', () => {
            this.updateSendButtonState();
        });
        
        // Initial state
        this.updateSendButtonState();
    }

    updateSendButtonState() {
        const hasMessage = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasMessage;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input and disable send button
        this.messageInput.value = '';
        this.updateSendButtonState();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Call your API here
            const response = await this.callAPI(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response to chat
            this.addMessage(response, 'bot');
            
        } catch (error) {
            console.error('API Error:', error);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add error message
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    async callAPI(message) {
        // Replace this with your actual API call
        // Example API structure:
        /*
        const response = await fetch('YOUR_API_ENDPOINT', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer YOUR_API_KEY' // if needed
            },
            body: JSON.stringify({
                message: message,
                // Add other parameters as needed
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response; // Adjust based on your API response structure
        */

        // Simulated API response for demo purposes
        // Remove this when implementing your actual API
        return new Promise((resolve) => {
            setTimeout(() => {
                const responses = [
                    "That's an interesting question! Let me think about that...",
                    "I understand what you're asking. Here's what I think:",
                    "Great point! Based on what you've shared:",
                    "Thanks for asking! Here's my response:",
                    "I see what you mean. Let me help you with that:"
                ];
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                resolve(randomResponse + " " + this.generateSimulatedResponse(message));
            }, 1000 + Math.random() * 2000); // Random delay between 1-3 seconds
        });
    }

    // Remove this method when implementing your actual API
    generateSimulatedResponse(userMessage) {
        const responses = [
            "This is a simulated response to demonstrate the chatbot interface.",
            "Your API integration will replace this placeholder response.",
            "The chatbot is working correctly and ready for your API!",
            "This demonstrates how the bot will respond to your messages.",
            "Replace the callAPI method with your actual API endpoint."
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const currentTime = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        if (sender === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <span>AI</span>
                </div>
                <div class="message-content">
                    <p>${this.escapeHtml(text)}</p>
                    <span class="message-time">${currentTime}</span>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${this.escapeHtml(text)}</p>
                    <span class="message-time">${currentTime}</span>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    clearChat() {
        // Keep only the initial welcome message
        const welcomeMessage = this.chatMessages.querySelector('.message');
        this.chatMessages.innerHTML = '';
        if (welcomeMessage) {
            this.chatMessages.appendChild(welcomeMessage);
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatBot();
});

// Add some additional utility functions if needed

// Function to format messages with basic markdown support (optional)
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
        .replace(/`(.*?)`/g, '<code>$1</code>') // Inline code
        .replace(/\n/g, '<br>'); // Line breaks
}

// Function to validate API response (optional)
function validateAPIResponse(response) {
    if (!response || typeof response !== 'string') {
        throw new Error('Invalid API response format');
    }
    return response.trim();
}