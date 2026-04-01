function toast(msg, tipo = "ok") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `show toast-${tipo}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = ""; }, 3500);
}

async function aprovar(id, btn) {
  btn.disabled = true;
  btn.closest(".flag-actions").querySelectorAll(".btn").forEach(b => b.disabled = true);

  try {
    const r = await fetch(`/adm/aprovar/${id}/`, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      credentials: "same-origin",
    });
    const d = await r.json();
    if (d.success) {
      document.getElementById(`flag-${id}`).classList.add("resolvido");
      toast(`✓ Dia ${d.data} marcado como legítimo.`, "ok");
      atualizarContador(-1);
    } else {
      toast(d.error || "Erro ao aprovar.", "erro");
      btn.disabled = false;
    }
  } catch (_) {
    toast("Sem conexão.", "erro");
    btn.disabled = false;
  }
}


let _pendingLimpar = null;

function confirmarLimpar(id, dataStr, qtd) {
  _pendingLimpar = id;
  document.getElementById("modal-texto").textContent =
    `Isso vai remover permanentemente ${qtd} votos do dia ${dataStr}. Esta ação não pode ser desfeita.`;
  document.getElementById("overlay").classList.add("show");
  document.getElementById("modal-confirmar").onclick = () => executarLimpar(id);
}

function fecharModal() {
  document.getElementById("overlay").classList.remove("show");
  _pendingLimpar = null;
}

async function executarLimpar(id) {
  fecharModal();
  const card = document.getElementById(`flag-${id}`);
  card.querySelectorAll(".btn").forEach(b => b.disabled = true);

  try {
    const r = await fetch(`/adm/limpar/${id}/`, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      credentials: "same-origin",
    });
    const d = await r.json();
    if (d.success) {
      card.classList.add("resolvido");
      toast(`✗ ${d.removidos} votos removidos (${d.data}).`, "erro");
      atualizarContador(-1);
    } else {
      toast(d.error || "Erro ao limpar.", "erro");
      card.querySelectorAll(".btn").forEach(b => b.disabled = false);
    }
  } catch (_) {
    toast("Sem conexão.", "erro");
    card.querySelectorAll(".btn").forEach(b => b.disabled = false);
  }
}

function atualizarContador(delta) {
  const el = document.querySelector(".stat-value.danger, .stat-value.ok");
  if (!el) return;
  const novo = Math.max(0, (parseInt(el.textContent) || 0) + delta);
  el.textContent = novo;
  el.className = `stat-value ${novo > 0 ? "danger" : "ok"}`;
}


let _searchTimer = null;

async function buscarCampeoes(q) {
  const resultsEl = document.getElementById("featuredResults");
  try {
    const r = await fetch(
      `/adm/buscar-campeoes/?q=${encodeURIComponent(q)}`,
      { credentials: "same-origin" }
    );
    const d = await r.json();

    resultsEl.innerHTML = d.results.length
      ? d.results.map(c => `
          <div class="result-item" onclick="selecionarDestaque('${c.slug}', '${c.name.replace(/'/g, "\\'")}')">
            <span class="result-item-name">${c.name}</span>
            <span class="result-item-meta">/${c.slug} · ${c.votes} votos</span>
          </div>`).join("")
      : '<div class="result-item"><span class="result-item-meta">Nenhum resultado.</span></div>';

    resultsEl.classList.add("show");
  } catch (_) {
    toast("Erro ao buscar campeões.", "erro");
  }
}

async function selecionarDestaque(slug, name) {
  document.getElementById("featuredResults").classList.remove("show");
  document.getElementById("featuredSearch").value = "";

  const formData = new FormData();
  formData.append("slug", slug);

  try {
    const r = await fetch("/adm/set-featured/", {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      credentials: "same-origin",
      body: formData,
    });
    const d = await r.json();
    if (d.success) {
      document.querySelector(".featured-current").innerHTML = `
        <span class="featured-name">${d.name}</span>
        <span class="featured-slug">/${d.slug}</span>`;
      toast(`✓ Redirect de / → /${d.slug}`, "ok");
    } else {
      toast(d.error || "Erro ao definir destaque.", "erro");
    }
  } catch (_) {
    toast("Sem conexão.", "erro");
  }
}

async function limparDestaque() {
  const formData = new FormData();
  formData.append("slug", "");

  try {
    const r = await fetch("/adm/set-featured/", {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      credentials: "same-origin",
      body: formData,
    });
    const d = await r.json();
    if (d.success) {
      document.querySelector(".featured-current").innerHTML =
        '<span class="featured-none">Nenhum campeão definido — usando fallback</span>';
      toast("Destaque removido.", "ok");
    }
  } catch (_) {
    toast("Sem conexão.", "erro");
  }
}


document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("overlay").addEventListener("click", e => {
    if (e.target === e.currentTarget) fecharModal();
  });

  // Busca de campeões
  document.getElementById("featuredSearch").addEventListener("input", function () {
    clearTimeout(_searchTimer);
    const q = this.value.trim();
    if (!q) {
      document.getElementById("featuredResults").classList.remove("show");
      return;
    }
    _searchTimer = setTimeout(() => buscarCampeoes(q), 220);
  });

  document.addEventListener("click", e => {
    if (!e.target.closest(".featured-block")) {
      document.getElementById("featuredResults").classList.remove("show");
    }
  });
});