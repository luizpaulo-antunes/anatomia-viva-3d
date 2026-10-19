# Instalador do Windows

O pacote final é `AnatomiaViva3D-Windows-<versão>.zip`. Dentro dele há um único instalador `AnatomiaViva3D-Setup-<versão>.exe`.

O Setup instala por usuário, sem exigir privilégios de administrador, cria atalhos e registra um desinstalador. Python, PySide6, PyVista e VTK são incluídos pelo PyInstaller. O cache anatômico otimizado com as 443 estruturas atuais também é incluído, portanto o atlas detalhado funciona offline sem baixar os STL brutos.

## Atualizações após a instalação

O menu **Dados → Atualizar biblioteca anatômica…** consulta `anatomia-content.json` na Release mais recente. Se houver um conteúdo mais novo, o programa:

1. informa a versão, o número de estruturas e o tamanho;
2. baixa `AnatomiaViva3D-Content-<versão>.zip`;
3. confere tamanho e SHA-256;
4. valida se todas as malhas esperadas estão presentes;
5. ativa o pacote no perfil do usuário, preservando os dados embutidos como fallback.

No Windows, os pacotes ficam em `%LOCALAPPDATA%\AnatomiaViva3D\content`. Atualizações de geometria e fichas compatíveis podem ser entregues dessa forma. Quando uma versão introduzir recursos ou tipos de estrutura que o código antigo não conhece, ela também exigirá uma atualização do aplicativo.

## Build automático no GitHub

Depois que o código for enviado ao GitHub, abra **Actions → Build Windows installer → Run workflow**. O ZIP ficará disponível como Artifact.

Ao criar e enviar uma tag como `v0.3.0`, o mesmo workflow cria ou atualiza uma GitHub Release e anexa o ZIP automaticamente.

## Build em um computador Windows

Requisitos:

- Python 3.12 de 64 bits;
- Inno Setup 6 ou 7;
- PowerShell 5.1 ou mais recente;
- conexão à internet na primeira montagem das malhas.

No PowerShell, na raiz do projeto:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\packaging\windows\build.ps1
```

O script instala as dependências, executa os testes, obtém e otimiza as malhas, gera o aplicativo autocontido, compila o Setup e cria em `release\`:

- `AnatomiaViva3D-Windows-<versão>.zip`;
- `AnatomiaViva3D-Content-<versão>.zip`;
- `anatomia-content.json`.

## Publicação

Os ZIPs e o manifesto devem ser publicados em **GitHub Releases**, não commitados no histórico do Git. `dist/`, `build/` e `release/` são produtos reproduzíveis e permanecem ignorados.
