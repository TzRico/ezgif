# COPIE ESTE ARQUIVO EM UM ARQUIVO CHAMADO config.py E MUDE OS VALORES CONFORME NECESSÁRIO.
# token de bot da API de discórdia https://discord.com/developers/applications
bot_token = "TOKEN"
# tenor API key https://developers.google.com/tenor/guides/quickstart#setup
tenor_key = "CHAVE"
# BotBlock tokens. see https://pypi.org/project/discordlists.py/
bot_list_data = None
# bot_list_data = {
#         "examplebotlist.com": {
#             "token": "exampletoken"
#         },
# }
# número de comandos que podem ser processados ​​ao mesmo tempo. definido como Nenhum para usar automaticamente a contagem de núcleos da CPU do SO
workers = None
# especifique manualmente tempdir em vez de usar o padrão do sistema operacional
# temp dir padrão para /dev/shm (na memória) se disponível e esta variável é None
override_temp_dir = None
# NOTICE é recomendado, INFO imprime mais informações sobre o que o bot está fazendo, WARNING imprime apenas erros.
log_level = "NOTICE"
# quantidade de segundos de tempo de espera por comandos de usuário. definido como 0 para desativar o cooldown
cooldown = 3
# altura/largura mínima em que a mídia será dimensionada se estiver abaixo
min_size = 100
# altura/largura máxima para a qual a mídia será reduzida se estiver acima
max_size = 2000
# tamanho máximo, em bytes, para download. Vejo https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Length
max_file_size = 25_000_000
# tamanho máximo de arquivo, em bytes, que um arquivo pode ter. se o arquivo resultante for maior que isso, o mediaforge fornece instantaneamente
# up e não tenta carregar nem redimensionar o arquivo.
way_too_big_size = 100_000_000
# o texto a ser usado para mensagens diferentes, pode ser emojis personalizados ou qualquer texto
emojis = {
    "x": "<:xmark:803792052932444180>",
    "warning": "<:wmark:1059038815529992242>",
    "question": "<:qmark:803791399615070249>",
    "exclamation_question": "<:eqmark:1059039044954243162>",
    "2exclamation": "<:eemark:1059039133340815420>",
    "working": "<a:ezgif:1059282779378024569>",
    "clock": "<:clockmark:1059039207869395025>",
    "one": "<:one:1059039312378863616>",
    "two": "<:two:1059039470848065587>",
    "three": "<:three:826643438723923968>",
    "resize": "<:resize:1059039611961217116>",
    "check": "<:check:826643438652489778>"
}
# até 25 dicas que podem ser exibidas ao usar $ajuda tips. digite \n para uma nova linha
tips = {
    "Media Searching": "O Ezgif procura automaticamente por qualquer mídia em um canal. Responder a uma mensagem com o "
                       "comando para pesquisar essa mensagem primeiro.",
    "File Formats": "O Ezgif oferece suporte a formatos de imagem estática como PNG, formatos de imagem animada como GIF e vídeo "
                    "formatos como MP4.",
    "Self-Hosting": "Ezgif é completamente open source e qualquer um pode hospedar um clone "
                    "themself!\nhttps://github.com/Tzrico/ezgif "
}
# https://www.reddit.com/r/discordapp/comments/aflp3p/the_truth_about_discord_file_upload_limits/
# limite de upload configurado, em bytes, para arquivos.
# não mude isso a menos que você tenha um bom motivo para isso. eu não tenho tratamento de erros para arquivos excessivamente grandes
file_upload_limit = 8_388_119
# isso se aplica a todos os comandos. se algum argumento de string contiver qualquer uma dessas palavras, o comando será instantaneamente
# falhou. isso tem como objetivo bloquear linguagem odiosa como calúnias. não diferencia maiúsculas de minúsculas.
# está na configuração, então não preciso enviar calúnias para o github...
blocked_words = []
# nome do arquivo do banco de dados sqlite3. atualmente usado apenas para armazenar prefixos específicos do servidor.
db_filename = "database.db"
# default prefix for commands
default_command_prefix = "ez!"
# este url receberá uma solicitação periódica. isso é projetado para ser usado com um serviço de monitoramento de tempo de atividade
heartbeaturl = None
# com que frequência (em segundos) solicitar o url de pulsação
heartbeatfrequency = 60
# número de fragmentos
# defina como None ou remova e "a biblioteca usará a chamada do endpoint do Bot Gateway para descobrir quantos fragmentos usar."
shard_count = None
# número máximo de quadros que um vídeo de entrada pode ter, será cortado se for muito longo
max_frames = 1024
# tamanho máximo de arquivo temporário do FFmpeg. reduza se o ffmpeg consumir muito seu disco/memória, aumente se puder
max_temp_file_size = "1G"
# limite FPS para sanidade
max_fps = 100
