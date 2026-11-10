# MacroPad Studio

Aplicativo portátil para personalizar um teclado macro USB no Windows. Associa teclas e o knob a atalhos, texto, ações multimídia e camadas gerenciadas pelo aplicativo.

Baixe `MacroPadStudio.exe` e execute no Windows; não é necessário instalar Python. As configurações pessoais ficam ao lado do executável e não são versionadas.

## Como usar

1. Selecione uma tecla virtual ou um controle de giro/clique do knob.
2. Clique em **Capturar** e acione o controle físico.
3. Escolha e configure a ação; salve.

Ações de mídia: aumentar/diminuir volume, silenciar, faixa anterior/próxima, reproduzir/pausar e parar. O aplicativo oferece três camadas de software.

## Limitações

O aplicativo envia ações globais enquanto está aberto e não grava o firmware. Eventos iguais de outros teclados também podem acioná-lo. As camadas pertencem ao aplicativo; alguns knobs podem emitir eventos Consumer Control que o modo global não captura.

## Desenvolvimento

Requer Python 3 e Tkinter. Para gerar o executável no Windows, instale PyInstaller e execute:

```powershell
python -m PyInstaller --onefile --windowed --name MacroPadStudio MacroPad_Personalizador.py
```
