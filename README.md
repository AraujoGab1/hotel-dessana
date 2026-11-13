# DESSANA AMAZON RESORT — TCC

Sistema administrativo para gerenciamento de um hotel/resort amazônico.

## Tecnologias
- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript

## Como executar no VS Code

1. Abra a pasta `Dessana_Amazon_Resort_TCC` no VS Code.
2. Abra o terminal.
3. Execute:

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

4. Instale o Flask:

```bash
pip install -r requirements.txt
```

5. Inicie:

```bash
python app.py
```

6. Abra no Chrome:

http://127.0.0.1:5000

## Evolução "padrão bangalô" (inspirada no Juma Lodge)

O hotel manteve seu nome, logo e identidade visual — apenas o conteúdo e a estrutura de quartos/experiências evoluíram:

- **Categorias**: agora são 5 bangalôs (Vista Rio, Vista Floresta, Panorâmico, Família, Premium/Presidencial), cada um com descrição detalhada, metragem, capacidade, comodidades e **galeria de fotos própria** (tabela `quarto_imagens`).
- **Página de detalhes do quarto** (`/hospede/quartos/<id>`): galeria com foto principal + miniaturas clicáveis, descrição completa, comodidades e botão de reserva.
- **Experiências**: cada uma agora tem ícone e duração, e pode ser gerenciada pelo admin em `/experiencias`.
- **Área de Lazer** (nova): piscina, restaurante, bar, deck panorâmico e espaço de bem-estar — gerenciados pelo admin em `/lazer` e exibidos ao hóspede em `/hospede/lazer`.
- **Home pública** (`/`): ganhou seções de destaque (bangalôs, experiências, lazer) puxadas direto do banco, um banner de chamada para reserva e um rodapé — mantendo o hero e a marca já existentes.
- **Admin de categorias**: o formulário ganhou campos de metragem e imagem principal, e cada card tem um link "Gerenciar fotos" para a galeria daquela categoria.
- Rodar `init_db()` + `migrate_db()` em um banco já existente **renomeia e enriquece automaticamente** as categorias antigas (Suíte Rio Negro → Bangalô Vista Rio, etc.) sem apagar reservas, hóspedes ou qualquer descrição que o admin já tenha personalizado manualmente.

## Login inicial (administração)

E-mail: admin@dessana.com
Senha: admin123

## Portal do hóspede

O sistema agora possui uma área exclusiva para hóspedes, com o mesmo layout premium da administração.

- Novos hóspedes criam a própria conta em **/cadastro** (nome, e-mail, telefone e senha).
- Após o login, o hóspede é direcionado automaticamente para o seu próprio painel — o mesmo formulário de login (`/login`) reconhece tanto usuários administrativos quanto hóspedes.
- O hóspede pode: ver seu dashboard, navegar pelos quartos/categorias com fotos e comodidades, reservar diretamente (o sistema escolhe automaticamente uma acomodação livre da categoria escolhida e verifica conflitos de data), consultar e cancelar suas próprias reservas, editar seus dados e senha, ver a página de Experiências e enviar mensagens em Contato.
- O acesso é controlado por perfil (`session['tipo']`): rotas administrativas exigem `admin`, rotas do hóspede exigem `hospede` — um perfil não acessa as páginas do outro.

## Observação
O arquivo `database/dessana.db` é criado (e migrado, se já existir) automaticamente na primeira execução via `init_db()` e `migrate_db()`.
Fotos usadas na área do hóspede ficam em `static/images/guest/` e podem ser trocadas livremente; os caminhos ficam salvos nas colunas `imagem` de `categorias` e `experiencias`.
