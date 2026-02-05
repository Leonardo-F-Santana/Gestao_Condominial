import csv
import random


QUANTIDADE = 200
ARQUIVO_SAIDA = "moradores_condominio.csv"


nomes = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Barbosa", "Melo", "Costa", "Ribeiro"]
prenomes = ["João", "Maria", "José", "Ana", "Pedro", "Paula", "Carlos", "Fernanda", "Lucas", "Juliana", "Marcos", "Patrícia", "Rafael", "Camila", "Bruno", "Aline"]


blocos = [str(i) for i in range(1, 16)] 

def gerar_cpf_falso():
    return "".join([str(random.randint(0, 9)) for _ in range(11)])

print(f"Gerando {QUANTIDADE} moradores (15 Blocos, 5 Andares)...")

with open(ARQUIVO_SAIDA, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    
    writer.writerow(['nome', 'cpf', 'bloco', 'apartamento', 'telefone', 'email'])
    
    for i in range(QUANTIDADE):
        nome = f"{random.choice(prenomes)} {random.choice(nomes)} {random.choice(nomes)}"
        cpf = gerar_cpf_falso()
        
        
        bloco = random.choice(blocos)
        
        
        andar = random.randint(1, 5)
        
        
        final = random.randint(1, 4)
        
        
        apartamento = f"{andar}0{final}"
        
        telefone = f"119{random.randint(10000000, 99999999)}"
        email = f"{nome.split()[0].lower()}.{nome.split()[1].lower()}@email.com"
        
        writer.writerow([nome, cpf, bloco, apartamento, telefone, email])

print(f"✅ Arquivo '{ARQUIVO_SAIDA}' gerado com sucesso!")