let btn = document.getElementById("btn");
let content = document.getElementById("content")
let voice = document.getElementById("voice")
let socket = new WebSocket("ws://localhost:8765");  


function speak(text) {
    let utterance = new SpeechSynthesisUtterance(text);
    let synth = window.speechSynthesis;
    utterance.onstart = () => console.log("Speech started...");
    utterance.onend = () => console.log("Speech ended.");
    utterance.onerror = (event) => console.error("Speech error:", event);
    utterance.lang="hi-IN"
    
    utterance.rate = 1.0;  // Adjust speed
    utterance.pitch = 1.0; // Adjust pitch
    utterance.volume = 1.0; // Ensure full volume
    window.speechSynthesis.speak(utterance);
    synth.cancel();
    setTimeout(() => {
        synth.speak(utterance);
    }, 100);

}

let speechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = new speechRecognition();

recognition.onresult = (event) => {
    let transcript = event.results[event.results.length - 1][0].transcript;
    content.innerText = transcript;
    console.log(event);
    takeCommand(transcript)
};

btn.addEventListener("click",()=>{
    recognition.start()
    btn.style.display = "none"
    voice.style.display = "block"
})

// Send the user's command to the chatbot via WebSocket
function sendMessageToChatbot(message) {
    if (socket.readyState === WebSocket.OPEN) {
        // Stringify the message object before sending it
        socket.send(JSON.stringify({ "input": message }));
    } else {
        console.log("WebSocket connection is not open");
    }
}

socket.onmessage = (event) => {
    // Parse the JSON response from the chatbot
    let response = JSON.parse(event.data).answer;  // Extract the 'answer' field from the response object
    console.log("Chatbot Response:", response);
    // Speak the chatbot response in the detected language
    speak(response);
};

function takeCommand(message) {
    btn.style.display = "flex";
    voice.style.display = "none";

    // Send the message to the chatbot via WebSocket
    sendMessageToChatbot(message);
}