{
  pkgs,
  lib,
  config,
  ...
}:
{
  packages = with pkgs; [
    gh
    git
    ripgrep
    just
  ];

  scripts.issues.exec = ''
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    uv run --script "$REPO_ROOT/scripts/issues.py" "$@"
  '';

  dotenv.enable = true;
}
