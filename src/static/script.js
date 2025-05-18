let currentImage = "";
let socket = null;
let lastFetchTime = 0;
const FETCH_INTERVAL = 60000; // 1 minute

function formatDate(rawDate) {
    const date = new Date(rawDate);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
}

function showImageInfo(data) {
    if (!data.url) {
        document.body.style.backgroundImage = 'none';
        return;
    }
    
    if (data.url !== currentImage) {
        currentImage = data.url;
        document.body.style.backgroundImage = `url(${currentImage})`;
    }
    
    document.getElementById('date').textContent = formatDate(data.date);
    document.getElementById('prompt').textContent = data.prompt;
    document.getElementById('date').style.opacity = 1;
    document.getElementById('prompt').style.opacity = 1;
    setTimeout(() => {
        document.getElementById('date').style.opacity = 0;
        document.getElementById('prompt').style.opacity = 0;
    }, 20000);
}

function fetchImage() {
    const now = Date.now();
    if (now - lastFetchTime < FETCH_INTERVAL) {
        return;
    }
    lastFetchTime = now;
    
    fetch('/image')
        .then(response => response.json())
        .then(showImageInfo)
        .catch(console.error);
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        showImageInfo(data);
    };
    
    socket.onclose = () => {
        console.log('WebSocket closed, reconnecting in 5s...');
        setTimeout(connectWebSocket, 5000);
    };
}

// Start periodic polling and WebSocket connection
fetchImage();
setInterval(fetchImage, FETCH_INTERVAL);
connectWebSocket();