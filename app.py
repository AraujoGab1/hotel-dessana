from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from pathlib import Path
from functools import wraps
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "dessana.db"

app = Flask(__name__)
app.secret_key = "dessana-amazon-resort-tcc-2026"

@app.template_filter("format_date")
def format_date(value):
    """Formata datas do banco (YYYY-MM-DD) para DD/MM/YYYY."""
    if not value:
        return "—"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(value)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = get_db()
    schema = (BASE_DIR / "database" / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    user = conn.execute("SELECT id FROM usuarios WHERE email = ?", ("admin@dessana.com",)).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha, perfil) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin@dessana.com", "admin123", "Administrador")
        )
    if conn.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO categorias (nome, descricao, capacidade, valor_diaria, imagem, comodidades, metragem) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("Bangalô Vista Rio",
                 "Suspenso sobre as águas, este bangalô oferece uma conexão única com a Amazônia. Grandes aberturas emolduram a paisagem e a varanda com rede é o convite perfeito para observar o entardecer sobre o rio.",
                 2, 1250.00, "guest/suite-rio-negro.jpg",
                 "Vista para o rio, Varanda com rede, Ar-condicionado, Wi-Fi, Frigobar", "38 m²"),
                ("Bangalô Vista Floresta",
                 "Envolto pela mata nativa, este bangalô circular foi construído em madeira e palha trançada, seguindo técnicas tradicionais da região. Ideal para quem busca silêncio e uma experiência imersiva na floresta.",
                 2, 1150.00, "guest/chale-arara.jpg",
                 "Vista para a floresta, Varanda com rede, Ventilação natural, Wi-Fi, Deck suspenso", "34 m²"),
                ("Bangalô Panorâmico",
                 "Erguido em um dos pontos mais altos da propriedade, este bangalô oferece vista panorâmica de 360° para o encontro das águas e o dossel da floresta — perfeito para o nascer e o pôr do sol.",
                 3, 1550.00, "guest/exp-trilhas.jpg",
                 "Vista 360°, Varanda ampla com rede, Wi-Fi, Ar-condicionado, Iluminação natural", "42 m²"),
                ("Bangalô Família",
                 "Espaçoso e pensado para grupos e famílias, este bangalô reúne múltiplas camas, área de convivência e varanda ampla, sem abrir mão do conforto e da vista para a natureza.",
                 5, 1850.00, "guest/quarto-familia.jpg",
                 "Camas extras, Sala de estar, Varanda compartilhada, Wi-Fi, Ar-condicionado", "56 m²"),
                ("Bangalô Premium Presidencial",
                 "Nossa acomodação mais exclusiva, com piscina privativa suspensa sobre o rio, sala de estar integrada e serviço de quarto dedicado — a experiência definitiva de luxo na Amazônia.",
                 4, 2600.00, "guest/quarto-premium.jpg",
                 "Piscina privativa, Sala de estar, Serviço de quarto, Wi-Fi, Vista panorâmica", "68 m²"),
            ]
        )
    if conn.execute("SELECT COUNT(*) FROM quartos").fetchone()[0] == 0:
        cats = {r["nome"]: r["id"] for r in conn.execute("SELECT id, nome FROM categorias").fetchall()}
        quartos_padrao = [
            ("101", "Bangalô Vista Rio", "Disponível", "Vista para o rio"),
            ("102", "Bangalô Vista Rio", "Disponível", "Varanda privativa"),
            ("201", "Bangalô Vista Floresta", "Disponível", "Acesso por passarela"),
            ("202", "Bangalô Vista Floresta", "Manutenção", "Manutenção preventiva"),
            ("401", "Bangalô Panorâmico", "Disponível", "Ponto mais alto da propriedade"),
            ("501", "Bangalô Família", "Disponível", "Duas camas de casal + beliche"),
            ("502", "Bangalô Família", "Disponível", "Varanda compartilhada"),
            ("301", "Bangalô Premium Presidencial", "Disponível", "Piscina privativa"),
        ]
        for numero, nome_categoria, status, obs in quartos_padrao:
            if nome_categoria in cats:
                conn.execute(
                    "INSERT INTO quartos (numero, categoria_id, status, observacoes) VALUES (?, ?, ?, ?)",
                    (numero, cats[nome_categoria], status, obs)
                )
    if conn.execute("SELECT COUNT(*) FROM quarto_imagens").fetchone()[0] == 0:
        cats = {r["nome"]: r["id"] for r in conn.execute("SELECT id, nome FROM categorias").fetchall()}
        galeria_padrao = {
            "Bangalô Vista Rio": ["guest/suite-rio-negro.jpg", "guest/hero-rio.jpg", "guest/exp-lazer.jpg"],
            "Bangalô Vista Floresta": ["guest/chale-arara.jpg", "guest/exp-trilhas.jpg", "guest/hero-rio.jpg"],
            "Bangalô Panorâmico": ["guest/exp-trilhas.jpg", "guest/hero-rio.jpg", "guest/chale-arara.jpg"],
            "Bangalô Família": ["guest/exp-lazer.jpg", "guest/exp-gastronomia.jpg", "guest/hero-rio.jpg"],
            "Bangalô Premium Presidencial": ["guest/villa-dessana.jpg", "guest/exp-spa.jpg", "guest/suite-rio-negro.jpg"],
        }
        for nome, urls in galeria_padrao.items():
            if nome not in cats:
                continue
            for i, url in enumerate(urls):
                conn.execute(
                    "INSERT INTO quarto_imagens (categoria_id, url, ordem) VALUES (?, ?, ?)",
                    (cats[nome], url, i)
                )
    if conn.execute("SELECT COUNT(*) FROM lazer").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO lazer (nome, descricao, imagem, icone, ordem) VALUES (?, ?, ?, ?, ?)",
            [
                ("Piscina Flutuante", "Deck suspenso sobre o rio com piscina integrada à paisagem e vista de 360° para a floresta.", "guest/lazer-piscina.jpg", "🏊", 1),
                ("Restaurante", "Cardápio autoral com ingredientes regionais, servido em salão com vista panorâmica para o rio.", "guest/lazer-restaurante.jpg", "🍽️", 2),
                ("Bar Flutuante", "Drinks autorais e coquetéis com frutas amazônicas, ao entardecer sobre as águas.", "guest/lazer-bar.jpg", "🍹", 3),
                ("Deck Panorâmico", "Espaço aberto para contemplação, ioga e observação de aves, suspenso entre a floresta e o rio.", "guest/exp-trilhas.jpg", "🌅", 4),
                ("Espaço de Bem-estar", "Área de descanso e massagens relaxantes em deck suspenso sobre as águas da Amazônia.", "guest/exp-spa.jpg", "🧘", 5),
            ]
        )
    conn.commit()
    conn.close()

