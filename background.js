let isListening = false;
let recognition;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'toggleListening') {
    isListening = !isListening;
    if (isListening) {
      startListening();
    } else {
      stopListening();
    }
    updatePopup();
  }
});

function startListening() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        function: initializeSpeechRecognition,
      });
    }
  });
}

function stopListening() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        function: stopSpeechRecognition,
      });
    }
  });
}

function updatePopup() {
  chrome.runtime.sendMessage({ action: 'updateListeningStatus', isListening });
}

function initializeSpeechRecognition() {
  if (!('webkitSpeechRecognition' in window)) {
    console.error('Speech recognition not supported');
    return;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const last = event.results.length - 1;
    const command = event.results[last][0].transcript.trim().toLowerCase();
    console.log('Recognized command:', command);
    processCommand(command);
  };

  recognition.start();
  console.log('Speech recognition started');
}

function stopSpeechRecognition() {
  if (window.recognition) {
    window.recognition.stop();
    console.log('Speech recognition stopped');
  }
}

function processCommand(command) {
  if (command.includes('scroll down')) {
    window.scrollBy(0, window.innerHeight / 2);
  } else if (command.includes('scroll up')) {
    window.scrollBy(0, -window.innerHeight / 2);
  } else if (command.includes('click')) {
    simulateClick();
  } else if (command.includes('move cursor')) {
    moveCursor();
  }
}

function simulateClick() {
  const element = document.elementFromPoint(
    window.innerWidth / 2,
    window.innerHeight / 2
  );
  if (element) {
    element.click();
  }
}

function moveCursor() {
  const x = Math.floor(Math.random() * window.innerWidth);
  const y = Math.floor(Math.random() * window.innerHeight);
  const event = new MouseEvent('mousemove', {
    view: window,
    bubbles: true,
    cancelable: true,
    clientX: x,
    clientY: y,
  });
  document.dispatchEvent(event);
}