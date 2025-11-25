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

    // AJAX para backend salvar cliente
    const resposta = await fetch("/salvar_cliente/", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie('csrftoken')},
        body: JSON.stringify({nome, whats})
    });

    const data = await resposta.json();

    if (data.ok) {
        alert("Cliente cadastrado!");

        // recarregar página com novo cliente no select
        window.location.reload();
    }
};


// Finalizar pedido
document.getElementById("btn-finalizar-pedido").onclick = async () => {

    const cliente = document.getElementById("cliente-select").value;

    if (!cliente) return alert("Selecione o cliente!");

    if (!formaPagamento) return alert("Escolha a forma de pagamento!");

    const resposta = await fetch("/criar_pedido/", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie('csrftoken')},
        body: JSON.stringify({
            cliente,
            pagamento: formaPagamento,
            itens: carrinho
        })
    });

    const data = await resposta.json();

    if (data.ok) {
        alert("Pedido criado com sucesso!");
        localStorage.removeItem("carrinho");
        window.location = "/";
    }
};


// função pra pegar CSRF
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