def migrate_db():
    """Ajusta bancos já existentes (criados antes das evoluções mais recentes) sem perder dados."""
    conn = get_db()

    cols_hospedes = {r["name"] for r in conn.execute("PRAGMA table_info(hospedes)")}
    if "senha" not in cols_hospedes:
        conn.execute("ALTER TABLE hospedes ADD COLUMN senha TEXT")

    cols_categorias = {r["name"] for r in conn.execute("PRAGMA table_info(categorias)")}
    if "imagem" not in cols_categorias:
        conn.execute("ALTER TABLE categorias ADD COLUMN imagem TEXT")
    if "comodidades" not in cols_categorias:
        conn.execute("ALTER TABLE categorias ADD COLUMN comodidades TEXT")
    if "metragem" not in cols_categorias:
        conn.execute("ALTER TABLE categorias ADD COLUMN metragem TEXT")

    cols_reservas = {r["name"] for r in conn.execute("PRAGMA table_info(reservas)")}
    if "valor_total" not in cols_reservas:
        conn.execute("ALTER TABLE reservas ADD COLUMN valor_total REAL")

    conn.execute("""CREATE TABLE IF NOT EXISTS experiencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT,
        imagem TEXT,
        duracao TEXT,
        icone TEXT,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    cols_experiencias = {r["name"] for r in conn.execute("PRAGMA table_info(experiencias)")}
    if "duracao" not in cols_experiencias:
        conn.execute("ALTER TABLE experiencias ADD COLUMN duracao TEXT")
    if "icone" not in cols_experiencias:
        conn.execute("ALTER TABLE experiencias ADD COLUMN icone TEXT")

    conn.execute("""CREATE TABLE IF NOT EXISTS mensagens_contato (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospede_id INTEGER,
        nome TEXT NOT NULL,
        email TEXT,
        assunto TEXT,
        mensagem TEXT NOT NULL,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hospede_id) REFERENCES hospedes(id)
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS quarto_imagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        ordem INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS lazer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        imagem TEXT,
        icone TEXT,
        ordem INTEGER NOT NULL DEFAULT 0,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")

    # Evolui as categorias antigas para o padrão "bangalô" (só renomeia se o admin
    # ainda não tiver editado o nome padrão anterior — não sobrescreve customizações)
    descricoes_originais_v1 = {
        "Suíte Rio Negro": "Suíte premium com vista para a floresta.",
        "Chalé Arara": "Chalé privativo integrado à natureza.",
        "Villa Dessana": "Acomodação exclusiva para famílias.",
    }
    renomear_categorias = {
        "Suíte Rio Negro": (
            "Bangalô Vista Rio",
            "Suspenso sobre as águas, este bangalô oferece uma conexão única com a Amazônia. Grandes aberturas emolduram a paisagem e a varanda com rede é o convite perfeito para observar o entardecer sobre o rio.",
            "guest/suite-rio-negro.jpg",
            "Vista para o rio, Varanda com rede, Ar-condicionado, Wi-Fi, Frigobar",
            "38 m²"
        ),
        "Chalé Arara": (
            "Bangalô Vista Floresta",
            "Envolto pela mata nativa, este bangalô circular foi construído em madeira e palha trançada, seguindo técnicas tradicionais da região. Ideal para quem busca silêncio e uma experiência imersiva na floresta.",
            "guest/chale-arara.jpg",
            "Vista para a floresta, Varanda com rede, Ventilação natural, Wi-Fi, Deck suspenso",
            "34 m²"
        ),
        "Villa Dessana": (
            "Bangalô Premium Presidencial",
            "Nossa acomodação mais exclusiva, com piscina privativa suspensa sobre o rio, sala de estar integrada e serviço de quarto dedicado — a experiência definitiva de luxo na Amazônia.",
            "guest/villa-dessana.jpg",
            "Piscina privativa, Sala de estar, Serviço de quarto, Wi-Fi, Vista panorâmica",
            "68 m²"
        ),
    }
    for nome_antigo, (novo_nome, nova_desc, nova_img, novas_comodidades, nova_metragem) in renomear_categorias.items():
        linha = conn.execute("SELECT descricao FROM categorias WHERE nome = ?", (nome_antigo,)).fetchone()
        if not linha:
            continue
        descricao_e_original = (linha["descricao"] or "") == descricoes_originais_v1.get(nome_antigo, "")
        if descricao_e_original:
            # admin nunca editou a descrição padrão: aplica o texto novo no estilo bangalô
            conn.execute(
                """UPDATE categorias SET nome = ?, descricao = ?, imagem = COALESCE(NULLIF(imagem,''), ?),
                   comodidades = COALESCE(NULLIF(comodidades,''), ?), metragem = COALESCE(NULLIF(metragem,''), ?)
                   WHERE nome = ?""",
                (novo_nome, nova_desc, nova_img, novas_comodidades, nova_metragem, nome_antigo)
            )
        else:
            # admin já personalizou a descrição: só atualiza o nome/campos vazios, preserva o texto dele
            conn.execute(
                """UPDATE categorias SET nome = ?, imagem = COALESCE(NULLIF(imagem,''), ?),
                   comodidades = COALESCE(NULLIF(comodidades,''), ?), metragem = COALESCE(NULLIF(metragem,''), ?)
                   WHERE nome = ?""",
                (novo_nome, nova_img, novas_comodidades, nova_metragem, nome_antigo)
            )

    # Acrescenta as categorias novas do padrão bangalô, caso ainda não existam
    nomes_atuais = {r["nome"] for r in conn.execute("SELECT nome FROM categorias").fetchall()}
    novas_categorias = [
        ("Bangalô Panorâmico",
         "Erguido em um dos pontos mais altos da propriedade, este bangalô oferece vista panorâmica de 360° para o encontro das águas e o dossel da floresta — perfeito para o nascer e o pôr do sol.",
         3, 1550.00, "guest/exp-trilhas.jpg",
         "Vista 360°, Varanda ampla com rede, Wi-Fi, Ar-condicionado, Iluminação natural", "42 m²",
         [("401", "Disponível", "Ponto mais alto da propriedade")]),
        ("Bangalô Família",
         "Espaçoso e pensado para grupos e famílias, este bangalô reúne múltiplas camas, área de convivência e varanda ampla, sem abrir mão do conforto e da vista para a natureza.",
         5, 1850.00, "guest/quarto-familia.jpg",
         "Camas extras, Sala de estar, Varanda compartilhada, Wi-Fi, Ar-condicionado", "56 m²",
         [("501", "Disponível", "Duas camas de casal + beliche"), ("502", "Disponível", "Varanda compartilhada")]),
    ]
    for nome, desc, cap, valor, img, comodidades, metragem, quartos_novos in novas_categorias:
        if nome not in nomes_atuais:
            cur = conn.execute(
                "INSERT INTO categorias (nome, descricao, capacidade, valor_diaria, imagem, comodidades, metragem) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nome, desc, cap, valor, img, comodidades, metragem)
            )
            categoria_id = cur.lastrowid
            for numero, status, obs in quartos_novos:
                existe_quarto = conn.execute("SELECT id FROM quartos WHERE numero = ?", (numero,)).fetchone()
                if not existe_quarto:
                    conn.execute(
                        "INSERT INTO quartos (numero, categoria_id, status, observacoes) VALUES (?, ?, ?, ?)",
                        (numero, categoria_id, status, obs)
                    )

    # Preenche imagens/comodidades/metragem de qualquer categoria que ainda esteja sem (ex: criada manualmente)
    conn.execute("UPDATE categorias SET imagem = ? WHERE imagem IS NULL OR imagem = ''", ("guest/hero-rio.jpg",))
    conn.execute("UPDATE categorias SET comodidades = ? WHERE comodidades IS NULL OR comodidades = ''",
                 ("Wi-Fi, Ar-condicionado, Vista para a floresta",))
    conn.execute("UPDATE categorias SET metragem = ? WHERE metragem IS NULL OR metragem = ''", ("30 m²",))

    # Galeria de fotos: garante ao menos a foto principal na tabela quarto_imagens para toda categoria
    categorias_sem_galeria = conn.execute("""
        SELECT c.id, c.imagem FROM categorias c
        WHERE NOT EXISTS (SELECT 1 FROM quarto_imagens qi WHERE qi.categoria_id = c.id)
    """).fetchall()
    for c in categorias_sem_galeria:
        conn.execute(
            "INSERT INTO quarto_imagens (categoria_id, url, ordem) VALUES (?, ?, 0)",
            (c["id"], c["imagem"] or "guest/hero-rio.jpg")
        )

    if conn.execute("SELECT COUNT(*) FROM experiencias").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO experiencias (titulo, categoria, descricao, imagem, duracao, icone) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Passeios na Amazônia", "Passeios",
                 "Saídas de barco para observação de botos, vitórias-régias e o pôr do sol sobre o rio.",
                 "guest/experiencia-passeios.jpg", "2h", "🚤"),
                ("Trilhas na Floresta", "Trilhas",
                 "Caminhadas guiadas pela mata com especialistas em fauna e flora regionais.",
                 "guest/experiencia-trilhas.jpg", "1h30", "🥾"),
                ("Gastronomia Amazônica", "Gastronomia",
                 "Pratos autorais com ingredientes regionais, servidos com vista para o rio.",
                 "guest/experiencia-gastronomia.jpg", "Todos os dias", "🍽️"),
                ("Spa & Bem-estar", "Spa",
                 "Massagens e rituais relaxantes em deck suspenso sobre as águas.",
                 "guest/exp-spa.jpg", "50 min", "🧘"),
                ("Observação de Fauna", "Passeios",
                 "Passeios noturnos guiados para observação de jacarés, aves e outros animais da região.",
                 "guest/hero-rio.jpg", "1h", "🦜"),
            ]
        )
    else:
        # completa duração/ícone para experiências criadas antes desse campo existir
        conn.execute("UPDATE experiencias SET duracao = COALESCE(NULLIF(duracao,''), '1h')")
        conn.execute("UPDATE experiencias SET icone = COALESCE(NULLIF(icone,''), '🌿')")

    conn.commit()
    conn.close()

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session or session.get("tipo") != "admin":
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def hospede_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session or session.get("tipo") != "hospede":
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    if session.get("tipo") == "admin":
        return redirect(url_for("dashboard"))
    if session.get("tipo") == "hospede":
        return redirect(url_for("hospede_dashboard"))
    conn = get_db()
    destaque_quartos = conn.execute("SELECT * FROM categorias ORDER BY valor_diaria ASC LIMIT 3").fetchall()
    destaque_experiencias = conn.execute("SELECT * FROM experiencias ORDER BY id ASC LIMIT 3").fetchall()
    destaque_lazer = conn.execute("SELECT * FROM lazer ORDER BY ordem ASC LIMIT 3").fetchall()
    conn.close()
    return render_template(
        "home.html",
        destaque_quartos=destaque_quartos,
        destaque_experiencias=destaque_experiencias,
        destaque_lazer=destaque_lazer,
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        # O formulário administrativo envia destino=admin. Nesse fluxo, nunca
        # autentique uma conta de hóspede nem a redirecione ao portal público.
        destino = request.form.get("destino") or session.get("login_destino") or request.args.get("proximo")
        conn = get_db()

        user = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
            (email, senha)
        ).fetchone()
        if user:
            conn.close()
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["nome"]
            session["perfil"] = user["perfil"]
            session["tipo"] = "admin"
            return redirect(url_for("dashboard"))

        if destino == "admin":
            conn.close()
            flash("Acesso restrito: use o e-mail e a senha de uma conta administrativa.", "danger")
            return render_template("login.html", destino="admin")

        hospede = conn.execute(
            "SELECT * FROM hospedes WHERE email = ? AND senha IS NOT NULL AND senha = ?",
            (email, senha)
        ).fetchone()
        conn.close()
        if hospede:
            session.clear()
            session["user_id"] = hospede["id"]
            session["user_name"] = hospede["nome"]
            session["perfil"] = "Hóspede"
            session["tipo"] = "hospede"
            return redirect(url_for("hospede_dashboard"))

        flash("E-mail ou senha inválidos.", "danger")
    destino = request.args.get("proximo") or session.get("login_destino")
    return render_template("login.html", destino=destino)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        if not nome or not email or not senha:
            flash("Preencha nome, e-mail e senha para continuar.", "danger")
            return render_template("cadastro.html", nome=nome, email=email, telefone=telefone)
        if senha != confirmar:
            flash("As senhas informadas não coincidem.", "danger")
            return render_template("cadastro.html", nome=nome, email=email, telefone=telefone)

        conn = get_db()
        existente = conn.execute("SELECT id, senha FROM hospedes WHERE email = ?", (email,)).fetchone()
        if existente and existente["senha"]:
            conn.close()
            flash("Este e-mail já possui acesso ao portal. Faça login.", "danger")
            return render_template("cadastro.html")
        if existente:
            conn.execute(
                "UPDATE hospedes SET nome = ?, telefone = ?, senha = ? WHERE id = ?",
                (nome, telefone, senha, existente["id"])
            )
        else:
            conn.execute(
                "INSERT INTO hospedes (nome, email, telefone, senha) VALUES (?, ?, ?, ?)",
                (nome, email, telefone, senha)
            )
        conn.commit()
        conn.close()
        flash("Cadastro realizado com sucesso! Faça login para acessar o portal.", "success")
        return redirect(url_for("login"))
    return render_template("cadastro.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/administracao")
