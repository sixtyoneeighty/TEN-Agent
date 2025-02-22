from ten import (
    Addon,
    register_addon_as_extension,
    TenEnv,
)

@register_addon_as_extension("tavilysearch_tool_python")
class TavilySearchToolExtensionAddon(Addon):
    def on_create_instance(self, ten_env: TenEnv, name: str, context) -> None:
        from .extension import TavilySearchToolExtension
        ten_env.log_info("TavilySearchToolExtensionAddon on_create_instance")
        ten_env.on_create_instance_done(TavilySearchToolExtension(name), context) 