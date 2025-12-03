// ----------------------------
// Funções do Carrinho
// ----------------------------

// Carrega carrinho do localStorage ou cria novo
function getCarrinho() {
    return JSON.parse(localStorage.getItem("carrinho")) || [];
}

// Salva carrinho
function salvarCarrinho(carrinho) {
    localStorage.setItem("carrinho", JSON.stringify(carrinho));
}

// Atualiza número no ícone do carrinho
function atualizarCarrinhoCount() {
    const carrinho = getCarrinho();
    const totalItens = carrinho.reduce((soma, item) => soma + item.qtd, 0);
    document.getElementById("carrinho-count").textContent = totalItens;
}

// ----------------------------
// Lógica dos botões + e -
// ----------------------------

const produtos = document.querySelectorAll(".produto");

produtos.forEach(card => {

    const btnMais = card.querySelector(".btn-mais");
    const btnMenos = card.querySelector(".btn-menos");
    const btnAdd = card.querySelector(".btn-add");
    const qtdSpan = card.querySelector(".qtd");
    const estoque = parseInt(card.querySelector(".estoque").dataset.estoque);

    const nome = card.querySelector("h3").textContent;
    const preco = parseFloat(card.dataset.preco.replace(",", ".")); 
    const imagem = card.querySelector("img").src;

    let qtd = 1;
    qtdSpan.textContent = qtd;

    // +
    btnMais.addEventListener("click", () => {
        if (qtd < estoque) {
            qtd++;
            qtdSpan.textContent = qtd;
        }
    });

    // -
    btnMenos.addEventListener("click", () => {
        if (qtd > 1) {
            qtd--;
            qtdSpan.textContent = qtd;
        }
    });

    // ----------------------------
    // Adicionar ao Carrinho
    // ----------------------------
    btnAdd.addEventListener("click", () => {
        let carrinho = getCarrinho();

        // Verifica se item já existe no carrinho
        const itemExistente = carrinho.find(i => i.nome === nome);

        if (itemExistente) {
            // Soma quantidade
            if (itemExistente.qtd + qtd <= estoque) {
                itemExistente.qtd += qtd;
            } else {
                itemExistente.qtd = estoque;
            }
        } else {
            carrinho.push({
                nome: nome,
                preco: preco,       // <<<<< VALOR DECIMAL MANTIDO
                qtd: qtd,
                imagem: imagem,
                estoque: estoque
            });
        }

        salvarCarrinho(carrinho);
        atualizarCarrinhoCount();

        // Feedback visual
        btnAdd.textContent = "Adicionado ✔";
        btnAdd.style.background = "#28a745";

        setTimeout(() => {
            btnAdd.textContent = "Adicionar ao Carrinho";
            btnAdd.style.background = "";
        }, 1200);
    });
});

// Atualiza o contador na primeira carga
atualizarCarrinhoCount();
