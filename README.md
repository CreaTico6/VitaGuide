# VitaGuide

Aplicacao desktop em Python para analise de suplementos com foco em:
- contraindicacoes
- interacoes medicamentosas
- efeitos adversos
- exportacao de relatorio em PDF

## Requisitos

- Python 3.8+ (recomendado para compatibilidade com Windows 7)
- Dependencias em requirements.txt

## Preparacao

1. Instalar dependencias:

   python -m pip install -r requirements.txt

2. Gerar dataset a partir do Excel:

   python scripts/build_dataset.py

3. Executar a aplicacao:

   python app.pyw

## Funcionalidades atuais

- Selecao multipla de suplementos
- Entrada de externos por lista pre-definida e texto livre
- Exibicao de contraindicacoes, interacoes e efeitos adversos
- Exportacao para PDF

## Build para EXE (Windows)

No Windows, apos validar o app:

1. Instalar pyinstaller

   python -m pip install pyinstaller

2. Gerar executavel

   pyinstaller --noconfirm --windowed --onefile --name VitaGuide --add-data "data/dataset.json;data" app.pyw

O executavel sera gerado na pasta dist.
