document.addEventListener("DOMContentLoaded", function () {
    const mensagem = document.querySelector("p");
    const botao = document.getElementById("iniciarBot");

    if (mensagem) {
        mensagem.textContent = "Bot Afiliado carregado e pronto!";
    }

    if (botao) {
        botao.addEventListener("click", function () {
            mensagem.textContent = "Bot iniciado com sucesso!";
        });
    }
});
