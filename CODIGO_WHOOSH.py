from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StandardAnalyzer
import os.path
from whoosh.index import create_in
from whoosh import index
import timeit
from whoosh.qparser import MultifieldParser, OrGroup
from statistics import mean
import matplotlib.pyplot as plt

esquema = Schema(index=ID(stored=True),
                 titulo=TEXT(stored=True),
                 autor=TEXT(stored=True),
                 texto_arquivo=TEXT(analyzer=StandardAnalyzer()))

if not os.path.exists('indice'):
    os.mkdir('indice')
indexador = create_in('indice', esquema)
indexador = index.open_dir('indice')


def splitar_linha_arquivo(linha_arquivo):
    linha_splitada = []
    linha_arquivo = linha_arquivo.split('.T\n')
    linha_splitada.append(linha_arquivo[0].replace('\n', '').strip())
    linha_arquivo = linha_arquivo[1].split('.A\n')
    linha_splitada.append(linha_arquivo[0].replace('\n', ''))
    linha_arquivo = linha_arquivo[1].split('.B\n')
    linha_splitada.append(linha_arquivo[0].replace('\n', ''))
    linha_arquivo = linha_arquivo[1].split('.W\n')
    linha_splitada.append(linha_arquivo[1].replace('\n', ' '))
    return linha_splitada


def indexar_arquivos(nome_arquivo, indexador):
    writer = indexador.writer()
    with open(nome_arquivo) as arquivo:
        arquivos_splitado = arquivo.read().split('.I')[1:]
    for linha in arquivos_splitado:
        linha_arquivo = splitar_linha_arquivo(linha)
        index = linha_arquivo[0]
        titulo = linha_arquivo[1]
        autor = linha_arquivo[2]
        texto_arquivo = linha_arquivo[3]
        writer.add_document(index=index,
                            titulo=titulo,
                            autor=autor,
                            texto_arquivo=texto_arquivo)
    writer.commit()


def obter_documentos_relevantes(nome_arquivo):
    relevantes = {}
    with open(nome_arquivo, 'r') as arquivo:
        linhas = arquivo.read().split('\n')
        for linha in linhas:
            linha = linha.split(' ')
            if linha[0] not in relevantes:
                relevantes[linha[0].strip()] = [linha[1].strip()]
            else:
                relevantes[linha[0].strip()].append(linha[1].strip())
    return relevantes


def buscar_arquivos(nome_arquivo, indexador, esquema):
    parser = MultifieldParser(fieldnames=['titulo', 'autor', 'texto_arquivo'],
                              schema=esquema,
                              group=OrGroup)
    resultados = {}
    with open(nome_arquivo) as arquivo:
        arquivos_splitados = arquivo.read().split('.I')[1:]
    with indexador.searcher() as buscador:
        for x, arquivo in enumerate(arquivos_splitados):
            busca = parser.parse(arquivo.split('.W\n')[1])
            resultado_busca = buscador.search(busca)
            indice = '{}'.format(x + 1)
            resultados[indice] = []
            for resultado in resultado_busca:
                resultados[indice].append(resultado.get('index').strip())
    return resultados


tempo_antes_indexacao = timeit.default_timer()
indexar_arquivos('cran.all.1400', indexador)
tempo_depois_indexacao = timeit.default_timer()

print('Tempo de indexar os arquivos: ',
      tempo_depois_indexacao - tempo_antes_indexacao)

tempo_antes_busca = timeit.default_timer()
resultados = buscar_arquivos('cran.qry', indexador, esquema)
tempo_depois_busca = timeit.default_timer()

print('Tempo de buscar os arquivos: ', tempo_depois_busca - tempo_antes_busca)

#calculando precisão e recall
documentos_relevantes = obter_documentos_relevantes('cranqrel')
precisoes = []
recalls = []
tamanho = len(documentos_relevantes)

for k in range(1, 11):
    precisoes_k = []
    recalls_k = []
    for i in range(tamanho):
        indice = '{}'.format(i + 1)
        documentos_k_relevantes = len(
            set(documentos_relevantes[indice]).intersection(
                resultados[indice][:k]))
        precisoes_k.append(documentos_k_relevantes / k)
        recalls_k.append(documentos_k_relevantes /
                         len(documentos_relevantes[indice]))
    precisoes.append(mean(precisoes_k))
    recalls.append(mean(recalls_k))

#plotando grafico precisao
plt.plot(range(1, 11), precisoes, marker='o')
plt.title('Whoosh Precisao @ k')
plt.xlabel('k')
plt.ylabel('precisao')
plt.show()

#plotando grafico recall
plt.plot(range(1, 11), recalls, marker='o')
plt.title('Whoosh Recall @ k')
plt.xlabel('k')
plt.ylabel('Recall')
plt.show()
