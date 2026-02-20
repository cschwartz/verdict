# devenv.nix
{ pkgs, ... }:
{
  git-hooks.hooks = {
    ruff = {
      enable = true;
      name = "ruff";
      entry = "${pkgs.ruff}/bin/ruff check --fix";
      files = "\\.(py)$";
      pass_filenames = true;
      excludes = [ "^(?!verdict-backend/).*" ];
    };

    ruff-format = {
      enable = true;
      name = "ruff-format";
      entry = "${pkgs.ruff}/bin/ruff format";
      files = "\\.(py)$";
      pass_filenames = true;
      excludes = [ "^(?!verdict-backend/).*" ];
    };

    mypy = {
      enable = true;
      name = "mypy";
      entry = "${pkgs.bash}/bin/bash -c 'uv run --directory verdict-backend/ mypy app '";
      language = "system";
      files = "^verdict-backend/.*\\.py$";
      pass_filenames = false;
      stages = [ "pre-push" ];
    };
  };
}
