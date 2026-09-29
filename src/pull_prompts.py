"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "prompts" / "bug_to_user_story_v1.yml"
PROMPT_IDENTIFIER = "leonanluppi/bug_to_user_story_v1"

load_dotenv(ROOT / ".env")


def _message_template(message) -> str:
    """Extrai o texto do template de uma mensagem do ChatPromptTemplate."""
    prompt_attr = getattr(message, "prompt", None)
    if prompt_attr is None:
        return ""

    if isinstance(prompt_attr, list):
        parts = []
        for item in prompt_attr:
            template = getattr(item, "template", None)
            if isinstance(template, str):
                parts.append(template)
        return "\n".join(parts)

    template = getattr(prompt_attr, "template", "")
    return template if isinstance(template, str) else str(template)


def _message_role(message) -> str:
    """Classifica a mensagem como system ou user."""
    class_name = message.__class__.__name__.lower()
    if "system" in class_name:
        return "system"

    role = getattr(message, "role", "")
    if isinstance(role, str) and role.lower() == "system":
        return "system"

    return "user"


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt semente e grava prompts/bug_to_user_story_v1.yml.

    Returns:
        Dados salvos, ou None em caso de erro.
    """
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return None

    print_section_header("PULL DE PROMPTS DO LANGSMITH")
    print(f"Prompt: {PROMPT_IDENTIFIER}")

    try:
        client = Client()
        prompt = client.pull_prompt(
            PROMPT_IDENTIFIER,
            dangerously_pull_public_prompt=True,
        )
    except Exception as error:
        print(f"❌ Falha ao fazer pull do prompt: {error}")
        return None

    system_prompt = ""
    user_prompt = ""
    for message in prompt.messages:
        text = _message_template(message)
        if _message_role(message) == "system" and not system_prompt:
            system_prompt = text
        else:
            user_prompt = text

    if not system_prompt or not user_prompt:
        print("❌ O prompt baixado não contém system prompt e user prompt.")
        return None

    description = "Prompt para converter relatos de bugs em User Stories"
    tags = ["bug-analysis", "user-story", "product-management"]
    try:
        info = client.get_prompt(PROMPT_IDENTIFIER)
        if getattr(info, "description", None):
            description = info.description
        if getattr(info, "tags", None):
            tags = list(info.tags)
    except Exception:
        pass

    data = {
        "bug_to_user_story_v1": {
            "description": description,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "tags": tags,
        }
    }

    if not save_yaml(data, str(OUTPUT_PATH)):
        return None

    print(f"✓ Prompt salvo em {OUTPUT_PATH}")
    return data


def main():
    """Função principal"""
    result = pull_prompts_from_langsmith()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
