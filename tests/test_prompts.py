"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_v2_prompt():
    """Retorna o bloco do prompt otimizado."""
    prompts = load_prompts(str(PROMPT_PATH))
    assert "bug_to_user_story_v2" in prompts
    return prompts["bug_to_user_story_v2"]


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = get_v2_prompt()
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = get_v2_prompt()["system_prompt"]
        assert "Você é um Engenheiro de Requisitos Sênior" in system_prompt

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = get_v2_prompt()["system_prompt"]
        assert "User Story" in system_prompt
        assert "Como um" in system_prompt
        assert "eu quero" in system_prompt
        assert "para que" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = get_v2_prompt()["system_prompt"]
        assert system_prompt.count("Relato:") >= 3
        assert system_prompt.count("Saída:") >= 3
        assert "Exemplo 1" in system_prompt
        assert "Exemplo 2" in system_prompt
        assert "Exemplo 3" in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        raw_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        assert "[TODO]" not in raw_prompt
        assert "TODO" not in get_v2_prompt()["system_prompt"]

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = get_v2_prompt()
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2

        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
