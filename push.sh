#!/bin/bash

# ==============================================================================
# PROTOCOLO TOLERÂNCIA ZERO: CI/CD LOCAL
# ==============================================================================

# 1. Verifica se você passou uma mensagem de commit
if [ -z "$1" ]; then
    echo "❌ BLOQUEADO: Você não informou a mensagem do commit."
    echo "💡 Uso correto: ./push.sh \"sua mensagem de commit aqui\""
    exit 1
fi

MENSAGEM_COMMIT="$1"

echo "======================================================="
echo "🛡️ INICIANDO BLINDAGEM DE CÓDIGO..."
echo "======================================================="

# 2. Roda a suíte completa de testes
echo "🧪 Executando Pytest..."
pytest -v

# 3. Captura o Código de Saída (Exit Code) do Pytest
if [ $? -ne 0 ]; then
    echo "======================================================="
    echo "❌ FALHA CRÍTICA: Os testes locais falharam!"
    echo "O código não sairá da sua máquina até que a arquitetura seja consertada."
    echo "======================================================="
    exit 1
fi

echo "======================================================="
echo "✅ CÓDIGO APROVADO. Iniciando esteira de envio..."
echo "======================================================="

# 4. Descobre a branch atual
BRANCH_ATUAL=$(git rev-parse --abbrev-ref HEAD)

# 5. Executa as operações do Git
git add .
git commit -m "$MENSAGEM_COMMIT"
git push origin $BRANCH_ATUAL

echo "======================================================="
echo "🚀 SUCESSO! Código empurrado para a branch '$BRANCH_ATUAL'."
echo "O GitHub Actions assumirá o comando a partir de agora."
echo "======================================================="
