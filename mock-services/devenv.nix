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
  # Uses the git root so this works both standalone and when imported.
  env.MOCK_SERVICES_DIR = lib.mkDefault "${config.git.root}/mock-services";

  processes.asset-inventory-mock = {
    exec = "cd $MOCK_SERVICES_DIR && uv run uvicorn asset_inventory.app:app --host 0.0.0.0 --port ${toString config.processes.asset-inventory-mock.ports.http.value}";
    ports.http.allocate = 4010;
    ready.http.get = {
      host = "localhost";
      port = config.processes.asset-inventory-mock.ports.http.value;
      path = "/assets";
    };
  };

  processes.cmdb-mock = {
    exec = "cd $MOCK_SERVICES_DIR && uv run uvicorn cmdb.app:app --host 0.0.0.0 --port ${toString config.processes.cmdb-mock.ports.http.value}";
    ports.http.allocate = 4011;
    ready.http.get = {
      host = "localhost";
      port = config.processes.cmdb-mock.ports.http.value;
      path = "/systems";
    };
  };

  processes.iam-mock = {
    exec = "cd $MOCK_SERVICES_DIR && uv run uvicorn iam.app:app --host 0.0.0.0 --port ${toString config.processes.iam-mock.ports.http.value}";
    ports.http.allocate = 4012;
    ready.http.get = {
      host = "localhost";
      port = config.processes.iam-mock.ports.http.value;
      path = "/users";
    };
  };
}
