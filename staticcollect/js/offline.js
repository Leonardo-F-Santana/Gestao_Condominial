/**
 * ============================================================
 * PORTARIA OFFLINE ENGINE
 * ============================================================
 * Gerencia armazenamento offline (IndexedDB), detecção de
 * conexão e sincronização automática de visitantes, encomendas
 * e solicitações.
 * 
 * Quando offline, os formulários salvam localmente.
 * Quando online, sincroniza automaticamente com o servidor.
 * ============================================================
 */

const OfflineEngine = (function () {
    const DB_NAME = 'portaria_offline';
    const DB_VERSION = 2;
    let db = null;

    // =====================
    // 1. IndexedDB Setup
    // =====================
    function init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onupgradeneeded = function (e) {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('moradores')) {
                    db.createObjectStore('moradores', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('visitantes_pendentes')) {
                    db.createObjectStore('visitantes_pendentes', { keyPath: 'tempId', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('encomendas_pendentes')) {
                    db.createObjectStore('encomendas_pendentes', { keyPath: 'tempId', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('solicitacoes_pendentes')) {
                    db.createObjectStore('solicitacoes_pendentes', { keyPath: 'tempId', autoIncrement: true });
                }
            };

            request.onsuccess = function (e) {
                db = e.target.result;
                console.log('✅ IndexedDB pronto');
                resolve(db);
            };

            request.onerror = function (e) {
                console.error('❌ Erro ao abrir IndexedDB:', e);
                reject(e);
            };
        });
    }

    // =====================
    // 2. Cache de Moradores
    // =====================
    function cacheMoradores() {
        return fetch('/api/moradores-offline/')
            .then(r => r.json())
            .then(data => {
                const tx = db.transaction('moradores', 'readwrite');
                const store = tx.objectStore('moradores');
                store.clear();
                data.moradores.forEach(m => store.put(m));
                console.log(`✅ ${data.moradores.length} moradores em cache`);
                // Salvar username do porteiro logado
                localStorage.setItem('porteiro_username', data.porteiro);
                return data.moradores;
            })
            .catch(err => {
                console.warn('⚠️ Não foi possível atualizar cache de moradores:', err);
            });
    }

    function getMoradores() {
        return new Promise((resolve, reject) => {
            const tx = db.transaction('moradores', 'readonly');
            const store = tx.objectStore('moradores');
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // =====================
    // 3. Salvar Pendentes
    // =====================
    function salvarVisitante(dados) {
        return new Promise((resolve, reject) => {
            dados.timestamp = new Date().toISOString();
            dados.porteiro = localStorage.getItem('porteiro_username') || 'desconhecido';
            const tx = db.transaction('visitantes_pendentes', 'readwrite');
            const store = tx.objectStore('visitantes_pendentes');
            const request = store.add(dados);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function salvarEncomenda(dados) {
        return new Promise((resolve, reject) => {
            dados.timestamp = new Date().toISOString();
            dados.porteiro = localStorage.getItem('porteiro_username') || 'desconhecido';
            const tx = db.transaction('encomendas_pendentes', 'readwrite');
            const store = tx.objectStore('encomendas_pendentes');
            const request = store.add(dados);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function salvarSolicitacao(dados) {
        return new Promise((resolve, reject) => {
            dados.timestamp = new Date().toISOString();
            dados.porteiro = localStorage.getItem('porteiro_username') || 'desconhecido';
            const tx = db.transaction('solicitacoes_pendentes', 'readwrite');
            const store = tx.objectStore('solicitacoes_pendentes');
            const request = store.add(dados);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // =====================
    // 4. Contar Pendentes
    // =====================
    function contarPendentes() {
        return new Promise((resolve) => {
            let total = 0;
            const tx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readonly');

            const req1 = tx.objectStore('visitantes_pendentes').count();
            req1.onsuccess = () => { total += req1.result; };

            const req2 = tx.objectStore('encomendas_pendentes').count();
            req2.onsuccess = () => { total += req2.result; };

            const req3 = tx.objectStore('solicitacoes_pendentes').count();
            req3.onsuccess = () => { total += req3.result; };

            tx.oncomplete = () => resolve(total);
            tx.onerror = () => resolve(0);
        });
    }

    // =====================
    // 5. Sincronização
    // =====================
    function sincronizar() {
        if (!navigator.onLine) {
            console.log('⏸️ Ainda offline, sync adiado');
            return Promise.resolve(false);
        }

        return new Promise((resolve) => {
            const tx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readonly');
            const visitantes = [];
            const encomendas = [];
            const solicitacoes = [];

            tx.objectStore('visitantes_pendentes').getAll().onsuccess = function (e) {
                e.target.result.forEach(v => visitantes.push(v));
            };

            tx.objectStore('encomendas_pendentes').getAll().onsuccess = function (e) {
                e.target.result.forEach(enc => encomendas.push(enc));
            };

            tx.objectStore('solicitacoes_pendentes').getAll().onsuccess = function (e) {
                e.target.result.forEach(sol => solicitacoes.push(sol));
            };

            tx.oncomplete = function () {
                if (visitantes.length === 0 && encomendas.length === 0 && solicitacoes.length === 0) {
                    console.log('✅ Nada para sincronizar');
                    atualizarBadgePendentes();
                    resolve(true);
                    return;
                }

                console.log(`🔄 Sincronizando: ${visitantes.length} visitantes, ${encomendas.length} encomendas, ${solicitacoes.length} solicitações...`);

                fetch('/api/sync-offline/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        visitantes: visitantes.map(v => ({
                            nome_completo: v.nome_completo,
                            cpf: v.cpf || '',
                            data_nascimento: v.data_nascimento || null,
                            placa_veiculo: v.placa_veiculo || '',
                            morador_id: v.morador_id || null,
                            quem_autorizou: v.quem_autorizou || '',
                            observacoes: v.observacoes || ''
                        })),
                        encomendas: encomendas.map(e => ({
                            morador_id: e.morador_id,
                            volume: e.volume,
                            destinatario_alternativo: e.destinatario_alternativo || ''
                        })),
                        solicitacoes: solicitacoes.map(s => ({
                            tipo: s.tipo,
                            descricao: s.descricao,
                            morador_id: s.morador_id || null
                        }))
                    })
                })
                    .then(r => r.json())
                    .then(result => {
                        console.log('✅ Sync resultado:', result);

                        // Limpar stores após sync bem-sucedido
                        const clearTx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readwrite');
                        clearTx.objectStore('visitantes_pendentes').clear();
                        clearTx.objectStore('encomendas_pendentes').clear();
                        clearTx.objectStore('solicitacoes_pendentes').clear();

                        clearTx.oncomplete = () => {
                            atualizarBadgePendentes();
                            const partes = [];
                            if (result.visitantes_criados) partes.push(`${result.visitantes_criados} visitante(s)`);
                            if (result.encomendas_criadas) partes.push(`${result.encomendas_criadas} encomenda(s)`);
                            if (result.solicitacoes_criadas) partes.push(`${result.solicitacoes_criadas} solicitação(ões)`);
                            mostrarNotificacao(`✅ Sincronizado! ${partes.join(', ')} registrados por ${result.porteiro}.`, 'success');
                            resolve(true);
                        };
                    })
                    .catch(err => {
                        console.error('❌ Erro no sync:', err);
                        mostrarNotificacao('❌ Erro ao sincronizar. Tentaremos novamente em breve.', 'danger');
                        resolve(false);
                    });
            };
        });
    }

    // =====================
    // 6. UI Helpers
    // =====================
    function atualizarBadgePendentes() {
        contarPendentes().then(count => {
            const badge = document.getElementById('offline-pendentes-badge');
            const syncBtn = document.getElementById('btn-sync-manual');
            if (badge) {
                if (count > 0) {
                    badge.textContent = `${count} pendente${count > 1 ? 's' : ''}`;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
            if (syncBtn) {
                syncBtn.style.display = count > 0 ? 'inline-block' : 'none';
            }
        });
    }

    function atualizarStatusConexao() {
        const indicator = document.getElementById('offline-status');
        if (!indicator) return;

        if (navigator.onLine) {
            indicator.innerHTML = '<i class="bi bi-wifi"></i> Online';
            indicator.className = 'badge bg-success ms-2';
        } else {
            indicator.innerHTML = '<i class="bi bi-wifi-off"></i> Offline';
            indicator.className = 'badge bg-danger ms-2 pulse-offline';
        }
    }

    function mostrarNotificacao(mensagem, tipo) {
        const container = document.querySelector('.main-container') || document.querySelector('.container');
        if (!container) return;

        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
        alerta.setAttribute('role', 'alert');
        alerta.innerHTML = `
            <strong>${tipo === 'success' ? '✅' : tipo === 'warning' ? '⚠️' : '❌'}</strong> ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.insertBefore(alerta, container.firstChild);

        // Auto-remover após 6s
        setTimeout(() => {
            if (alerta.parentNode) alerta.remove();
        }, 6000);
    }

    // =====================
    // 7. Interceptar Forms
    // =====================
    function interceptarFormularios() {
        // --- Formulário de Visitantes ---
        const formVisitante = document.querySelector('form[action*="registrar_entrada"]'); // action url has registrar_entrada in views, or input hidden with registrar_entrada
        if (!formVisitante) {
            // Se formVisitante falhar, tenta pegar via input hidden 
            const inputVisitante = document.querySelector('input[name="registrar_entrada"]');
            if (inputVisitante && inputVisitante.closest('form')) {
                const formReal = inputVisitante.closest('form');
                formReal.addEventListener('submit', function (e) {
                    if (navigator.onLine) return; // Online: deixa o form normal funcionar
    
                    e.preventDefault();
                    const formData = new FormData(formReal);
                    salvarVisitante({
                        nome_completo: formData.get('nome'),
                        cpf: formData.get('cpf') || '',
                        data_nascimento: formData.get('data_nascimento') || '',
                        placa_veiculo: formData.get('placa') || '',
                        morador_id: formData.get('morador_id') || '',
                        quem_autorizou: formData.get('quem_autorizou') || '',
                        observacoes: formData.get('observacoes') || ''
                    }).then(() => {
                        formReal.reset();
                        mostrarNotificacao('Visitante salvo offline — será sincronizado automaticamente quando a internet voltar.', 'warning');
                        atualizarBadgePendentes();
                        
                        // Close modal if exists
                        const modal = document.getElementById('modalEntrada');
                        if (modal && typeof bootstrap !== 'undefined') {
                            const bsModal = bootstrap.Modal.getInstance(modal);
                            if (bsModal) bsModal.hide();
                        }
                    });
                });
            }
        } else {
            formVisitante.addEventListener('submit', function (e) {
                if (navigator.onLine) return; // Online: deixa o form normal funcionar

                e.preventDefault();
                const formData = new FormData(formVisitante);
                salvarVisitante({
                    nome_completo: formData.get('nome_completo') || formData.get('nome'),
                    cpf: formData.get('cpf') || '',
                    data_nascimento: formData.get('data_nascimento') || '',
                    placa_veiculo: formData.get('placa_veiculo') || formData.get('placa') || '',
                    morador_id: formData.get('morador_responsavel') || formData.get('morador_id') || '',
                    quem_autorizou: formData.get('quem_autorizou') || '',
                    observacoes: formData.get('observacoes') || ''
                }).then(() => {
                    formVisitante.reset();
                    mostrarNotificacao('Visitante salvo offline — será sincronizado automaticamente quando a internet voltar.', 'warning');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Formulário de Encomendas ---
        const formEncomenda = document.querySelector('form[action*="registrar_encomenda"]');
        if (formEncomenda) {
            formEncomenda.addEventListener('submit', function (e) {
                if (navigator.onLine) return;

                e.preventDefault();
                const formData = new FormData(formEncomenda);
                const moradorId = formData.get('morador_encomenda');
                if (!moradorId) {
                    mostrarNotificacao('Selecione um morador antes de registrar a encomenda.', 'danger');
                    return;
                }
                salvarEncomenda({
                    morador_id: moradorId,
                    volume: formData.get('volume') || '',
                    destinatario_alternativo: formData.get('destinatario_alternativo') || ''
                }).then(() => {
                    formEncomenda.reset();
                    mostrarNotificacao('Encomenda salva offline — será sincronizada automaticamente quando a internet voltar.', 'warning');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Formulário de Solicitações ---
        const formSolicitacao = document.querySelector('form[action*="registrar_solicitacao"]');
        if (formSolicitacao) {
            formSolicitacao.addEventListener('submit', function (e) {
                if (navigator.onLine) return;

                e.preventDefault();
                const formData = new FormData(formSolicitacao);
                const descricao = formData.get('descricao');
                if (!descricao) {
                    mostrarNotificacao('Preencha a descrição da solicitação.', 'danger');
                    return;
                }
                salvarSolicitacao({
                    tipo: formData.get('tipo') || 'OUTRO',
                    descricao: descricao,
                    morador_id: formData.get('morador_solicitacao') || ''
                }).then(() => {
                    formSolicitacao.reset();
                    mostrarNotificacao('Solicitação salva offline — será sincronizada automaticamente quando a internet voltar.', 'warning');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Botão de sync manual ---
        const syncBtn = document.getElementById('btn-sync-manual');
        if (syncBtn) {
            syncBtn.addEventListener('click', function () {
                syncBtn.disabled = true;
                syncBtn.innerHTML = '<i class="bi bi-arrow-repeat spin-icon"></i> Sincronizando...';
                sincronizar().then(() => {
                    syncBtn.disabled = false;
                    syncBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sincronizar';
                    // Recarregar a página para mostrar os novos registros
                    if (navigator.onLine) {
                        setTimeout(() => window.location.reload(), 1500);
                    }
                });
            });
        }
    }

    // =====================
    // 8. Monitor de Conexão
    // =====================
    function iniciarMonitor() {
        atualizarStatusConexao();
        atualizarBadgePendentes();

        window.addEventListener('online', () => {
            console.log('🟢 Conexão restabelecida!');
            atualizarStatusConexao();
            // Tentar sincronizar automaticamente após 2s (dar tempo para estabilizar)
            setTimeout(() => {
                sincronizar().then(ok => {
                    if (ok) {
                        // Recarregar para atualizar os dados na tela
                        setTimeout(() => window.location.reload(), 2000);
                    }
                });
            }, 2000);
        });

        window.addEventListener('offline', () => {
            console.log('🔴 Conexão perdida!');
            atualizarStatusConexao();
            mostrarNotificacao('⚠️ Você está sem internet. Os cadastros serão salvos localmente e sincronizados quando a conexão voltar.', 'warning');
        });
    }

    // =====================
    // PUBLIC API
    // =====================
    return {
        init: init,
        cacheMoradores: cacheMoradores,
        getMoradores: getMoradores,
        salvarVisitante: salvarVisitante,
        salvarEncomenda: salvarEncomenda,
        salvarSolicitacao: salvarSolicitacao,
        contarPendentes: contarPendentes,
        sincronizar: sincronizar,
        interceptarFormularios: interceptarFormularios,
        iniciarMonitor: iniciarMonitor,
        atualizarBadgePendentes: atualizarBadgePendentes
    };
})();

// =====================
// AUTO-INICIALIZAÇÃO
// =====================
document.addEventListener('DOMContentLoaded', function () {
    // Só inicializa na portaria (não no portal do morador/síndico)
    const isPortaria = document.querySelector('.brand-text');
    if (!isPortaria) return;

    OfflineEngine.init().then(() => {
        OfflineEngine.iniciarMonitor();
        OfflineEngine.interceptarFormularios();

        // Cachear moradores quando online
        if (navigator.onLine) {
            OfflineEngine.cacheMoradores();
        }

        // Verificar se há pendentes para sincronizar
        OfflineEngine.contarPendentes().then(count => {
            if (count > 0 && navigator.onLine) {
                OfflineEngine.sincronizar();
            }
        });
    });
});
