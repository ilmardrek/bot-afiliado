document.addEventListener("DOMContentLoaded", function () {
    const botao = document.getElementById("iniciarBot");

    if (botao) {
        botao.addEventListener("click", function () {
            alert("Bot iniciado com sucesso!");
        });
    }
});    
