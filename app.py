from flask import Flask, jsonify, request, abort
import json
import os
import random

# A sua lista de versões disponíveis, para validação.
VERSOES_SUPORTADAS = ["ACF", "ARA", "ARC", "AS21", "JFAA", "KJA", "KJF", "NAA", "NBV", "NTLH", "NVT", "NVI", "TB"]

app = Flask(__name__)

# --- Funções auxiliares ---

# Carrega os dados de uma versão inteira, otimizando o acesso.
def carregar_dados_versao(versao):
    versao_lower = versao.lower()
    caminho_arquivo = f'versoes/{versao_lower}.json'
    try:
        if not os.path.exists(caminho_arquivo):
            return None
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            # Verifica se os dados são uma lista e os converte para um dicionário de livros
            if isinstance(dados, list):
                # Usa um dicionário de compreensão para transformar a lista em um dicionário,
                # agora usando a chave "abbrev" do seu JSON.
                dados_dict = {
                    get_livro_completo(item.get("abbrev", "")): item for item in dados if item.get("abbrev")
                }
                return dados_dict
            return dados
    except Exception as e:
        print(f"Erro ao carregar dados da versão {versao}: {e}")
        return None

# Mapeia as abreviações dos livros (ex: gn) para os nomes completos (ex: genesis)
def get_livro_completo(abreviacao_ou_nome):
    livros_map = {
        "gn": "genesis", "ex": "exodo", "lv": "levitico", "nm": "numeros", "dt": "deuteronomio",
        "js": "josue", "jz": "juizes", "rt": "rute", "1sm": "1samuel", "2sm": "2samuel",
        "1rs": "1reis", "2rs": "2reis", "1cr": "1cronicas", "2cr": "2cronicas", "ed": "esdras",
        "ne": "neemias", "et": "ester", "jo": "jo", "sl": "salmos", "pv": "proverbios",
        "ec": "eclesiastes", "ct": "cantares", "is": "isaias", "jr": "jeremias", "lm": "lamentacoes",
        "ez": "ezequiel", "dn": "daniel", "os": "oseias", "jl": "joel", "am": "amos",
        "ob": "obadias", "jn": "jonas", "mq": "miqueias", "na": "naum", "hc": "habacuque",
        "sf": "sofonias", "ag": "ageu", "zc": "zacarias", "ml": "malaquias", "mt": "mateus",
        "mc": "marcos", "lc": "lucas", "jo": "joao", "at": "atos", "rm": "romanos",
        "1co": "1corintios", "2co": "2corintios", "gl": "galatas", "ef": "efesios", "fp": "filipenses",
        "cl": "colossenses", "1ts": "1tessalonicenses", "2ts": "2tessalonicenses", "1tm": "1timoteo",
        "2tm": "2timoteo", "tt": "tito", "fm": "filemom", "hb": "hebreus", "tg": "tiago",
        "1pe": "1pedro", "2pe": "2pedro", "1jo": "1joao", "2jo": "2joao", "3jo": "3joao",
        "jd": "judas", "ap": "apocalipse",
    }
    nome_padronizado = abreviacao_ou_nome.lower().replace(" ", "").replace(".", "")
    return livros_map.get(nome_padronizado, nome_padronizado)


# Um "dicionário" (hash map) para armazenar os dados em memória.
livros_carregados = {}

# --- Rotas da API ---

# NOVO Endpoint: GET /books/with_chapters
# Retorna uma lista de livros com a quantidade de capítulos de cada um.
@app.route('/books/with_chapters', methods=['GET'])
def get_books_with_chapters():
    versao_padrao = "ARA"
    if versao_padrao not in livros_carregados:
        dados_da_versao = carregar_dados_versao(versao_padrao)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{versao_padrao}' não encontrados."}), 404
        livros_carregados[versao_padrao] = dados_da_versao
    
    books_with_chapters = []
    for livro_data in livros_carregados[versao_padrao].values():
        num_capitulos = len(livro_data.get("chapters", []))
        books_with_chapters.append({
            "name": livro_data.get("name", "Nome Desconhecido"),
            "chapter_count": num_capitulos
        })

    return jsonify({"books": books_with_chapters})


# Endpoint: GET /books/count
# Retorna o número total de livros.
@app.route('/books/count', methods=['GET'])
def get_books_count():
    versao_padrao = "ARA"
    if versao_padrao not in livros_carregados:
        dados_da_versao = carregar_dados_versao(versao_padrao)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{versao_padrao}' não encontrados."}), 404
        livros_carregados[versao_padrao] = dados_da_versao
    
    total_livros = len(livros_carregados[versao_padrao])
    return jsonify({"total_books": total_livros})

