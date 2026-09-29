"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"

load_dotenv(ROOT / ".env")


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Dados do prompt inválidos"]

    for field in ("description", "system_prompt", "user_prompt", "version"):
        if not str(prompt_data.get(field, "")).strip():
            errors.append(f"Campo obrigatório ausente ou vazio: {field}")

    system_prompt = str(prompt_data.get("system_prompt", ""))
    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    user_prompt = str(prompt_data.get("user_prompt", ""))
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt precisa conter a variável {bug_report}")

    techniques = prompt_data.get("techniques_applied", [])
    technique_count = len(techniques) if isinstance(techniques, list) else 0
    if technique_count < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {technique_count}")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return False

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    identifier = prompt_name if "/" in prompt_name else f"{username}/{prompt_name}"

    techniques = [str(item).strip() for item in prompt_data.get("techniques_applied", [])]
    tags = []
    for tag in list(prompt_data.get("tags") or []) + techniques:
        tag = str(tag).strip()
        if tag and tag not in tags:
            tags.append(tag)

    description = str(prompt_data.get("description", "")).strip()
    techniques_text = ", ".join(techniques)
    if techniques_text and techniques_text not in description:
        description = f"{description} Técnicas: {techniques_text}."

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])

    print(f"Publicando {identifier} (público)...")

    try:
        client = Client()
        url = client.push_prompt(
            identifier,
            object=prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
    except Exception as error:
        print(f"❌ Falha ao fazer push de {identifier}: {error}")
        return False

    print(f"✓ Prompt publicado: {identifier}")
    print(f"  {url}")
    return True


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data:
        return 1

    prompt_data = data.get(PROMPT_KEY)
    if not isinstance(prompt_data, dict):
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    published = push_prompt_to_langsmith(f"{username}/{PROMPT_KEY}", prompt_data)
    return 0 if published else 1


if __name__ == "__main__":
    sys.exit(main())
