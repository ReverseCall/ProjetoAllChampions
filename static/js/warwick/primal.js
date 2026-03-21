const container = document.getElementById("container");
const message1 = document.getElementById("message1")
const message2 = document.getElementById("message2")
const yes = document.getElementById("yes");
const no = document.getElementById("no");
const music = document.getElementById("music");
const buttons = document.querySelector(".buttons");

const vizContainer = document.getElementById("visualizer-container");
const canvas = document.getElementById("visualizer-canvas");
const ctx = canvas.getContext("2d");
const textCanvas = document.getElementById("textCanvas");
const tCtx = textCanvas.getContext("2d");

let audioCtx, analyser, source, dataArray;

const CONFIG = {
  numBars: 100,
  innerRadius: 115,
  maxBarHeight: 200,
  barWidth: 5,
  rotationOffset: -Math.PI / 2,
  text: "AAAAAAUUUU!!!!!",
  pulseIntensity: 1.0
};

const assets = document.getElementById("assets");

initAnimations({
  emojiContainerId: 'emoji-container',
  audioId: 'music',
  dogImageId: 'dog-image',

  emojiUrl: assets.dataset.emoji1,
  emojiUrl2: assets.dataset.emoji2,
  emojiUrl3: assets.dataset.emoji3,
  emojiUrl4: assets.dataset.emoji4,
  emojiUrl5: assets.dataset.emoji5,

  dog1Url: assets.dataset.dog1,
  dog2Url: assets.dataset.dog2,

  timerDisplayId: null
});


// Logica para criar e renderizar o visualizador de audios
function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function drawCircularText(text, radius) {
  const centerX = textCanvas.width / 2;
  const centerY = textCanvas.height / 2;
  tCtx.clearRect(0, 0, textCanvas.width, textCanvas.height);
  tCtx.font = "bold 24px 'Arial Black'";
  tCtx.textAlign = "center";
  tCtx.fillStyle = "#fff";

  const characters = text.split("");
  const angleStep = (Math.PI * 2) / characters.length;

  characters.forEach((char, i) => {
    const angle = i * angleStep - Math.PI / 2;
    tCtx.save();
    tCtx.translate(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
    tCtx.rotate(angle + Math.PI / 2);
    tCtx.fillText(char, 0, 0);
    tCtx.restore();
  });
}

yes.addEventListener("click", () => {
  document.title = "AAAAAAUUUU!!!!!";
  
  container.style.top = "50%";
  container.style.left = "50%";
  container.style.transform = "translate(-50%, -50%)";
  buttons.style.display = "none";
  message1.style.display = "none";
  message2.style.display = "none";

  vizContainer.style.display = "flex";
  drawCircularText(CONFIG.text, 75);
  
  if (!audioCtx) {
    setupAudio();
  }
  
  music.currentTime = 0;
  music.play();
});

function setupAudio() {
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  analyser = audioCtx.createAnalyser();
  source = audioCtx.createMediaElementSource(music);
  source.connect(analyser);
  analyser.connect(audioCtx.destination);

  analyser.fftSize = 512;
  dataArray = new Uint8Array(analyser.frequencyBinCount);
  draw();
}

function draw() {
  requestAnimationFrame(draw);
  analyser.getByteFrequencyData(dataArray);

  let bassSum = 0;
  const bassCount = 10; 
  for(let i = 0; i < bassCount; i++) {
      bassSum += dataArray[i];
  }
  const bassAverage = bassSum / bassCount;
  const pulseScale = 1 + (bassAverage / 255) * (0.4 * CONFIG.pulseIntensity);
  vizContainer.style.transform = `scale(${pulseScale})`;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;

  const gradient = ctx.createRadialGradient(centerX, centerY, CONFIG.innerRadius, centerX, centerY, CONFIG.innerRadius + CONFIG.maxBarHeight);
  gradient.addColorStop(0, '#8A2BE2');   
  gradient.addColorStop(0.5, '#0000FF'); 
  gradient.addColorStop(1, '#FF0000');   

  for (let i = 0; i < CONFIG.numBars; i++) {
    let dataIndex = i < CONFIG.numBars / 2 ? i : CONFIG.numBars - i - 1;
    const value = dataArray[dataIndex];
    const barHeight = (value / 255) * CONFIG.maxBarHeight;
    const angle = (i * (Math.PI * 2)) / CONFIG.numBars + CONFIG.rotationOffset;

    const xStart = centerX + Math.cos(angle) * CONFIG.innerRadius;
    const yStart = centerY + Math.sin(angle) * CONFIG.innerRadius;
    const xEnd = centerX + Math.cos(angle) * (CONFIG.innerRadius + barHeight);
    const yEnd = centerY + Math.sin(angle) * (CONFIG.innerRadius + barHeight);

    ctx.strokeStyle = gradient;
    ctx.lineWidth = CONFIG.barWidth;
    ctx.lineCap = 'round';
    
    ctx.beginPath();
    ctx.moveTo(xStart, yStart);
    ctx.lineTo(xEnd, yEnd);
    ctx.stroke();
  }
}

function moverContainer(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  const padding = 50;
  const maxX = window.innerWidth - container.offsetWidth - padding;
  const maxY = window.innerHeight - container.offsetHeight - padding;
  const x = Math.max(padding, Math.random() * maxX);
  const y = Math.max(padding, Math.random() * maxY);
  
  container.style.left = `${x}px`;
  container.style.top = `${y}px`;
  container.style.transform = "none";

}

no.addEventListener("mouseenter", moverContainer);
no.addEventListener("touchstart", moverContainer, { passive: false });