# Endpoint: GET /chapters/<livro>/count
# Retorna o número de capítulos de um livro específico.
@app.route('/chapters/<string:book>/count', methods=['GET'])
def get_chapters_count(book):
    versao_padrao = "ARA"
    if versao_padrao not in livros_carregados:
        dados_da_versao = carregar_dados_versao(versao_padrao)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{versao_padrao}' não encontrados."}), 404
        livros_carregados[versao_padrao] = dados_da_versao

    livro_nome = get_livro_completo(book)
    dados_do_livro = livros_carregados[versao_padrao].get(livro_nome)
    
    if not dados_do_livro:
        return jsonify({"erro": f"Livro '{book}' não encontrado na versão {versao_padrao}."}), 404

    try:
        capitulos = dados_do_livro.get("chapters", [])
        num_capitulos = len(capitulos)
    except Exception:
        num_capitulos = 0

    return jsonify({"book": livro_nome.title(), "chapter_count": num_capitulos})


# Endpoint: GET /books
# Retorna uma lista de todos os livros disponíveis
@app.route('/books', methods=['GET'])
def get_books():
    # Carrega uma versão padrão para obter a lista de livros
    versao_padrao = "ARA"
    if versao_padrao not in livros_carregados:
        dados_da_versao = carregar_dados_versao(versao_padrao)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{versao_padrao}' não encontrados."}), 404
        livros_carregados[versao_padrao] = dados_da_versao
    
    livros = []
    # Itera sobre os dados para obter o nome completo de cada livro e sua abreviação
    for livro_data in livros_carregados[versao_padrao].values():
        livros.append({
            "name": livro_data.get("name", "Nome Desconhecido"),
            "abbrev": livro_data.get("abbrev", "Abrev Desconhecida"),
            "group": livro_data.get("group", "Grupo Desconhecido")
        })

    return jsonify({"books": livros})

# Endpoint: GET /verses (URL com parâmetros de consulta)
# Parâmetros: version, book, chapter
@app.route('/verses', methods=['GET'])
def get_verses():
    version = request.args.get('version', 'ara').upper()
    book_param = request.args.get('book')
    chapter_param = request.args.get('chapter')

    # Validação dos parâmetros obrigatórios
    if not all([book_param, chapter_param]):
        abort(400, "Parâmetros 'book' e 'chapter' são obrigatórios.")
    
    # Validação da versão
    if version not in VERSOES_SUPORTADAS:
        return jsonify({"erro": f"Versão '{version}' não suportada."}), 400

    # Carrega os dados da versão
    if version not in livros_carregados:
        dados_da_versao = carregar_dados_versao(version)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{version}' não encontrados."}), 404
        livros_carregados[version] = dados_da_versao

    livro_nome = get_livro_completo(book_param)
    dados_do_livro = livros_carregados[version].get(livro_nome)
    
    if not dados_do_livro:
        return jsonify({"erro": f"Livro '{book_param}' não encontrado na versão {version}."}), 404

    try:
        capitulo_str = str(int(chapter_param))
        # Agora acessamos o array de capítulos, não um dicionário de capítulos.
        capitulos_array = dados_do_livro.get("chapters", [])
        
        # O index da lista é o capítulo - 1.
        if int(capitulo_str) > 0 and int(capitulo_str) <= len(capitulos_array):
            versiculos = capitulos_array[int(capitulo_str) - 1]
        else:
            versiculos = None
        
        if not versiculos:
            return jsonify({"erro": f"Capítulo '{chapter_param}' não encontrado para o livro '{livro_nome}'."}), 404
    except ValueError:
        return jsonify({"erro": f"O parâmetro 'chapter' deve ser um número inteiro."}), 400

    return jsonify({
        "version": version,
        "book": livro_nome.title(),
        "chapter": int(capitulo_str),
        "verses": versiculos
    })

