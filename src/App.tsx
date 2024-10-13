import React, { useState, useEffect } from 'react';
import { Mic, MicOff } from 'lucide-react';

function App() {
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'updateListeningStatus') {
        setIsListening(request.isListening);
      }
    });
  }, []);

  const toggleListening = () => {
    chrome.runtime.sendMessage({ action: 'toggleListening' });
  };

  return (
    <div className="w-64 p-4 bg-gray-100">
      <h1 className="text-2xl font-bold mb-4">Voice Command Extension</h1>
      <button
        onClick={toggleListening}
        className={`w-full py-2 px-4 rounded-full flex items-center justify-center ${
          isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'
        } text-white transition-colors duration-300`}
      >
        {isListening ? (
          <>
            <MicOff className="mr-2" size={20} />
            Stop Listening
          </>
        ) : (
          <>
            <Mic className="mr-2" size={20} />
            Start Listening
          </>
        )}
      </button>
      <p className="mt-4 text-sm text-gray-600">
        {isListening
          ? "Listening for commands..."
          : "Click the button to start listening for voice commands."}
      </p>
    </div>
  );
}

export default App;