def administracao():
    """Entrada dedicada à gestão do hotel; exige autenticação administrativa."""
    if session.get("tipo") == "admin" and session.get("user_id"):
        return redirect(url_for("dashboard"))
    # Marca a intenção para o formulário de login manter o fluxo administrativo.
    session["login_destino"] = "admin"
    return redirect(url_for("login", proximo="admin"))

@app.route("/dashboard")
@admin_required
def dashboard():
    conn = get_db()
    total_quartos = conn.execute("SELECT COUNT(*) FROM quartos").fetchone()[0]
    ocupados = conn.execute("SELECT COUNT(*) FROM quartos WHERE status = 'Ocupado'").fetchone()[0]
    disponiveis = conn.execute("SELECT COUNT(*) FROM quartos WHERE status = 'Disponível'").fetchone()[0]
    reservas = conn.execute("SELECT COUNT(*) FROM reservas WHERE status = 'Confirmada'").fetchone()[0]
    checkins = conn.execute(
        "SELECT COUNT(*) FROM reservas WHERE data_entrada = date('now') AND status = 'Confirmada'"
    ).fetchone()[0]
    checkouts = conn.execute(
        "SELECT COUNT(*) FROM reservas WHERE data_saida = date('now') AND status = 'Confirmada'"
    ).fetchone()[0]
    hospedes = conn.execute("SELECT COUNT(*) FROM hospedes").fetchone()[0]
    taxa = round((ocupados / total_quartos) * 100, 1) if total_quartos else 0

    ultimas = conn.execute("""
        SELECT r.id, r.data_entrada, r.data_saida, r.quantidade_hospedes, r.status,
               h.nome AS hospede, q.numero AS quarto, c.nome AS categoria
        FROM reservas r
        JOIN hospedes h ON h.id = r.hospede_id
        JOIN quartos q ON q.id = r.quarto_id
        JOIN categorias c ON c.id = q.categoria_id
        ORDER BY r.id DESC LIMIT 6
    """).fetchall()
    conn.close()
    return render_template(
        "dashboard.html",
        total_quartos=total_quartos, ocupados=ocupados, disponiveis=disponiveis,
        reservas=reservas, checkins=checkins, checkouts=checkouts,
        hospedes=hospedes, taxa=taxa, ultimas=ultimas
    )

