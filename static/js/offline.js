

const OfflineEngine = (function () {
    const DB_NAME = 'portaria_offline';
    const DB_VERSION = 2;
    let db = null;
    let isSincronizando = false;


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

        if (isSincronizando) {
            console.log('⏳ Sincronização já em andamento');
            return Promise.resolve(false);
        }

        isSincronizando = true;

        return new Promise((resolve) => {
            const tx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readwrite');
            const visitantes = [];
            const encomendas = [];
            const solicitacoes = [];

            const storeV = tx.objectStore('visitantes_pendentes');
            storeV.getAll().onsuccess = function (e) {
                e.target.result.forEach(v => {
                    if (!v.sincronizando) {
                        v.sincronizando = true;
                        storeV.put(v);
                        visitantes.push(v);
                    }
                });
            };

            const storeE = tx.objectStore('encomendas_pendentes');
            storeE.getAll().onsuccess = function (e) {
                e.target.result.forEach(enc => {
                    if (!enc.sincronizando) {
                        enc.sincronizando = true;
                        storeE.put(enc);
                        encomendas.push(enc);
                    }
                });
            };

            const storeS = tx.objectStore('solicitacoes_pendentes');
            storeS.getAll().onsuccess = function (e) {
                e.target.result.forEach(sol => {
                    if (!sol.sincronizando) {
                        sol.sincronizando = true;
                        storeS.put(sol);
                        solicitacoes.push(sol);
                    }
                });
            };

            tx.oncomplete = function () {
                if (visitantes.length === 0 && encomendas.length === 0 && solicitacoes.length === 0) {
                    console.log('✅ Nada para sincronizar');
                    isSincronizando = false;
                    atualizarBadgePendentes();
                    resolve(true);
                    return;
                }

                console.log(`🔄 Sincronizando: ${visitantes.length} visitantes, ${encomendas.length} encomendas, ${solicitacoes.length} solicitações...`);

                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : (function(){
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, 10) === ('csrftoken=')) {
                                cookieValue = decodeURIComponent(cookie.substring(10));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                })();

                fetch('/api/sync-offline/', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
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
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`Erro HTTP: ${r.status}`);
                        }
                        return r.json();
                    })
                    .then(result => {
                        console.log('✅ Sync resultado:', result);

                        // Remover apenas os registros enviados com sucesso
                        const clearTx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readwrite');
                        
                        visitantes.forEach(v => clearTx.objectStore('visitantes_pendentes').delete(v.tempId));
                        encomendas.forEach(e => clearTx.objectStore('encomendas_pendentes').delete(e.tempId));
                        solicitacoes.forEach(s => clearTx.objectStore('solicitacoes_pendentes').delete(s.tempId));

                        clearTx.oncomplete = () => {
                            isSincronizando = false;
                            atualizarBadgePendentes();
                            const partes = [];
                            if (result.visitantes_criados) partes.push(`${result.visitantes_criados} visitante(s)`);
                            if (result.encomendas_criadas) partes.push(`${result.encomendas_criadas} encomenda(s)`);
                            if (result.solicitacoes_criadas) partes.push(`${result.solicitacoes_criadas} solicitação(ões)`);
                            mostrarNotificacao(`✅ Sincronizado! ${partes.join(', ')} registrados por ${result.porteiro}.`, 'success');
                            resolve(true);
                        };
                        clearTx.onerror = () => {
                            isSincronizando = false;
                            resolve(false);
                        };
                    })
                    .catch(err => {
                        console.error('❌ Erro no sync:', err);
                        
                        // Reverter flag "sincronizando"
                        const revertTx = db.transaction(['visitantes_pendentes', 'encomendas_pendentes', 'solicitacoes_pendentes'], 'readwrite');
                        
                        visitantes.forEach(v => {
                            v.sincronizando = false;
                            revertTx.objectStore('visitantes_pendentes').put(v);
                        });
                        encomendas.forEach(e => {
                            e.sincronizando = false;
                            revertTx.objectStore('encomendas_pendentes').put(e);
                        });
                        solicitacoes.forEach(s => {
                            s.sincronizando = false;
                            revertTx.objectStore('solicitacoes_pendentes').put(s);
                        });

                        revertTx.oncomplete = () => {
                            isSincronizando = false;
                            mostrarNotificacao('❌ Erro ao sincronizar. Tentaremos novamente em breve.', 'danger');
                            resolve(false);
                        };
                        revertTx.onerror = () => {
                            isSincronizando = false;
                            resolve(false);
                        };
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
                syncBtn.style.display = (count > 0 && navigator.onLine) ? 'inline-block' : 'none';
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
        const formVisitante = document.getElementById('form-visitante');
        if (formVisitante) {
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
                    // Restaurar Select2/Filtros simulando os fields originais se tiverem JS
                    const selApto = document.getElementById('vis_filtro_apto');
                    if(selApto) { selApto.disabled = true; selApto.innerHTML = '<option value="">Apto...</option>'; }
                     const selMorador = document.getElementById('vis_select_morador');
                    if(selMorador) { selMorador.disabled = true; selMorador.innerHTML = '<option value="" disabled selected>--- Aguardando Filtro ---</option>'; }

                    alert('Salvo com sucesso! O registro foi armazenado localmente e será sincronizado quando a internet voltar.');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Formulário de Encomendas ---
        const formEncomenda = document.getElementById('form-encomenda');
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
                    const selAptoE = document.getElementById('filtro_apto');
                    if(selAptoE) { selAptoE.disabled = true; selAptoE.innerHTML = '<option value="">Apto...</option>'; }
                     const selMoradorE = document.getElementById('select_morador_final');
                    if(selMoradorE) { selMoradorE.disabled = true; selMoradorE.innerHTML = '<option value="" disabled selected>--- Aguardando Filtro ---</option>'; }

                    alert('Salvo com sucesso! A encomenda foi armazenada localmente e será sincronizada quando a internet voltar.');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Formulário de Solicitações ---
        const formSolicitacao = document.getElementById('form-solicitacao');
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
                    const selAptoS = document.getElementById('sol_filtro_apto');
                    if(selAptoS) { selAptoS.disabled = true; selAptoS.innerHTML = '<option value="">Apto...</option>'; }
                     const selMoradorS = document.getElementById('sol_select_morador');
                    if(selMoradorS) { selMoradorS.innerHTML = '<option value="">-- Área Comum --</option>'; }
                    
                    alert('Salvo com sucesso! A solicitação foi armazenada localmente e será sincronizada quando a internet voltar.');
                    atualizarBadgePendentes();
                });
            });
        }

        // --- Botão de sync manual ---
        const syncBtn = document.getElementById('btn-sync-manual');
        if (syncBtn) {
            syncBtn.addEventListener('click', function () {
                syncBtn.disabled = true;
                syncBtn.innerHTML = '<i class="bi bi-arrow-repeat bi-spin"></i> Sincronizando...';
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
            atualizarBadgePendentes(); // Re-checar o botão Sincronizar
            
            const banner = document.getElementById('banner-offline');
            if (banner) {
                banner.style.backgroundColor = '#198754';
                banner.style.color = '#fff';
                banner.innerHTML = '🟢 Conexão restabelecida. Sincronizando...';
                setTimeout(() => {
                    banner.style.display = 'none';
                }, 4000);
            }

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
            atualizarBadgePendentes(); // Re-checar o botão Sincronizar (deve sumir)
            
            const banner = document.getElementById('banner-offline');
            if (banner) {
                banner.style.display = 'block';
                banner.style.backgroundColor = '#fc4d4dff';
                banner.style.color = '#000';
                banner.innerHTML = '⚠️ Conexão perdida. Operando normalmente em modo offline';
            }
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
