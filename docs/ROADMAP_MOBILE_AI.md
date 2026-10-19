# Roadmap mobile e IA

## APK

Uma versão Android é viável, mas o aplicativo desktop atual não deve ser empacotado sem alterações. O `pyside6-android-deploy` gera APK/AAB para aplicações PySide6; a dependência crítica deste projeto é o VTK/PyVista, que não oferece uma roda Android comum pronta para esta pilha. Compilar o VTK para Android aumentaria muito a complexidade e o tamanho do aplicativo.

A rota recomendada é compartilhar catálogo, progresso e regras de estudo, mas usar um visualizador próprio para mobile:

```text
apps/
  desktop/          # PySide6 + PyVista/VTK
  mobile/           # Capacitor + interface web 3D
packages/
  anatomy-core/     # catálogo, busca, quiz e contratos da IA
assets/
  manifests/        # nomes, FMA, regiões e relações
tools/
  model-pipeline/   # STL/VTP -> GLB com níveis de detalhe
```

O mobile pode renderizar modelos `GLB/glTF` com Three.js ou Babylon.js e ser empacotado com Capacitor. Isso mantém um único projeto Android, permite PWA no navegador e evita levar o VTK inteiro para o telefone. As malhas devem ser divididas por região e baixadas sob demanda, com dois ou três níveis de detalhe.

Arquivos 3D grandes não devem entrar no Git comum. Manter apenas manifestos e scripts no repositório; distribuir os pacotes de modelos por Releases/object storage, ou Git LFS se houver uma necessidade real de versioná-los.

## IA com maior valor didático

1. **Tutor anatômico contextual:** responde usando somente a estrutura selecionada e fontes revisadas, mostrando de onde veio cada afirmação.
2. **Quiz adaptativo:** pede para localizar músculos no 3D, identifica erros recorrentes e agenda revisões espaçadas.
3. **Modo oral:** recebe perguntas por voz e explica em nível básico, universitário ou clínico.
4. **Comparador funcional:** relaciona origem, inserção, inervação, ação e músculos agonistas/antagonistas.
5. **Roteiro automático de estudo:** monta sessões por região e atualiza a dificuldade a partir do desempenho.
6. **Busca semântica:** entende consultas como “músculos que fazem dorsiflexão” e destaca o conjunto correspondente.

O primeiro incremento recomendado combina tutor contextual, quiz de identificação e revisão espaçada. A IA não deve inventar geometria nem substituir o catálogo: respostas precisam ser ancoradas em conteúdo anatômico curado e o produto deve manter o aviso de uso educacional, não diagnóstico.

É possível oferecer dois modos: modelo local por Ollama para privacidade/offline e API remota para respostas de maior qualidade. O contrato de IA deve ficar atrás de uma interface única para que o app desktop e o mobile reutilizem a mesma lógica.

## Referências técnicas

- [Qt for Python: implantação no Android](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-android-deploy.html)
- [VTK: compilação para dispositivos móveis](https://docs.vtk.org/en/latest/advanced/build_for_mobile.html)
- [Capacitor: instalação e projetos Android/iOS](https://capacitorjs.com/docs/getting-started)
- [Three.js: carregamento de modelos glTF](https://threejs.org/docs/pages/GLTFLoader)