# Endpoint: GET /verses (URL simplificada com a rota)
# Parâmetros: version, book, chapter na URL
@app.route('/verses/<string:version>/<string:book>/<int:chapter>', methods=['GET'])
def get_verses_simple(version, book, chapter):
    version = version.upper()

    # Validação da versão
    if version not in VERSOES_SUPORTADAS:
        return jsonify({"erro": f"Versão '{version}' não suportada."}), 400

    # Carrega os dados da versão
    if version not in livros_carregados:
        dados_da_versao = carregar_dados_versao(version)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{version}' não encontrados."}), 404
        livros_carregados[version] = dados_da_versao

    livro_nome = get_livro_completo(book)
    dados_do_livro = livros_carregados[version].get(livro_nome)
    
    if not dados_do_livro:
        return jsonify({"erro": f"Livro '{book}' não encontrado na versão {version}."}), 404

    try:
        # Acessamos o array de capítulos, não um dicionário de capítulos.
        capitulos_array = dados_do_livro.get("chapters", [])
        
        # O index da lista é o capítulo - 1.
        if chapter > 0 and chapter <= len(capitulos_array):
            versiculos = capitulos_array[chapter - 1]
        else:
            versiculos = None
        
        if not versiculos:
            return jsonify({"erro": f"Capítulo '{chapter}' não encontrado para o livro '{livro_nome}'."}), 404
    except ValueError:
        return jsonify({"erro": f"O parâmetro 'chapter' deve ser um número inteiro."}), 400

    return jsonify({
        "version": version,
        "book": livro_nome.title(),
        "chapter": chapter,
        "verses": versiculos
    })


# Endpoint: GET /search
# Parâmetros: theme, version (opcional)
@app.route('/search/<string:theme>', methods=['GET'])
def search_theme(theme):
    version = request.args.get('version', 'ara').upper()
    
    if not theme:
        abort(400, "Parâmetro 'theme' é obrigatório.")
    
    if version not in VERSOES_SUPORTADAS:
        return jsonify({"erro": f"Versão '{version}' não suportada."}), 400

    if version not in livros_carregados:
        dados_da_versao = carregar_dados_versao(version)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{version}' não encontrados."}), 404
        livros_carregados[version] = dados_da_versao

    dados_da_versao = livros_carregados[version]
    resultados = []
    tema_lower = theme.lower()

    for book_name, book_data in dados_da_versao.items():
        if 'chapters' in book_data:
            for chapter_index, verses in enumerate(book_data['chapters']):
                chapter_num = chapter_index + 1
                for verse_index, verse_text in enumerate(verses):
                    verse_num = verse_index + 1
                    if tema_lower in verse_text.lower():
                        resultados.append({
                            "version": version,
                            "book": book_name.title(),
                            "chapter": chapter_num,
                            "verse_number": verse_num,
                            "text": verse_text
                        })

    return jsonify({"results": resultados, "count": len(resultados)})

# Endpoint: GET /random
# Parâmetros: version (opcional)
@app.route('/random', methods=['GET'])
def get_random_verse():
    version = request.args.get('version', 'ara').upper()

    if version not in VERSOES_SUPORTADAS:
        return jsonify({"erro": f"Versão '{version}' não suportada."}), 400

    if version not in livros_carregados:
        dados_da_versao = carregar_dados_versao(version)
        if dados_da_versao is None:
            return jsonify({"erro": f"Dados da versão '{version}' não encontrados."}), 404
        livros_carregados[version] = dados_da_versao

    dados_da_versao = livros_carregados[version]
    
    livros_com_capitulos = [k for k, v in dados_da_versao.items() if 'chapters' in v and v['chapters']]
    if not livros_com_capitulos:
        return jsonify({"erro": "Não há dados de livros com capítulos para esta versão."}), 404

    livro_aleatorio_nome = random.choice(livros_com_capitulos)
    dados_do_livro = dados_da_versao[livro_aleatorio_nome]
    
    capitulos = dados_do_livro['chapters']
    if not capitulos:
        return jsonify({"erro": "O livro selecionado não possui capítulos."}), 404
    
    capitulo_aleatorio_index = random.choice(range(len(capitulos)))
    versiculos_do_capitulo = capitulos[capitulo_aleatorio_index]
    capitulo_aleatorio_num = capitulo_aleatorio_index + 1

    if not versiculos_do_capitulo:
        return jsonify({"erro": "O capítulo selecionado não possui versículos."}), 404

    versiculo_aleatorio_texto = random.choice(versiculos_do_capitulo)
    versiculo_aleatorio_num = versiculos_do_capitulo.index(versiculo_aleatorio_texto) + 1

    return jsonify({
        "version": version,
        "book": livro_aleatorio_nome.title(),
        "chapter": capitulo_aleatorio_num,
        "verse_number": versiculo_aleatorio_num,
        "text": versiculo_aleatorio_texto
    })

# Rota para a página inicial (pode ser útil para testar)
@app.route('/')
def home():
    return "Bem-vindo à API da Bíblia!"

if __name__ == '__main__':
    # Habilitar CORS para permitir requisições de diferentes origens.
    from flask_cors import CORS
    CORS(app)
    
    # Inicia o servidor em modo de depuração.
    app.run(debug=True)
