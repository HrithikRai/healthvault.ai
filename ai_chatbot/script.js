let promptInput = document.getElementById("prompt");
let submitButton = document.getElementById("submit");
let chatContainer = document.querySelector(".chat-container");

// WebSocket connection
const socket = new WebSocket("ws://localhost:8765"); // Replace with your actual WebSocket API

// Scroll chat to the latest message
function scrollToBottom() {
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100); // Delay to allow DOM updates
}


// Create a chat message element
function createChatBox(html, classes) {
    let div = document.createElement("div");
    div.innerHTML = html;
    div.classList.add(...classes.split(" "));
    return div;
}

// Handle user's message
function handleUserMessage(message) {
    let html = `
        <div class="user-chat-box">
            <div class="user-chat-area">${message}</div>
        </div>`;

    let userChatBox = createChatBox(html, "chat-box user-message");
    chatContainer.appendChild(userChatBox);
    scrollToBottom();

    // Send message to WebSocket API
    sendMessageToChatbot(message);
}

// Send message to WebSocket API
function sendMessageToChatbot(message) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ "input": message })); // Send as JSON
    } else {
        console.log("WebSocket connection is not open");
    }
}

// Handle AI response
function handleAIResponse(message) {
    let html = `
        <div class="ai-chat-box">
            <img src="ai.gif" alt="AI" class="aiImage" width="100">
            <div class="ai-chat-area">${message}</div>
        </div>`;

    let aiChatBox = createChatBox(html, "chat-box ai-message");
    chatContainer.appendChild(aiChatBox);
    scrollToBottom();
}

// WebSocket event listeners
socket.onmessage = (event) => {
    try {
        let response = JSON.parse(event.data).answer; // Extract 'answer' from response
        console.log("Chatbot Response:", response);
        handleAIResponse(response);
    } catch (error) {
        console.error("Error parsing WebSocket response:", error);
    }
};

socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
};

socket.onclose = () => {
    console.warn("WebSocket connection closed.");
};

// Handle input via "Enter" key
promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && promptInput.value.trim() !== "") {
        handleUserMessage(promptInput.value.trim());
        promptInput.value = ""; // Clear input after sending
    }
});

// Handle input via button click
submitButton.addEventListener("click", () => {
    if (promptInput.value.trim() !== "") {
        handleUserMessage(promptInput.value.trim());
        promptInput.value = ""; // Clear input after sending
    }
});
