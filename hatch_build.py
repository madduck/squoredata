"""Hatchling build hook that regenerates the TypeScript bindings.

The hook shells out to ``scripts/generate_ts.py`` so that the generation logic
has a single source of truth.  It only runs when the local
``node_modules/.bin/json2ts`` binary is available, because the generator needs
it; without it the build would have to reach the network, which a build must
not do.  Drift in the committed bindings is caught by CI, which installs the
Node dependencies and checks ``git diff``.
"""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):  # type: ignore[misc]  # no stubs
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        script = Path(self.root) / "scripts" / "generate_ts.py"
        json2ts = Path(self.root) / "node_modules" / ".bin" / "json2ts"

        if not script.exists() or not json2ts.exists():
            # No Node tooling available: ship the committed bindings as they
            # are.  Never touch the network from a build.
            return

        # ``subprocess`` runs a fixed, trusted argv (the local generator),
        # so B404 and B603 do not apply here.
        import subprocess  # nosec B404
        import sys

        subprocess.run(  # nosec B603
            [sys.executable, str(script)], check=True, cwd=self.root
        )
