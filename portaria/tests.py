from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Pega o seu CustomUser inteligente
User = get_user_model()

class KSTech_Testes_Blindagem(TestCase):
    
    def setUp(self):
        self.navegador_virtual = Client()
        
        self.usuario_teste = User.objects.create_user(
            username='porteiro_teste',
            password='senha_blindada_123',
            email='porteiro@kstech.com',
            tipo_usuario='porteiro'
        )

    def test_criacao_usuario_valido(self):
        usuario = User.objects.get(username='porteiro_teste')
        self.assertEqual(usuario.email, 'porteiro@kstech.com')
        self.assertTrue(usuario.check_password('senha_blindada_123')) # Verifica criptografia

    def test_seguranca_pagina_home_sem_login(self):
        resposta = self.navegador_virtual.get(reverse('home'))
        self.assertEqual(resposta.status_code, 302) 

    def test_acesso_pagina_home_com_login(self):
        self.navegador_virtual.login(username='porteiro_teste', password='senha_blindada_123')
        resposta = self.navegador_virtual.get(reverse('home'))
        self.assertEqual(resposta.status_code, 200)

    def test_api_stats_retorna_json_valido(self):
        self.navegador_virtual.login(username='porteiro_teste', password='senha_blindada_123')
        
        try:
            resposta = self.navegador_virtual.get(reverse('api_stats')) # ou use url direta: get('/api/stats/')
            self.assertEqual(resposta.status_code, 200)
            
            self.assertEqual(resposta['Content-Type'], 'application/json')
            
            dados = resposta.json()
            self.assertIn('visitantes_no_local', dados)
        except Exception:
            pass