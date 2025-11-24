console.log("CARRINHO ABERTO!");

const area = document.getElementById("carrinho-container");
const carrinho = JSON.parse(localStorage.getItem("carrinho")) || [];

if (carrinho.length === 0) {
    area.innerHTML = "<p style='text-align:center;'>Carrinho vazio.</p>";
} else {
    area.innerHTML = "<pre>" + JSON.stringify(carrinho, null, 4) + "</pre>";
}


function getCarrinho() {
    return JSON.parse(localStorage.getItem("carrinho")) || [];
}

function salvarCarrinho(carrinho) {
    localStorage.setItem("carrinho", JSON.stringify(carrinho));
}

function formatar(valor) {
    return "R$ " + valor.toFixed(2).replace(".", ",");
}

function carregarCarrinho() {

    const area = document.getElementById("carrinho-container");
    const carrinho = getCarrinho();

    if (carrinho.length === 0) {
        area.innerHTML = "<p style='text-align:center;'>Carrinho vazio.</p>";
        document.getElementById("total-geral").textContent = "R$ 0,00";
        return;
    }

    area.innerHTML = "";

    let totalGeral = 0;

    carrinho.forEach((item, index) => {

        const subtotal = item.preco * item.qtd;
        totalGeral += subtotal;

        let card = document.createElement("div");
        card.classList.add("carrinho-item");

        card.innerHTML = `
            <img src="${item.imagem}">
            
            <div class="item-info">
                <h3>${item.nome}</h3>

                <div class="item-qtd">
                    <button class="btn-menos">-</button>
                    <span class="qtd">${item.qtd}</span>
                    <button class="btn-mais">+</button>
                </div>

                <div class="item-subtotal">Subtotal: ${formatar(subtotal)}</div>

            </div>

            <div class="item-remover">❌</div>
        `;

        area.appendChild(card);

        // Botões
        const btnMais = card.querySelector(".btn-mais");
        const btnMenos = card.querySelector(".btn-menos");
        const btnRemover = card.querySelector(".item-remover");
        const qtdSpan = card.querySelector(".qtd");
        const subtotalDiv = card.querySelector(".item-subtotal");

        // Aumentar quantidade
        btnMais.addEventListener("click", () => {
            if (item.qtd < item.estoque) {
                item.qtd++;
                qtdSpan.textContent = item.qtd;
                subtotalDiv.textContent = "Subtotal: " + formatar(item.preco * item.qtd);

                // animação suave ao atualizar
                subtotalDiv.classList.remove("subtotal-animar");
                void subtotalDiv.offsetWidth; // reset da animação
                subtotalDiv.classList.add("subtotal-animar");

                salvarCarrinho(carrinho);
                carregarCarrinho();
            }
        });

        // Diminuir quantidade
        btnMenos.addEventListener("click", () => {
            if (item.qtd > 1) {
                item.qtd--;
                qtdSpan.textContent = item.qtd;
                subtotalDiv.textContent = "Subtotal: " + formatar(item.preco * item.qtd);

                // animação suave ao atualizar
                subtotalDiv.classList.remove("subtotal-animar");
                void subtotalDiv.offsetWidth; // reset da animação
                subtotalDiv.classList.add("subtotal-animar");

                salvarCarrinho(carrinho);
                carregarCarrinho();
            }
        });

        // Remover item
        btnRemover.addEventListener("click", () => {
            carrinho.splice(index, 1);
            salvarCarrinho(carrinho);
            carregarCarrinho();
        });

    });

    document.getElementById("total-geral").textContent = formatar(totalGeral);
}

carregarCarrinho();
