### Um bot do Discord para editar e criar vídeos, imagens, GIFs e muito mais!

## informações técnicas gerais sobre o bot

- usa discord.py 2
- usa libvips para legendagem
- usa FFmpeg para processamento de mídia

## auto-hospedagem com docker

### para instalar

Tudo o que você precisa para instalar você mesmo é [Docker Desktop](https://docs.docker.com/get-docker/)

até o momento, uma cópia do docker de trabalho do Gifmaker ocupa ~ 3,46 GB. se isso é uma preocupação e você está usandoalguns dos
bibliotecas apt MediaForge faz, veja [auto-hospedar nativamente](#to-self-host-natively)

depois de instalado, execute esses comandos no terminal de sua escolha.

```shell
docker build -t tzrico/gifmaker https://github.com/Tzrico/gifmaker.git
docker run -it --cap-add SYS_NICE --shm-size 8G --name gifmaker tzrico/gifmaker
```

no linux, pode ser necessário executar o docker com `sudo`

substitua `8G` por quanta RAM livre seu sistema tem que você gostaria de fornecer ao MediaForge (em gigabytes). No menos `1G`
é sugerido. Tornar isso muito pequeno pode fazer com que os comandos falhem devido ao espaço insuficiente, pois o `/dev/shm` na memória
sistema de arquivos é, por padrão, o único diretório temporário do MediaForge. Substitua a opção `override_temp_dir` em`config.py`
se você não puder alocar memória suficiente.

se a instalação for bem-sucedida, você deverá ser solicitado com algumas opções. você precisará selecionar "Editar configuração". Isso vai
abra um editor de texto em seu terminal. as 2 definições de configuração necessárias para alterar a funcionalidade adequada são as
fichas de discórdia e tenor. certifique-se de não adicionar ou remover aspas. pressione `CTRL+S` para salvar e `CTRL+X` para sair.

se você não quiser usar o editor de texto embutido, você pode [obter a configuração de exemplo do GitHub](config.example.py), segure
pressione `CTRL+K` para limpar o arquivo e use `CTRL+V` para colar sua configuração.

### para ligar o bot

execute `docker ps -a` em seu terminal para ver a imagem do docker criada. seu contêiner deve ter 12 caracteres"ID",
que você precisará para executá-lo.

execute no seu terminal favorito:

```shell
docker start -ia gifmaker
```

### parar

matar a janela do terminal/`CTRL+C` não matará o bot, porque o docker é executado em segundo plano.

para matar o bot, corra

```shell
docker stop gifmaker
```

### para limitar o consumo de recursos

como o docker é muito conteinerizado, você pode facilmente limitar a quantidade de recursos que pode consumir.

o comando principal para fazer isso é [`docker update`](https://docs.docker.com/engine/reference/commandline/update/#usage),
embora a maioria desses argumentos possa ser passada literalmente para `docker run` durante a configuração.

as opções mais úteis são `--memory` and `--cpus`.

for example, this is (as of writing) what the official MediaForge bot uses:

```shell
docker update --memory 9000M --memory-swap -1 --cpus "3.9" mediaforge
```

- `--memory 9000M`: isso limita a 9 gb (9000 mb) de memória física
- `--memory-swap -1`: isso permite que ele use tanta memória de troca quanto quiser (a memória de troca é temporariamentearmazenar memória
  no disco)
- `--cpus "3.9"`: o servidor host tem 4 núcleos, então isso permite que ele use "3,9"/4 (97,5%) do tempo de CPU do PC.

### Modo automático

isso é projetado para funcionar com provedores de hospedagem onde o controle de terminal não é possível. Existem 3 argumentos para isso
modo que pode ser definido como
docker [construir argumentos](https://docs.docker.com/engine/reference/commandline/build/#set-build-time-variables---build-arg)
or [variáveis ​​ambientais](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file)
.
`AUTOMODE`: definido como "ON" para habilitar o modo automático
`AUTOUPDATE`: definido como "ON" para atualizar o código e os pacotes a cada execução
`CONFIG`: versão codificada em base64 do seu arquivo de configuração.

#### para codificar base 64

##### no linux:

- `base64 config.py` prints the output to terminal
- `base64 config.py > config.txt` writes the output to `config.txt`

##### com python:

```python
import base64

with open("config.py", "rb") as f:
    out = base64.b64encode(f.read())
print(out)  # escrever no terminal
# gravar no arquivo
with open("config.txt", "wb+") as f:
    f.write(out)
```

## auto-hospedar nativamente

O MediaForge é um aplicativo complexo e instalar manualmente todas as dependências é uma dor de cabeça. para quase todos os usos
casos, [a distribuição do docker](#self-host-with-docker) é muito melhor.

### summary

certifique-se de que seu sistema operacional é um dos [sistemas operacionais suportados](#supported-oses), então instale o [bibliotecas python](#python-libraries)
e a [bibliotecas não-python](#non-python-libraries), configurar o [config](#config), and [run](#to-run)

### sistemas operacionais suportados

construído e testado em windows 10/11 e debian 10/buster (dentro do docker). esses 2 sistemas operacionais (e seus sucessores)will
continuam a ser oficialmente apoiados.

_provavelmente_ funcionará em macos e outras distribuições linux/unix se as bibliotecas abaixo estiverem disponíveis, mas sãonão testado e
sem suporte. apenas substitua `apt-get` pelo gerenciador de pacotes preferido do seu sistema ([`brew`](https://brew.sh/) for macos)

no Windows, os emojis coloridos não funcionam. não faço ideia do porquê, apenas é um bug do windows pango.

### python libraries

- Este projeto usa [`poetry`](https://python-poetry.org/), run `poetry install` to install the required dependências.
    - instalar poesia com `pip install poetry`
    - parte de [`pyvips`](https://pypi.org/project/pyvips/) é construído a partir da fonte na instalação.
        - no Windows, isso exigirá o compilador MSVC, que é um componente opcional
          de [Visual Studio](https://visualstudio.microsoft.com/downloads/)
        - no Linux, isso exigirá [`gcc`](https://packages.ubuntu.com/bionic/gcc), instalável
          por `sudo apt-get install gcc`

### bibliotecas não-python

o bot usa muitos programas CLI externos para processamento de mídia.

- FFmpeg - não incluído, mas [facilmente instalável em windows e linux](https://ffmpeg.org/download.html)
    - **Se estiver instalando no Linux, certifique-se de que a versão do ffmpeg >= 5**
- libvips -instalável no linux com `sudo apt-get install libvips-dev`
  . [instruções do windows aqui](https://www.libvips.org/install.html#installing-the-windows-binary)
- ImageMagick - **não incluso** mas [para download aqui](https://imagemagick.org/script/download.php)
- TTS
    - no linux, isso usa [`mimic`](https://github.com/MycroftAI/mimic1). um binário pré-compilado está incluído.
        - as vozes masculina e feminina são baixadas do repositório do imitador na inicialização do bot, se não forem detectadas. Se você quiser
          para baixar novamente por algum motivo, exclua os 2 arquivos que terminam em `.flitefox` in `tts/`
    - no Windows, [`powershell`](https://aka.ms/powershell) é usado para
      acessar [TTS nativo do Windows](https://docs.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis.speechsynthesizer)
      . Ambos estão incluídos nas versões modernas do Windows, mas certifique-se de que o powershell esteja no caminho do sistema.
    - a voz "retro" usa [sam-cli](https://github.com/HexCodeFFF/sam-cli). está incluído, mas
      requer [node.js](https://nodejs.org/) para ser instalado e adicionado ao caminho do sistema
        - tenho certeza de que os instaladores do Windows e do Linux o adicionam ao caminho na instalação, mas não custa verificar

### configuração

- crie uma cópia de [`config.example.py`](config.example.py) e nomeie-a `config.py`.
- insira/altere as configurações apropriadas, como o token da API do Discord. certifique-se de não adicionar ou remover aspas.
- as 2 configurações necessárias para alterar a funcionalidade adequada são os tokens de discórdia e tenor.

### python

- desenvolvido e testado em python 3.11. use essa ou uma versão posterior compatível

### para ligar o bot

- depois de configurar todas as bibliotecas, basta executar o programa com `poetry run python src/main.py` (
  ou `poetry run python3.11 src/main.py` ou qualquer que seja o nome do seu python). certifique-se de que ele pode ler e escrevera
  diretório
  reside e também acessa/executa todas as bibliotecas mencionadas
    - se a poesia não estiver instalada na versão correta do python, execute `<yourpython> -m pip` em vez de pip
      and `<yourpython> -m poetry` instead of `poetry`
- encerre o bot executando o comando `shutdown`, isso _provavelmente_ fechará melhor do que um encerramento

## coisas legais

[termos de serviço](media/external/terms_of_service.md)

[política de Privacidade](media/external/privacy_policy.md)