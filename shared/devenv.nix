{
  pkgs,
  lib,
  config,
  ...
}:
{
  packages = with pkgs; [
    git
    ripgrep
    just
  ];

  dotenv.enable = true;
}
