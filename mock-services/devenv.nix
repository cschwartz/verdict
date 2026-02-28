{ lib, config, ... }:

let
  pythonVersion = lib.fileContents ./.python-version;
in
{
  languages.python = {
    enable = true;
    version = pythonVersion;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # Points to the mock-services directory at runtime.
  # Default works when mock-services IS the devenv project.
  # Importers (e.g. verdict-backend) override via mkForce.
  env.MOCK_SERVICES_DIR = lib.mkDefault config.devenv.root;

  processes.asset-inventory-mock = {
    exec = "cd $MOCK_SERVICES_DIR && uv run uvicorn asset_inventory.app:app --host 0.0.0.0 --port 4010";
    process-compose = {
      readiness_probe = {
        http_get = {
          host = "localhost";
          port = 4010;
          path = "/assets";
        };
        initial_delay_seconds = 2;
        period_seconds = 2;
      };
    };
  };
}
