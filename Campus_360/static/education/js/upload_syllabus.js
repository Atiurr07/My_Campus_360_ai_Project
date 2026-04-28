document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    form.addEventListener("submit", () => {
        const btn = document.querySelector(".btn-upload");
        btn.innerText = "Uploading...";
        btn.disabled = true;
    });
});
