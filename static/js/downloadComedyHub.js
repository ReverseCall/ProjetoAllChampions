const form = document.getElementById('downloadForm');
const videoUrl = document.getElementById('videoUrl');
const downloadBtn = document.getElementById('downloadBtn');
const progressBar = document.getElementById('progressBar');
const messageDiv = document.getElementById('message');
const icon = document.querySelector(".logo")
const boop = document.getElementById("click-boop")

let funnyMessages = [];
let messageRotationInterval = null;

// Boop :3
icon.addEventListener("click", () => {
    boop.currentTime = 0; // reinicia o som se clicar rápido
    boop.play();
});


// Carregar as mensagens divertidas ao inicializar
async function loadFunnyMessages() {
    try {
        const response = await fetch('/downloads/api/funny-messages/');
        const data = await response.json();
        funnyMessages = data.messages || [];
    } catch (error) {
        console.error('Erro ao carregar mensagens divertidas:', error);
        funnyMessages = [{ text: 'Preparando seu vídeo...', percentage: 100 }];
    }
}

// Selecionar uma mensagem aleatória baseada na porcentagem
function getRandomMessage() {
    if (funnyMessages.length === 0) return 'Carregando...';
    
    const totalPercentage = funnyMessages.reduce((sum, msg) => sum + msg.percentage, 0);
    let random = Math.random() * totalPercentage;
    
    for (let message of funnyMessages) {
        random -= message.percentage;
        if (random <= 0) {
            return message.text;
        }
    }
    
    return funnyMessages[0].text;
}

// Rotacionar mensagens a cada 3 segundos
function startMessageRotation() {
    if (messageRotationInterval) clearInterval(messageRotationInterval);
    
    updateMessage();
    messageRotationInterval = setInterval(updateMessage, 1500);
}

function updateMessage() {
    const message = getRandomMessage();
    messageDiv.innerHTML = message;
    messageDiv.className = 'message info';
    messageDiv.style.display = 'block';
}

function stopMessageRotation() {
    if (messageRotationInterval) {
        clearInterval(messageRotationInterval);
        messageRotationInterval = null;
    }
}

// Simular o fake delay do download
async function simulateFakeDelay() {
    return new Promise((resolve) => {
        const duration = 8000; // 8 segundos de fake delay
        const startTime = Date.now();
        
        const fakeInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min((elapsed / duration) * 100, 99);
            
            progressBar.style.width = progress + '%';
            
            if (elapsed >= duration) {
                clearInterval(fakeInterval);
                resolve();
            }
        }, 100);
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = videoUrl.value.trim();
    if (!url) {
        showMessage('Por favor, insira uma URL válida', 'error');
        return;
    }

    // Preparar UI
    downloadBtn.disabled = true;
    messageDiv.style.display = 'none';
    progressBar.classList.add('active');
    progressBar.style.width = '0%';
    
    startMessageRotation();

    try {
        // Executa a requisição e o delay visual em paralelo
        const [response] = await Promise.all([
            fetch('/downloads/api/download/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ url: url })
            }),
            simulateFakeDelay()
        ]);

        stopMessageRotation();
        progressBar.style.width = '100%';

        const data = await response.json();

        // Pequeno delay para o usuário ver os 100%
        setTimeout(() => {
            progressBar.classList.remove('active');
            progressBar.style.width = '0%';
        }, 800);

        if (response.ok && data.success) {
            const downloadUrl = data.download_url || '#';
            const successMsg = data.message || 'Vídeo processado com sucesso!';
            showMessage(
                `${successMsg}<br><a href="${downloadUrl}" class="download-link" download>Clique aqui para baixar</a>`,
                'success'
            );
            form.reset();
        } else {
            const errorMsg = data.error || 'Erro desconhecido ao processar download';
            showMessage(`❌ Erro: ${errorMsg}`, 'error');
        }
    } catch (error) {
        stopMessageRotation();
        progressBar.classList.remove('active');
        progressBar.style.width = '0%';
        showMessage(`❌ Erro na requisição: ${error.message}`, 'error');
    } finally {
        downloadBtn.disabled = false;
    }
});

function showMessage(text, type) {
    messageDiv.innerHTML = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Função auxiliar para pegar o CSRF token do Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', loadFunnyMessages);
