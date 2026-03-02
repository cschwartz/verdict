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
    REPO_ROOT="$(git rev-parse --show-toplevel)" || {
      echo "Error: could not determine repository root." >&2
      exit 1
    }
    if [ -z "$REPO_ROOT" ]; then
      echo "Error: could not determine repository root." >&2
      exit 1
    fi
    uv run --script "$REPO_ROOT/scripts/issues.py" "$@"
  '';

  dotenv.enable = true;
}
