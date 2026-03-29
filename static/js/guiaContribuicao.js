(() => {
    const LS_KEY = `votos_${SERVER_STATE.champion}`;
    const MAX_VOTOS = 3;

    function salvarCache(totalVotos, meusVotos) {
        try {
            localStorage.setItem(LS_KEY, JSON.stringify({ totalVotos, meusVotos }));
        } catch (_) {
            // localStorage indisponível (modo anônimo bloqueado, etc.) — ignora silenciosamente
        }
    }

    function lerCache() {
        try {
            const raw = localStorage.getItem(LS_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) {
            return null;
        }
    }


    // Renderização
    function renderizarVotos(totalVotos, meusVotos) {
        document.getElementById("totalVotos").textContent = totalVotos;
    }

    function atualizarBotao(meusVotos) {
        const btn = document.getElementById("btnVotar");
        const jaVotou = meusVotos.some(v => v.champion === SERVER_STATE.champion);

        if (jaVotou) {
            btn.disabled = true;
            btn.textContent = `✓ Você já votou em ${capitalize(SERVER_STATE.champion)}`;
        } else {
            btn.disabled = false;
            btn.textContent = `Votar para criar a página de ${capitalize(SERVER_STATE.champion)}`;
        }
    }

    function mostrarFeedback(mensagem, tipo = "info") {
        const el = document.getElementById("feedbackVoto");
        el.textContent = mensagem;
        el.style.display = "block";
        el.style.color = tipo === "erro" ? "#c0392b" : tipo === "sucesso" ? "#27ae60" : "#666";
        setTimeout(() => { el.style.display = "none"; }, 3500);
    }

    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    function getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    }

    // Sincroniza com o servidor ao carregar a página
    async function sincronizarComServidor() {
        const btn = document.getElementById("btnVotar");
        const stateUrl = btn.dataset.stateUrl;

        try {
            const resp = await fetch(stateUrl, { credentials: "same-origin" });
            if (!resp.ok) return;
            const data = await resp.json();

            salvarCache(data.total_votos, data.meus_votos);
            renderizarVotos(data.total_votos, data.meus_votos);
            atualizarBotao(data.meus_votos);
        } catch (_) {
            const cache = lerCache();
            if (cache) {
                renderizarVotos(cache.totalVotos, cache.meusVotos);
                atualizarBotao(cache.meusVotos);
            }
        }
    }

    // Ação de votar
    async function votar() {
        const btn = document.getElementById("btnVotar");
        if (btn.disabled) return;

        btn.disabled = true;
        const original = btn.textContent;
        btn.textContent = "Enviando…";

        try {
            const resp = await fetch(btn.dataset.url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "Content-Type": "application/json",
                },
            });

            const data = await resp.json();

            if (resp.ok && data.success) {
                salvarCache(data.total_votos, data.meus_votos);
                renderizarVotos(data.total_votos, data.meus_votos);
                atualizarBotao(data.meus_votos);
                mostrarFeedback("✓ Voto registrado!", "sucesso");
            } else {
                // Voto duplicado ou outro erro esperado
                btn.disabled = false;
                btn.textContent = original;
                mostrarFeedback(data.error || "Erro ao votar.", "erro");
            }
        } catch (_) {
            btn.disabled = false;
            btn.textContent = original;
            mostrarFeedback("Sem conexão. Tente novamente.", "erro");
        }
    }

    function init() {
        renderizarVotos(SERVER_STATE.totalVotos, SERVER_STATE.meusVotos);
        atualizarBotao(SERVER_STATE.meusVotos);
        salvarCache(SERVER_STATE.totalVotos, SERVER_STATE.meusVotos);
        
        sincronizarComServidor();

        // 3. Botão de votação
        document.getElementById("btnVotar").addEventListener("click", votar);
    }

    document.addEventListener("DOMContentLoaded", init);
})();