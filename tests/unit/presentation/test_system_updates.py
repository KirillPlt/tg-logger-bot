from types import SimpleNamespace

from app.presentation.routers.system_updates import _reaction_type_to_text, _render_reactions


def test_reaction_type_to_text_returns_emoji_symbol() -> None:
    reaction = SimpleNamespace(emoji="🔥")

    assert _reaction_type_to_text(reaction) == "🔥"


def test_render_reactions_uses_actual_reaction_objects() -> None:
    reactions = (
        SimpleNamespace(emoji="🔥"),
        SimpleNamespace(emoji="👍"),
    )

    assert _render_reactions(reactions) == "🔥, 👍"