@app.route("/hospedes")
@admin_required
def hospedes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM hospedes ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("hospedes.html", hospedes=rows)

@app.route("/hospedes/salvar", methods=["POST"])
@admin_required
def salvar_hospede():
    conn = get_db()
    conn.execute(
        "INSERT INTO hospedes (nome, cpf, telefone, email, observacoes) VALUES (?, ?, ?, ?, ?)",
        tuple(request.form.get(k, "").strip() for k in ["nome", "cpf", "telefone", "email", "observacoes"])
    )
    conn.commit()
    conn.close()
    flash("Hóspede cadastrado com sucesso.", "success")
    return redirect(url_for("hospedes"))

@app.route("/hospedes/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_hospede(id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM hospedes WHERE id = ?", (id,))
        conn.commit()
        flash("Hóspede excluído.", "success")
    except sqlite3.IntegrityError:
        flash("Não é possível excluir este hóspede porque existem reservas vinculadas.", "danger")
    conn.close()
    return redirect(url_for("hospedes"))

@app.route("/categorias")
@admin_required
def categorias():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categorias ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("categorias.html", categorias=rows)

@app.route("/categorias/salvar", methods=["POST"])
@admin_required
def salvar_categoria():
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO categorias (nome, descricao, capacidade, valor_diaria, imagem, comodidades, metragem) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            request.form.get("nome", "").strip(),
            request.form.get("descricao", "").strip(),
            int(request.form.get("capacidade", 1)),
            float(request.form.get("valor_diaria", 0).replace(",", ".")),
            request.form.get("imagem", "").strip() or None,
            request.form.get("comodidades", "").strip() or None,
            request.form.get("metragem", "").strip() or None,
        )
    )
    imagem = request.form.get("imagem", "").strip()
    if imagem:
        conn.execute(
            "INSERT INTO quarto_imagens (categoria_id, url, ordem) VALUES (?, ?, 0)",
            (cursor.lastrowid, imagem)
        )
    conn.commit()
    conn.close()
    flash("Categoria cadastrada com sucesso.", "success")
    return redirect(url_for("categorias"))

