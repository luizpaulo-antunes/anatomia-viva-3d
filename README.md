# Anatomia Viva 3D

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença MIT](https://img.shields.io/badge/código-MIT-2ea44f)](LICENSE)
[![Atlas](https://img.shields.io/badge/atlas-Z--Anatomy%202026.09-b3272d)](#cobertura-anatômica)
[![Windows](https://img.shields.io/badge/Windows-instalador-0078D4?logo=windows)](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases/latest/download/AnatomiaViva3D-Windows.zip)

Atlas anatômico 3D local e interativo para estudo. Permite explorar estruturas, pesquisar em português ou latim, selecionar diretamente no corpo, isolar sistemas e consultar informações e proveniência sem depender de uma conexão durante o uso.

> [!IMPORTANT]
> Este é um recurso educacional. Não deve ser usado para diagnóstico, planejamento clínico ou como única fonte de informação médica.

## Download para Windows

[**Baixar o instalador do Anatomia Viva 3D (.zip)**](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases/latest/download/AnatomiaViva3D-Windows.zip)

Extraia o ZIP e execute `AnatomiaViva3D-Setup-<versão>.exe`. Python e a biblioteca anatômica já acompanham o instalador.

## O que há no aplicativo

- rotação, zoom, deslocamento e vistas anatômicas predefinidas;
- **2.847 malhas selecionáveis** entre os perfis, renderizadas de forma otimizada em um único conjunto composto;
- seletor de perfil reprodutivo **Masculino, Feminino ou Ambos**, sem perder a posição da câmera;
- ossos, articulações/ligamentos/fáscias, músculos, cardiovascular, linfático, nervoso e vísceras;
- seleção pelo modelo ou pela árvore, com enquadramento anatômico regional estável;
- estrutura selecionada sólida e contornada, com somente os ossos próximos como referência anatômica discreta;
- pesquisa por nome em português, termo latino, sistema e região;
- isolamento, ocultação, opacidade e filtros por sistema;
- nomes em português associados à Terminologia Anatomica 2 quando disponíveis;
- descrições, funções, classificações, regiões e lateralidade sempre exibidas em português;
- fonte, revisão, licença e identificador TA2 exibidos por estrutura;
- relatório de cobertura e verificação SHA-256 de todos os arquivos baixados;
- funcionamento offline depois da instalação;
- modelo BodyParts3D anterior preservado somente como fallback de compatibilidade.

## Cobertura anatômica

A biblioteca atual reúne **2.847 estruturas selecionáveis entre os perfis**, com nomes em português e latim, sínteses didáticas em português e informações sobre a origem dos dados. O perfil masculino mantém as 2.827 malhas do Z-Anatomy; o feminino oculta as 18 estruturas reprodutivas masculinas e acrescenta 20 referências femininas do Human Reference Atlas. As definições em inglês das fontes não são mostradas como conteúdo de estudo.

O seletor **Perfil reprodutivo** fica na barra superior. Estruturas comuns permanecem no lugar e somente a anatomia específica é alternada; **Ambos (comparar)** exibe os dois conjuntos. A referência HRA inclui útero e colo, ovários, tubas, vagina, suportes ligamentares e vasos uterinos, todos com descrição e função em português. Trata-se de um complemento reprodutivo/pélvico alinhado ao corpo principal — não de um modelo feminino completo de todas as diferenças sexuais do corpo.

| Sistema | Malhas selecionáveis |
| --- | ---: |
| Esquelético | 277 |
| Articulações, ligamentos e fáscias | 358 |
| Muscular | 669 |
| Cardiovascular | 680 |
| Linfático | 158 |
| Nervoso | 580 |
| Órgãos e vísceras | 125 |
| **Total entre os perfis** | **2.847** |

Consulte [fontes e versões dos dados](docs/FONTES_E_COBERTURA.md) e [licenças de terceiros](THIRD_PARTY_LICENSES.md).

## Atualização dos dados

O instalador inclui a revisão estável. No aplicativo, use **Dados → Instalar/atualizar atlas moderno…**. O download tem aproximadamente 20 MB, é salvo no perfil do usuário e cada arquivo é validado antes da ativação. Uma falha não substitui a biblioteca válida existente.

Pelo terminal:

```bash
anatomia-dados instalar
anatomia-dados verificar
anatomia-dados status
anatomia-dados relatorio
```

O relatório resume a biblioteca instalada e confirma a integridade dos arquivos.

## Executar pelo código-fonte

Requisitos: Python 3.10 ou superior e computador com suporte a OpenGL.

### macOS ou Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-dados instalar
anatomia-3d
```

### Windows — PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-dados instalar
anatomia-3d
```

O primeiro comando de dados baixa a revisão fixada para `data/zanatomy`. Os arquivos grandes ficam fora do histórico do Git.

## Controles

| Ação | Controle |
| --- | --- |
| Girar | arrastar com o botão esquerdo |
| Zoom | roda do mouse, teclas **+ / −** ou botões da barra superior |
| Deslocar câmera | arrastar com o botão direito |
| Selecionar | clicar no modelo ou na lista |
| Mostrar/ocultar | caixa ao lado da estrutura |
| Trocar anatomia reprodutiva | seletor **Perfil reprodutivo** na barra superior |
| Reenquadrar seleção | tecla **F** ou botão **Reenquadrar** |
| Restaurar contexto | **Exibir todas as estruturas** |

Ao selecionar uma estrutura, a câmera enquadra uma região coerente — por exemplo, a cabeça ao selecionar um osso da face — e mantém um campo de visão mínimo para evitar aproximações exageradas em peças pequenas. A estrutura fica sólida, suavizada e com contorno claro. Para evitar o efeito confuso de muitas transparências sobrepostas, somente os ossos próximos permanecem como referência discreta; **Isolar** remove também esse contexto. Ao trocar entre Ossos, Músculos, Vasos, Nervos ou Órgãos, o aplicativo preserva a câmera e mostra o novo sistema somente no volume 3D atualmente visível. O botão **Exibir todas as estruturas** retorna ao corpo inteiro.

### Desempenho em computadores básicos

No Windows com até 12 GB de RAM, o aplicativo ativa automaticamente o **modo leve**. Ele usa um cache 3D pré-otimizado, reduz o atlas de aproximadamente 10,4 para 3,7 milhões de triângulos e desliga a suavização de tela mais cara, sem remover estruturas ou informações.

Para forçar um perfil ao executar pelo código-fonte, defina `ANATOMIA_3D_QUALIDADE=leve` ou `ANATOMIA_3D_QUALIDADE=detalhada`. O instalador para Windows já inclui o cache leve; para prepará-lo manualmente, execute `anatomia-dados otimizar`.

## Testes

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Os testes cobrem catálogo, perfis reprodutivos masculino/feminino, referência HRA, conteúdo didático em português, perfil para PCs com pouca memória, redução geométrica, modelos legados, atualização segura, foco de câmera, parser GLB, descompressão Draco, transformações 3D e leitura da TA2.

## Organização

```text
src/anatomia_app/
├── atlas.py             # contrato de um atlas versionado
├── zanatomy.py          # download, hashes, TA2, GLB/Draco e cobertura
├── female_reference.py  # complemento reprodutivo feminino HRA
├── main_window.py       # interface, seleção e renderização composta
├── catalog.py           # catálogo didático e fallback legado
├── bodyparts3d.py       # importador legado, não usado como padrão
└── geometry.py          # modo demonstrativo sem downloads

packaging/windows/       # PyInstaller, Inno Setup e build do ZIP
tools/                   # pacote de conteúdo e utilitários
tests/                   # testes automatizados
```

## Instalador do Windows

O pipeline gera:

```text
AnatomiaViva3D-Windows.zip
└── AnatomiaViva3D-Setup-<versão>.exe
```

O build baixa somente a revisão fixada, verifica hashes, executa os testes e inclui o atlas no instalador. Consulte [Instalador do Windows](docs/INSTALADOR_WINDOWS.md).

## Licenças e contribuição

O código é MIT. As malhas, a terminologia e as descrições mantêm suas próprias licenças; algumas estruturas têm restrição não comercial. Veja [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) antes de redistribuir dados.

Correções anatômicas são bem-vindas. Ao abrir uma issue, informe a estrutura, o sistema operacional, a revisão exibida em **Dados → Fonte, cobertura e licenças** e, se possível, uma captura de tela.
