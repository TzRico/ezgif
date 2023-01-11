#!/bin/bash

updategit() {
  # remoto não é configurado por padrão quando o contêiner é configurado
  echo "Atualizando o código do ezgif..."
  if [ ! -d ".git" ]; then
    git init . --initial-branch=master
    git remote add origin https://github.com/Tzrico/ezgif.git
  fi
  git fetch --all
  git reset --hard origin/master
}
updateapt() {
  echo "Atualizando pacotes APT..."
  apt-get update -y
  apt-get install -t experimental -y ffmpeg
  apt-get upgrade -y
  apt autoremove -y
  echo "Feito!"
}
updatepip() {
  # remoto não é configurado por padrão quando o contêiner é configurado
  echo "Atualizando pacotes PIP..."
  python -m poetry install
}

run() {
  # remoto não é configurado por padrão quando o contêiner é configurado
  echo "Running..."
  python -m poetry run python src/main.py
}

# arte ascii do Gifmaker :3
cat "media/active/braillebanner.txt"
printf "\n\n"

if [ "$AUTOMODE" == "ON" ] && [ "$CONFIG" != "" ]; then
  echo "Estamos em modo automático. Executando o Gifmaker"
  if [ "$AUTOUPDATE" == "ON" ]; then
    updategit
    updateapt
    updatepip
  fi
  echo "$CONFIG" | base64 -d >config.py
  run
  exit
fi

# coisa estranha de nome de variável para prompt
PS3='O que você gostaria de fazer? '
choices=("Execute o Gifmaker" "Editar configuração" "Atualize tudo e execute" "Atualizar código do Gifmaker" "Atualizar pacotes APT" "Atualizar pacotes PIP" "Shell de depuração" "Desistir")
select fav in "${choices[@]}"; do
  case $fav in
  "Execute o Gifmaker")
    run
    ;;
  "Editar configuração")
    nano config.py
    ;;
  "Atualize tudo e execute")
    updategit
    updateapt
    updatepip
    run
    ;;
  "Atualizar código do Gifmaker")
    updategit
    ;;
  "Atualizar pacotes APT")
    updateapt
    ;;
  "Atualizar pacotes PIP")
    updatepip
    ;;
  "Shell de depuração")
    /bin/bash
    ;;
  "Desistir")
    echo "Adeus!"
    exit
    ;;
  *) echo "opção inválida $REPLY" ;;
  esac
done
