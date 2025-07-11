let userId = 'user_' + Math.random().toString(36).substr(2, 9);

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, 'user');
    input.value = '';
    
    showLoading(true);
    
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        
        if (data.success) {
            const response = data.response;
            addBotMessage(response.message, response.suggestions, response.type);
        } else {
            addBotMessage('Entschuldigung, es ist ein Fehler aufgetreten.', [], 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        addBotMessage('Entschuldigung, es ist ein Fehler aufgetreten.', [], 'error');
        console.error('Error:', error);
    });
}

function addMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(message, suggestions, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message bot-message`;
    
    if (type === 'weather_info') {
        messageDiv.innerHTML = `<div class="weather-info">${message}</div>`;
    } else if (type === 'hotel_results') {
        const messageWithLinks = message.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" style="color: #667eea; text-decoration: underline;">$1</a>'
        );
        messageDiv.innerHTML = `<div class="hotel-results">${messageWithLinks}</div>`;
    } else if (type === 'error') {
        messageDiv.innerHTML = `<div class="error-message">${message}</div>`;
    } else if (type === 'success') {
        messageDiv.innerHTML = `<div class="success-message">${message}</div>`;
    } else {
        messageDiv.textContent = message;
    }
    
    chatMessages.appendChild(messageDiv);
    
    if (suggestions && suggestions.length > 0) {
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'suggestions';
        
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'suggestion-btn';
            button.textContent = suggestion;
            button.onclick = () => {
                document.getElementById('messageInput').value = suggestion;
                sendMessage();
            };
            suggestionsDiv.appendChild(button);
        });
        
        messageDiv.appendChild(suggestionsDiv);
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('show');
    } else {
        loading.classList.remove('show');
    }
}

function sendSuggestion(suggestion) {
    document.getElementById('messageInput').value = suggestion;
    sendMessage();
} 