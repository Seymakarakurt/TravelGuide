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
            addBotMessage(response.message, response.suggestions, response.type, response.tool_used);
            
            const lastBotMessage = document.querySelector('.bot-message:last-child');
            if (lastBotMessage) {
                lastBotMessage.dataset.userMessage = message;
            }

            if (data.interaction_id && response.type !== 'error') {
                setTimeout(() => {
                }, 2000);
            }
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

function addBotMessage(message, suggestions, type, toolUsed = '') {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    messageDiv.dataset.aiResponse = message;
    messageDiv.dataset.toolUsed = toolUsed;
    messageDiv.dataset.responseType = type;
    
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
    } else if (type === 'rag_response') {
        messageDiv.innerHTML = `<div class="rag-response">${message}</div>`;
    } else if (type === 'mcp_response') {
        messageDiv.innerHTML = `<div class="mcp-response">${message}</div>`;
    } else {
        messageDiv.textContent = message;
    }
    
    const lastUserMessage = document.querySelector('.user-message:last-child');
    if (lastUserMessage) {
        messageDiv.dataset.userMessage = lastUserMessage.textContent;
    }
    
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-inline';
    feedbackDiv.innerHTML = `
      <div class="feedback-options">
        <button class="feedback-btn" onclick="submitFeedbackDirect('thumbs_up', this)">Gut</button>
        <button class="feedback-btn" onclick="submitFeedbackDirect('thumbs_down', this)">Schlecht</button>
        <button class="feedback-btn" onclick="submitFeedbackDirect('incomplete', this)">Unvollständig</button>
        <button class="feedback-btn" onclick="submitFeedbackDirect('inaccurate', this)">Ungenau</button>
      </div>
      <div class="feedback-actions">
      </div>
    `;
    messageDiv.appendChild(feedbackDiv);
    
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

let selectedFeedbacks = new Map();

window.submitFeedbackDirect = function(type, el) {
    const feedbackContainer = el.closest('.feedback-inline');
    const botMessage = el.closest('.bot-message');
    const messageId = botMessage.dataset.messageId || Math.random().toString(36).substr(2, 9);
    botMessage.dataset.messageId = messageId;
    
    if (el.classList.contains('selected')) {
        el.classList.remove('selected');
        el.style.opacity = '0.7';
        el.style.color = '';
        el.disabled = false;
        
        if (selectedFeedbacks.has(messageId)) {
            const feedbacks = selectedFeedbacks.get(messageId);
            const index = feedbacks.indexOf(type);
            if (index > -1) {
                feedbacks.splice(index, 1);
            }
            if (feedbacks.length === 0) {
                selectedFeedbacks.delete(messageId);
            }
        }
    } else {
        el.classList.add('selected');
        el.style.opacity = '1';
        el.style.color = '#667eea';
        el.disabled = true;
        
        if (!selectedFeedbacks.has(messageId)) {
            selectedFeedbacks.set(messageId, []);
        }
        selectedFeedbacks.get(messageId).push(type);
    }
    
    const submitBtn = feedbackContainer.querySelector('.feedback-submit-btn');
    if (selectedFeedbacks.has(messageId) && selectedFeedbacks.get(messageId).length > 0) {
        if (!submitBtn) {
            const submitButton = document.createElement('button');
            submitButton.className = 'feedback-submit-btn';
            submitButton.textContent = 'Abschicken';
            submitButton.onclick = () => submitAllFeedbacks(messageId, feedbackContainer);
            feedbackContainer.querySelector('.feedback-actions').appendChild(submitButton);
        }
    } else {
        if (submitBtn) {
            submitBtn.remove();
        }
    }
    

};

function submitAllFeedbacks(messageId, feedbackContainer) {
    const botMessage = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!botMessage || !selectedFeedbacks.has(messageId)) {
        alert('Keine Feedbacks zum Senden vorhanden.');
        return;
    }
    
    const feedbacks = selectedFeedbacks.get(messageId);
    const userMessage = botMessage.dataset.userMessage || 'unbekannt';
    const aiResponse = botMessage.dataset.aiResponse || botMessage.textContent || 'unbekannt';
    const toolUsed = botMessage.dataset.toolUsed || '';
    const responseType = botMessage.dataset.responseType || '';
    
    const feedbackData = {
        user_message: userMessage,
        ai_response: aiResponse,
        feedback_types: feedbacks,
        specific_feedback: '',
        tool_used: toolUsed,
        response_type: responseType
    };
    
    const submitBtn = feedbackContainer.querySelector('.feedback-submit-btn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Wird gesendet...';
    }
    
    fetch('/api/feedback/multiple', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFeedbackThankYouInline(feedbackContainer);
            feedbackContainer.querySelectorAll('.feedback-btn').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
            });
            if (submitBtn) {
                submitBtn.remove();
            }
            selectedFeedbacks.delete(messageId);
        } else {
            alert('Fehler beim Senden des Feedbacks: ' + (data.error || 'Unbekannter Fehler'));
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Abschicken';
            }
        }
    })
    .catch(error => {
        console.error('Feedback error:', error);
        alert('Fehler beim Senden des Feedbacks. Bitte versuchen Sie es erneut.');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Abschicken';
        }
    });
}

function showFeedbackThankYouInline(parent) {
    const thankYou = document.createElement('span');
    thankYou.className = 'feedback-thankyou-inline';
    thankYou.textContent = 'Danke für Ihr Feedback!';
    thankYou.style.marginLeft = '10px';
    thankYou.style.color = '#28a745';
    thankYou.style.fontWeight = 'bold';
    parent.appendChild(thankYou);
    setTimeout(() => { thankYou.remove(); }, 3000);
} 