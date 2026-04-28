let currentChat = [];
let chats = [];
let isSending = false;

function addMessage(text, type) {
    let chatBox = document.getElementById("chat-box");

    if (!chatBox) {
        console.error("chat-box not found");
        return;
    }

    let wrapper = document.createElement("div");
    wrapper.className = type;

    let bubble = document.createElement("div");

    bubble.innerText = (type === "user-msg" ? "🧑 " : "🤖 ") + text;

    wrapper.appendChild(bubble);
    chatBox.appendChild(wrapper);

    // ✅ FIXED SCROLL
    chatBox.scrollTo({
        top: chatBox.scrollHeight,
        behavior: "smooth"
    });

    return bubble;
}

function showLoader() {
    document.getElementById("chat-loader").classList.remove("d-none");
}

function hideLoader() {
    document.getElementById("chat-loader").classList.add("d-none");
}

async function sendMessage() {
    let input = document.getElementById("user-input");
    let fileInput = document.getElementById("file-input");

    let message = input.value.trim();
    let file = fileInput.files[0];

    if (!message && !file) return;
    
    console.log("Sending:", message, file);
    input.disabled = true;

    if (isSending) return;
    isSending = true;

    if (message) addMessage(message, "user-msg")
    input.value = "";

    showLoader();

    let botBubble = addMessage("", "bot-msg");

    try {
        let formData = new FormData();
        formData.append("query", message);

        if (file) {
            formData.append("file", file);
        }

        const response = await fetch("/education/api/ai-assistant/query/", {
            method: "POST",
            body: formData
        });

        console.log("STATUS:", response.status);

        if (!response.ok) {
            throw new Error("HTTP error: " + response.status);
        }

        let data;
        try{
            data = await response.json();
        } catch {
            throw new Error("Invalid JSON response");
        }

        console.log("DATA:", data);

        hideLoader();

        // ✅ FIRST define reply
        let reply =
            data.response ||
            data.answer?.explanation ||
            data.message ||
            "No response";

        reply = reply
            .replace(/([a-z])([A-Z])/g, "$1 $2")
            .replace(/\*\*/g, "")
            .replace(/\s+/g, " ")
            .trim();

        // ✅ CLEAR before typing
        botBubble.innerHTML = reply
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");

        // ✅ Typing effect
        let i = 0;
        function typeEffect() {
            if (i >= reply.length) {
                botBubble.innerHTML += reply.charAt(i);
                i++;
                setTimeout(typeEffect, 10);
            }
        }

        typeEffect();

        currentChat.push({ user: message, bot: reply });
        fileInput.value = "";


    } catch (err) {
        hideLoader();
        console.error(err);

        botBubble.innerText = "⚠️ Server error";
    }

    input.disabled = false;
    input.focus();
    isSending = false;
}

function newChat() {
    if (currentChat.length > 0) {
        chats.push(currentChat);
        saveChats();
    }
    currentChat = [];
    document.getElementById("chat-box").innerHTML = "";
    renderHistory();
}

function saveChats() {
    localStorage.setItem("ai_chats", JSON.stringify(chats));
}

function loadchats() {
    let saved = localStorage.getItem("ai_chats");
    if (saved){
        chats = JSON.parse(saved);
        if (chats.length > 0) {
            currentChat = chats[chats.length - 1];

            currentChat.forEach(msg => {
                addMessage(msg.user, "user-msg");
                addMessage(msg.bot, "bot-msg");
            });
        }
        renderHistory();
    }
}

window.onload = function () {
    let saved = localStorage.getItem("ai_chats");

    if (saved) {
        chats = JSON.parse(saved);

        if (chats.length > 0) {
            currentChat = chats[chats.length - 1];

            currentChat.forEach(msg => {
                addMessage(msg.user, "user-msg");
                addMessage(msg.bot, "bot-msg");
            });
        }
    } else {
        addMessage("👋 Hello! I'm your AI assistant. Ask anything!", "bot-msg");
    }
};

function renderHistory() {
    let container = document.getElementById("chat-history");
    container.innerHTML = "";

    chats.forEach((chat, index) => {
        let div = document.createElement("div");
        div.innerText = "Chat " + (index + 1);
        div.onclick = () => loadChat(index);
        container.appendChild(div);
    });
}

function loadChat(index) {
    let chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = "";

    chats[index].forEach(msg => {
        addMessage(msg.user, "user-msg");
        addMessage(msg.bot, "bot-msg");
    });
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                cookieValue = cookie.substring('csrftoken='.length);
                break;
            }
        }
    }
    return cookieValue;
}

/* ENTER KEY */
document.addEventListener("DOMContentLoaded", function() {
    const input = document.getElementById("user-input");
    if (input){
        input.addEventListener("keydown", function(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});