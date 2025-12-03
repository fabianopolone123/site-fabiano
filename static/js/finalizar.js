// Carrega total do carrinho
const carrinho = JSON.parse(localStorage.getItem("carrinho")) || [];

function calcularTotal() {
    let t = 0;
    carrinho.forEach(i => t += i.preco * i.qtd);
    return t.toFixed(2).replace('.', ',');
}

document.getElementById("total-pedido").innerText = "R$ " + calcularTotal();


// Mostrar / esconder formulário novo cliente
document.getElementById("btn-novo").onclick = () => {
    document.getElementById("novo-cliente").style.display = "block";
};


// selecionar pagamento
let formaPagamento = null;
document.querySelectorAll(".pg-card").forEach(card => {
    card.addEventListener("click", function(){
        document.querySelectorAll(".pg-card").forEach(c => c.classList.remove("selecionado"));
        this.classList.add("selecionado");
        formaPagamento = this.dataset.pg;
    });
});


// salvar cliente novo
document.getElementById("btn-salvar").onclick = async () => {

    const nome = document.getElementById("novo-nome").value;
    const whats = document.getElementById("novo-whats").value;

    if (!nome || !whats) {
        alert("Preencha nome e WhatsApp!");
        return;
    }

    const resposta = await fetch("/salvar_cliente/", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie('csrftoken')},
        body: JSON.stringify({nome, whats})
    });

    const data = await resposta.json();

    if (data.ok) {
        alert("Cliente cadastrado!");
        window.location.reload();
    }
};



// ==========================
// FINALIZAR PEDIDO (NOVA VERSÃO)
// ==========================

document.getElementById("btn-finalizar-pedido").onclick = async function() {

    const btn = document.getElementById("btn-finalizar-pedido");

    // impedir múltiplos cliques
    if (btn.disabled) return;

    btn.disabled = true;
    btn.innerText = "Processando...";

    const cliente = document.getElementById("cliente-select").value;

    if (!cliente) {
        alert("Selecione o cliente!");
        btn.disabled = false;
        btn.innerText = "Finalizar Pedido";
        return;
    }

    if (!formaPagamento) {
        alert("Escolha a forma de pagamento!");
        btn.disabled = false;
        btn.innerText = "Finalizar Pedido";
        return;
    }

    // TOKEN para idempotência do pedido
    const token = document.getElementById("pedido_token").value;

    try {

        const resposta = await fetch("/criar_pedido/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie('csrftoken')},
            body: JSON.stringify({
                cliente,
                pagamento: formaPagamento,
                itens: carrinho,
                token: token
            })
        });

        const data = await resposta.json();

        if (data.ok) {

            localStorage.removeItem("carrinho");

            if (data.redirect_url) {
                window.location = data.redirect_url; // pagamento PIX
            } else {
                alert("Pedido criado com sucesso!");
                window.location = "/";
            }

        } else {
            alert(data.erro || "Erro ao criar pedido.");
            btn.disabled = false;
            btn.innerText = "Finalizar Pedido";
        }

    } catch (err) {
        alert("Erro de conexão. Tente novamente.");
        btn.disabled = false;
        btn.innerText = "Finalizar Pedido";
    }

};


// Pega CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
