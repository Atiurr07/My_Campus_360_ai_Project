document.addEventListener("DOMContentLoaded", () => {
    const btn = document.querySelector(".btn-generate");
    const form = document.querySelector("form");

    form.addEventListener("submit", () => {
        btn.innerText = "Generating...";
        btn.disabled = true;
    });
});
