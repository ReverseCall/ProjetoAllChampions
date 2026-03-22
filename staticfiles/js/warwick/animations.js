/*
    Fazer essa brincadeira demandou mais tempo do que eu gostaria de ter dedicado
    Aproveite ;)
 */

function initAnimations(config) {
    const container = document.getElementById(config.emojiContainerId);
    const audio = document.getElementById(config.audioId);
    const dogImg = document.getElementById(config.dogImageId);
    const timerDisplay = document.getElementById(config.timerDisplayId);
    
    // Lista de provabilidades dos icones
    const icons = [
        { url: config.emojiUrl, weight: 90 },
        { url: config.emojiUrl2, weight: 4 },
        { url: config.emojiUrl3, weight: 3 },
        { url: config.emojiUrl4, weight: 2 },
        { url: config.emojiUrl5, weight: 1 }
    ];

    const dog1Url = config.dog1Url;
    const dog2Url = config.dog2Url;
    
    let bounceInterval = null;
    let floatInterval = null;
    const gravity = 0.3;
    let lastTriggered = "";

    // Função para escolher um ícone baseado na probabilidade
    function getRandomIcon() {
        const random = Math.random() * 100;
        let cumulativeWeight = 0;
        for (const icon of icons) {
            cumulativeWeight += icon.weight;
            if (random < cumulativeWeight) {
                return icon.url;
            }
        }
        return icons[0].url;
    }

    // Configurações dos emojis
    function createBouncingEmoji() {
        const emoji = document.createElement('img');
        emoji.src = getRandomIcon();
        emoji.className = 'bouncing-emoji';
        const size = 33 + Math.random() * 10;
        emoji.style.width = size + 'px';
        emoji.style.height = size + 'px';
        emoji.style.objectFit = 'contain';
        let posX = Math.random() * (window.innerWidth - size);
        let posY = window.innerHeight + 50;
        let velX = (Math.random() - 0.5) * 10; 
        let velY = -(12 + Math.random() * 10); 
        let rotation = 0;
        let rotationSpeed = (Math.random() - 0.5) * 10;
        container.appendChild(emoji);
        
        function update() {
            velY += gravity; posX += velX; posY += velY; rotation += rotationSpeed;
            if (posY + size > window.innerHeight) {
                posY = window.innerHeight - size;
                velY = -(8 + Math.random() * 12);
                velX += (Math.random() - 0.5) * 2;
            }
            if (posX <= 0 || posX + size >= window.innerWidth) {
                velX = -velX;
                if (posX <= 0) posX = 0;
                if (posX + size >= window.innerWidth) posX = window.innerWidth - size;
            }
            emoji.style.transform = `translate(${posX}px, ${posY}px) rotate(${rotation}deg)`;
            if (emoji.parentElement) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
        setTimeout(() => {
            emoji.style.transition = 'opacity 1s';
            emoji.style.opacity = '0';
            setTimeout(() => emoji.remove(), 1000);
        }, 4000);
    }

    // --------------------------------
    function createFloatingEmoji() {
        const emoji = document.createElement('img');
        emoji.src = getRandomIcon();
        emoji.className = 'floating-emoji';
        emoji.style.left = Math.random() * 100 + '%';
        emoji.style.setProperty('--random-x', (Math.random() - 0.5) * 300 + 'px');
        emoji.style.setProperty('--random-rotate', (Math.random() - 0.5) * 720 + 'deg');
        emoji.style.width = (60 + Math.random() * 40) + 'px';
        container.appendChild(emoji);
        emoji.addEventListener('animationend', () => emoji.remove());
    }

    function setBounceFlow(active) {
        if (active && !bounceInterval) {
            bounceInterval = setInterval(() => {
                for(let i=0; i < (Math.floor(Math.random()*2)+1); i++) createBouncingEmoji();
            }, 500);
        } else if (!active && bounceInterval) {
            clearInterval(bounceInterval); bounceInterval = null;
        }
    }

    function setFloatFlow(active) {
        if (active && !floatInterval) floatInterval = setInterval(createFloatingEmoji, 400);
        else if (!active && floatInterval) { clearInterval(floatInterval); floatInterval = null; }
    }

    function showDog(side) {
        lastTriggered = side;
        dogImg.classList.remove('dog-left-anim', 'dog-right-anim');
        void dogImg.offsetWidth;
        
        if (side === "left") {
            dogImg.src = dog1Url;
            dogImg.classList.add('dog-left-anim');
        } else {
            dogImg.src = dog2Url;
            dogImg.classList.add('dog-right-anim');
        }
    }

    const stopAll = () => { 
        setBounceFlow(false); 
        setFloatFlow(false); 
        dogImg.classList.remove('dog-left-anim', 'dog-right-anim');
        lastTriggered = "";
    };

    // Eventos
    audio.addEventListener('timeupdate', () => {
        const currentTime = audio.currentTime;
        
        // Atualiza o timer
        if (timerDisplay) {
            const mins = Math.floor(currentTime / 60);
            const secs = Math.floor(currentTime % 60);
            timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }

        // Controle de apareção dos emojis
        setBounceFlow((currentTime >= 7 && currentTime <= 17) || (currentTime >= 28 && currentTime <= 57)); // Sirilepe
        setFloatFlow((currentTime >= 10 && currentTime <= 12) || (currentTime >= 35 && currentTime <= 59)); // Balão

        // Controle DO O! CACHORROOOOUUU
        if (currentTime >= 6 && currentTime < 7) {
            if (lastTriggered !== "left") showDog("left");
        } 
        else if (currentTime >= 27 && currentTime < 28) {
            if (lastTriggered !== "right") showDog("right");
        }
        else {
            lastTriggered = "";
        }
    });

    audio.addEventListener('pause', stopAll);
    audio.addEventListener('ended', stopAll);
}