@app.route("/categorias/<int:id>/imagens")
@admin_required
def categoria_imagens(id):
    conn = get_db()
    categoria = conn.execute("SELECT * FROM categorias WHERE id = ?", (id,)).fetchone()
    if not categoria:
        conn.close()
        flash("Categoria não encontrada.", "danger")
        return redirect(url_for("categorias"))
    imagens = conn.execute(
        "SELECT * FROM quarto_imagens WHERE categoria_id = ? ORDER BY ordem, id", (id,)
    ).fetchall()
    conn.close()
    return render_template("categoria_imagens.html", categoria=categoria, imagens=imagens)

@app.route("/categorias/<int:id>/imagens/salvar", methods=["POST"])
@admin_required
def salvar_categoria_imagem(id):
    url = request.form.get("url", "").strip()
    if url:
        conn = get_db()
        maior_ordem = conn.execute(
            "SELECT COALESCE(MAX(ordem), -1) FROM quarto_imagens WHERE categoria_id = ?", (id,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO quarto_imagens (categoria_id, url, ordem) VALUES (?, ?, ?)",
            (id, url, maior_ordem + 1)
        )
        conn.commit()
        conn.close()
        flash("Imagem adicionada à galeria.", "success")
    return redirect(url_for("categoria_imagens", id=id))

@app.route("/categorias/imagens/excluir/<int:img_id>", methods=["POST"])
@admin_required
def excluir_categoria_imagem(img_id):
    conn = get_db()
    img = conn.execute("SELECT categoria_id FROM quarto_imagens WHERE id = ?", (img_id,)).fetchone()
    conn.execute("DELETE FROM quarto_imagens WHERE id = ?", (img_id,))
    conn.commit()
    conn.close()
    flash("Imagem removida da galeria.", "success")
    return redirect(url_for("categoria_imagens", id=img["categoria_id"] if img else 0))

@app.route("/quartos")
@admin_required
def quartos():
    conn = get_db()
    rows = conn.execute("""
        SELECT q.*, c.nome AS categoria
        FROM quartos q JOIN categorias c ON c.id = q.categoria_id
        ORDER BY q.numero
    """).fetchall()
    cats = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
    conn.close()
    return render_template("quartos.html", quartos=rows, categorias=cats)

@app.route("/quartos/salvar", methods=["POST"])
@admin_required
def salvar_quarto():
    conn = get_db()
    conn.execute(
        "INSERT INTO quartos (numero, categoria_id, status, observacoes) VALUES (?, ?, ?, ?)",
        (
            request.form.get("numero", "").strip(),
            int(request.form.get("categoria_id")),
            request.form.get("status", "Disponível"),
            request.form.get("observacoes", "").strip()
        )
    )
    conn.commit()
    conn.close()
    flash("Quarto cadastrado com sucesso.", "success")
    return redirect(url_for("quartos"))

@app.route("/reservas")
@admin_required
def reservas():
    conn = get_db()
    rows = conn.execute("""
        SELECT r.*, h.nome AS hospede, q.numero AS quarto, c.nome AS categoria
        FROM reservas r
        JOIN hospedes h ON h.id = r.hospede_id
        JOIN quartos q ON q.id = r.quarto_id
        JOIN categorias c ON c.id = q.categoria_id
        ORDER BY r.data_entrada DESC, r.id DESC
    """).fetchall()
    hospedes_rows = conn.execute("SELECT * FROM hospedes ORDER BY nome").fetchall()
    quartos_rows = conn.execute("""
        SELECT q.id, q.numero, q.status, c.nome AS categoria, c.capacidade
        FROM quartos q JOIN categorias c ON c.id = q.categoria_id
        ORDER BY q.numero
    """).fetchall()
    conn.close()
    return render_template("reservas.html", reservas=rows, hospedes=hospedes_rows, quartos=quartos_rows)

@app.route("/reservas/salvar", methods=["POST"])
@admin_required
def salvar_reserva():
    entrada = request.form.get("data_entrada")
    saida = request.form.get("data_saida")
    quarto_id = int(request.form.get("quarto_id"))
    hospede_id = int(request.form.get("hospede_id"))
    quantidade = int(request.form.get("quantidade_hospedes", 1))

    if not entrada or not saida or entrada >= saida:
        flash("A data de saída deve ser posterior à data de entrada.", "danger")
        return redirect(url_for("reservas"))

    conn = get_db()
    quarto = conn.execute("""
        SELECT q.*, c.capacidade, c.valor_diaria FROM quartos q
        JOIN categorias c ON c.id = q.categoria_id WHERE q.id = ?
    """, (quarto_id,)).fetchone()

    if not quarto:
        conn.close()
        flash("Quarto não encontrado.", "danger")
        return redirect(url_for("reservas"))

    if quantidade > quarto["capacidade"]:
        conn.close()
        flash("A quantidade de hóspedes ultrapassa a capacidade do quarto.", "danger")
        return redirect(url_for("reservas"))

    conflito = conn.execute("""
        SELECT id FROM reservas
        WHERE quarto_id = ?
          AND status IN ('Confirmada', 'Check-in')
          AND data_entrada < ?
          AND data_saida > ?
    """, (quarto_id, saida, entrada)).fetchone()

    if conflito:
        conn.close()
        flash("Este quarto já possui uma reserva para esse período.", "danger")
        return redirect(url_for("reservas"))

    noites = (datetime.strptime(saida, "%Y-%m-%d") - datetime.strptime(entrada, "%Y-%m-%d")).days
    valor_total = round(noites * quarto["valor_diaria"], 2)

    conn.execute("""
        INSERT INTO reservas (hospede_id, quarto_id, data_entrada, data_saida, quantidade_hospedes, status, valor_total, observacoes)
        VALUES (?, ?, ?, ?, ?, 'Confirmada', ?, ?)
    """, (
        hospede_id, quarto_id, entrada, saida, quantidade, valor_total,
        request.form.get("observacoes", "").strip()
    ))
    conn.commit()
    conn.close()
    flash("Reserva confirmada e disponibilidade verificada.", "success")
    return redirect(url_for("reservas"))

@app.route("/reservas/status/<int:id>/<status>", methods=["POST"])
@admin_required
def alterar_status_reserva(id, status):
    permitidos = {"Confirmada", "Check-in", "Finalizada", "Cancelada"}
    if status not in permitidos:
        flash("Status inválido.", "danger")
        return redirect(url_for("reservas"))
    conn = get_db()
    conn.execute("UPDATE reservas SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()
    flash("Status da reserva atualizado.", "success")
    return redirect(url_for("reservas"))

@app.route("/usuarios")
@admin_required
def usuarios():
    conn = get_db()
    rows = conn.execute("SELECT id, nome, email, perfil FROM usuarios ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=rows)

@app.route("/usuarios/salvar", methods=["POST"])
@admin_required
def salvar_usuario():
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha, perfil) VALUES (?, ?, ?, ?)",
            (
                request.form.get("nome", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("senha", ""),
                request.form.get("perfil", "Funcionário")
            )
        )
        conn.commit()
        flash("Usuário cadastrado.", "success")
    except sqlite3.IntegrityError:
        flash("Este e-mail já está cadastrado.", "danger")
    conn.close()
    return redirect(url_for("usuarios"))

@app.route("/relatorios")
@admin_required
def relatorios():
    conn = get_db()
    por_categoria = conn.execute("""
        SELECT c.nome, COUNT(q.id) AS quantidade
        FROM categorias c LEFT JOIN quartos q ON q.categoria_id = c.id
        GROUP BY c.id ORDER BY quantidade DESC
    """).fetchall()
    por_status = conn.execute("""
        SELECT status, COUNT(*) AS quantidade FROM reservas GROUP BY status
    """).fetchall()
    faturamento = conn.execute("""
        SELECT COALESCE(SUM((julianday(data_saida)-julianday(data_entrada))*c.valor_diaria),0)
        FROM reservas r
        JOIN quartos q ON q.id = r.quarto_id
        JOIN categorias c ON c.id = q.categoria_id
        WHERE r.status IN ('Confirmada','Check-in','Finalizada')
    """).fetchone()[0]
    conn.close()
    return render_template("relatorios.html", por_categoria=por_categoria, por_status=por_status, faturamento=faturamento)

@app.route("/api/dashboard")
@admin_required
def api_dashboard():
    conn = get_db()
    data = {
        "quartos": conn.execute("SELECT COUNT(*) FROM quartos").fetchone()[0],
        "hospedes": conn.execute("SELECT COUNT(*) FROM hospedes").fetchone()[0],
        "reservas": conn.execute("SELECT COUNT(*) FROM reservas").fetchone()[0],
        "disponiveis": conn.execute("SELECT COUNT(*) FROM quartos WHERE status='Disponível'").fetchone()[0],
    }
    conn.close()
    return jsonify(data)

# ============================================================
# ADMINISTRAÇÃO — EXPERIÊNCIAS E ÁREA DE LAZER
# ============================================================

@app.route("/experiencias")
@admin_required
def experiencias_admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM experiencias ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("experiencias_admin.html", experiencias=rows)

@app.route("/experiencias/salvar", methods=["POST"])
@admin_required
def salvar_experiencia():
    conn = get_db()
    conn.execute(
        "INSERT INTO experiencias (titulo, categoria, descricao, imagem, duracao, icone) VALUES (?, ?, ?, ?, ?, ?)",
        (
            request.form.get("titulo", "").strip(),
            request.form.get("categoria", "").strip(),
            request.form.get("descricao", "").strip(),
            request.form.get("imagem", "").strip() or None,
            request.form.get("duracao", "").strip() or None,
            request.form.get("icone", "").strip() or "🌿",
        )
    )
    conn.commit()
    conn.close()
    flash("Experiência cadastrada com sucesso.", "success")
    return redirect(url_for("experiencias_admin"))

@app.route("/experiencias/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_experiencia(id):
    conn = get_db()
    conn.execute("DELETE FROM experiencias WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Experiência removida.", "success")
    return redirect(url_for("experiencias_admin"))

@app.route("/lazer")
@admin_required
def lazer_admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM lazer ORDER BY ordem, id").fetchall()
    conn.close()
    return render_template("lazer_admin.html", itens=rows)

@app.route("/lazer/salvar", methods=["POST"])
@admin_required
def salvar_lazer():
    conn = get_db()
    maior_ordem = conn.execute("SELECT COALESCE(MAX(ordem), 0) FROM lazer").fetchone()[0]
    conn.execute(
        "INSERT INTO lazer (nome, descricao, imagem, icone, ordem) VALUES (?, ?, ?, ?, ?)",
        (
            request.form.get("nome", "").strip(),
            request.form.get("descricao", "").strip(),
            request.form.get("imagem", "").strip() or None,
            request.form.get("icone", "").strip() or "🌿",
            maior_ordem + 1,
        )
    )
    conn.commit()
    conn.close()
    flash("Item de lazer cadastrado com sucesso.", "success")
    return redirect(url_for("lazer_admin"))

@app.route("/lazer/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_lazer(id):
    conn = get_db()
    conn.execute("DELETE FROM lazer WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Item de lazer removido.", "success")
    return redirect(url_for("lazer_admin"))

# ============================================================
# ÁREA DO HÓSPEDE
# ============================================================

@app.route("/hospede/dashboard")
@hospede_required
def hospede_dashboard():
    conn = get_db()
    hospede_id = session["user_id"]

    total_reservas = conn.execute(
        "SELECT COUNT(*) FROM reservas WHERE hospede_id = ?", (hospede_id,)
    ).fetchone()[0]

    proxima = conn.execute("""
        SELECT r.*, c.nome AS categoria, c.imagem, q.numero AS quarto
        FROM reservas r
        JOIN quartos q ON q.id = r.quarto_id
        JOIN categorias c ON c.id = q.categoria_id
        WHERE r.hospede_id = ? AND r.status IN ('Confirmada', 'Check-in')
          AND r.data_saida >= date('now')
        ORDER BY r.data_entrada ASC LIMIT 1
    """, (hospede_id,)).fetchone()

    dias_checkin = None
    if proxima:
        try:
            dias_checkin = (datetime.strptime(proxima["data_entrada"], "%Y-%m-%d").date() - datetime.now().date()).days
        except (ValueError, TypeError):
            dias_checkin = None

    status_atual = "Sem hospedagem ativa"
    em_andamento = conn.execute("""
        SELECT status FROM reservas
        WHERE hospede_id = ? AND status = 'Check-in'
        ORDER BY id DESC LIMIT 1
    """, (hospede_id,)).fetchone()
    if em_andamento:
        status_atual = "Hospedado no resort"
    elif proxima:
        status_atual = "Reserva confirmada"

    conn.close()
    return render_template(
        "hospede_dashboard.html",
        total_reservas=total_reservas, proxima=proxima,
        dias_checkin=dias_checkin, status_atual=status_atual
    )

@app.route("/hospede/quartos")
@hospede_required
def hospede_quartos():
    conn = get_db()
    categorias_rows = conn.execute("""
        SELECT c.*,
          (SELECT COUNT(*) FROM quartos q WHERE q.categoria_id = c.id AND q.status = 'Disponível') AS disponiveis
        FROM categorias c
        ORDER BY c.valor_diaria ASC
    """).fetchall()
    conn.close()
    return render_template("hospede_quartos.html", categorias=categorias_rows)

@app.route("/hospede/quartos/<int:id>")
@hospede_required
def hospede_quarto_detalhe(id):
    conn = get_db()
    categoria = conn.execute("""
        SELECT c.*,
          (SELECT COUNT(*) FROM quartos q WHERE q.categoria_id = c.id AND q.status = 'Disponível') AS disponiveis
        FROM categorias c WHERE c.id = ?
    """, (id,)).fetchone()
    if not categoria:
        conn.close()
        flash("Acomodação não encontrada.", "danger")
        return redirect(url_for("hospede_quartos"))
    imagens = conn.execute(
        "SELECT * FROM quarto_imagens WHERE categoria_id = ? ORDER BY ordem, id", (id,)
    ).fetchall()
    if not imagens:
        imagens = [{"url": categoria["imagem"] or "guest/hero-rio.jpg"}]
    conn.close()
    return render_template("hospede_quarto_detalhe.html", categoria=categoria, imagens=imagens)

@app.route("/hospede/reservas/nova", methods=["POST"])
@hospede_required
def hospede_nova_reserva():
    categoria_id = int(request.form.get("categoria_id"))
    entrada = request.form.get("data_entrada")
    saida = request.form.get("data_saida")
    quantidade = int(request.form.get("quantidade_hospedes", 1))
    hospede_id = session["user_id"]

    if not entrada or not saida or entrada >= saida:
        flash("A data de saída deve ser posterior à data de entrada.", "danger")
        return redirect(url_for("hospede_quartos"))

    conn = get_db()
    categoria = conn.execute("SELECT * FROM categorias WHERE id = ?", (categoria_id,)).fetchone()
    if not categoria:
        conn.close()
        flash("Acomodação não encontrada.", "danger")
        return redirect(url_for("hospede_quartos"))

    if quantidade > categoria["capacidade"]:
        conn.close()
        flash("A quantidade de hóspedes ultrapassa a capacidade desta acomodação.", "danger")
        return redirect(url_for("hospede_quartos"))

    quarto_livre = conn.execute("""
        SELECT q.id FROM quartos q
        WHERE q.categoria_id = ? AND q.status != 'Manutenção'
          AND q.id NOT IN (
            SELECT quarto_id FROM reservas
            WHERE status IN ('Confirmada', 'Check-in')
              AND data_entrada < ? AND data_saida > ?
          )
        ORDER BY q.numero LIMIT 1
    """, (categoria_id, saida, entrada)).fetchone()

    if not quarto_livre:
        conn.close()
        flash("Não há acomodações desta categoria disponíveis para o período selecionado.", "danger")
        return redirect(url_for("hospede_quartos"))

    noites = (datetime.strptime(saida, "%Y-%m-%d") - datetime.strptime(entrada, "%Y-%m-%d")).days
    valor_total = round(noites * categoria["valor_diaria"], 2)

    conn.execute("""
        INSERT INTO reservas (hospede_id, quarto_id, data_entrada, data_saida, quantidade_hospedes, status, valor_total, observacoes)
        VALUES (?, ?, ?, ?, ?, 'Confirmada', ?, ?)
    """, (
        hospede_id, quarto_livre["id"], entrada, saida, quantidade, valor_total,
        request.form.get("observacoes", "").strip()
    ))
    conn.commit()
    conn.close()
    flash("Reserva confirmada com sucesso! Estamos ansiosos para recebê-lo.", "success")
    return redirect(url_for("minhas_reservas"))

@app.route("/hospede/minhas-reservas")
@hospede_required
def minhas_reservas():
    conn = get_db()
    rows = conn.execute("""
        SELECT r.*, c.nome AS categoria, q.numero AS quarto
        FROM reservas r
        JOIN quartos q ON q.id = r.quarto_id
        JOIN categorias c ON c.id = q.categoria_id
        WHERE r.hospede_id = ?
        ORDER BY r.data_entrada DESC, r.id DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    return render_template("minhas_reservas.html", reservas=rows)

@app.route("/hospede/reservas/cancelar/<int:id>", methods=["POST"])
@hospede_required
def hospede_cancelar_reserva(id):
    conn = get_db()
    reserva = conn.execute(
        "SELECT * FROM reservas WHERE id = ? AND hospede_id = ?", (id, session["user_id"])
    ).fetchone()
    if not reserva:
        conn.close()
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("minhas_reservas"))
    if reserva["status"] in ("Finalizada", "Cancelada"):
        conn.close()
        flash("Esta reserva não pode mais ser cancelada.", "danger")
        return redirect(url_for("minhas_reservas"))
    conn.execute("UPDATE reservas SET status = 'Cancelada' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Reserva cancelada com sucesso.", "success")
    return redirect(url_for("minhas_reservas"))

@app.route("/hospede/experiencias")
@hospede_required
def hospede_experiencias():
    conn = get_db()
    rows = conn.execute("SELECT * FROM experiencias ORDER BY id").fetchall()
    conn.close()
    return render_template("hospede_experiencias.html", experiencias=rows)

@app.route("/hospede/lazer")
@hospede_required
def hospede_lazer():
    conn = get_db()
    rows = conn.execute("SELECT * FROM lazer ORDER BY ordem, id").fetchall()
    conn.close()
    return render_template("hospede_lazer.html", itens=rows)

@app.route("/hospede/contato", methods=["GET", "POST"])
@hospede_required
def hospede_contato():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO mensagens_contato (hospede_id, nome, email, assunto, mensagem)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            request.form.get("nome", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("assunto", "").strip(),
            request.form.get("mensagem", "").strip(),
        ))
        conn.commit()
        conn.close()
        flash("Mensagem enviada! Nossa equipe responderá em breve.", "success")
        return redirect(url_for("hospede_contato"))
    return render_template("hospede_contato.html")

@app.route("/hospede/perfil", methods=["GET", "POST"])
@hospede_required
def hospede_perfil():
    conn = get_db()
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "dados":
            nome = request.form.get("nome", "").strip()
            conn.execute(
                "UPDATE hospedes SET nome = ?, telefone = ?, email = ? WHERE id = ?",
                (
                    nome,
                    request.form.get("telefone", "").strip(),
                    request.form.get("email", "").strip(),
                    session["user_id"]
                )
            )
            conn.commit()
            session["user_name"] = nome
            flash("Dados atualizados com sucesso.", "success")

        elif form_type == "senha":
            atual = request.form.get("senha_atual", "")
            nova = request.form.get("nova_senha", "")
            confirmar = request.form.get("confirmar_senha", "")
            row = conn.execute("SELECT senha FROM hospedes WHERE id = ?", (session["user_id"],)).fetchone()
            if not row or row["senha"] != atual:
                flash("Senha atual incorreta.", "danger")
            elif not nova or nova != confirmar:
                flash("As novas senhas não coincidem.", "danger")
            else:
                conn.execute("UPDATE hospedes SET senha = ? WHERE id = ?", (nova, session["user_id"]))
                conn.commit()
                flash("Senha alterada com sucesso.", "success")

        conn.close()
        return redirect(url_for("hospede_perfil"))

    hospede = conn.execute("SELECT * FROM hospedes WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("hospede_perfil.html", hospede=hospede)

if __name__ == "__main__":
    init_db()
    migrate_db()
    app.run(debug=True)
