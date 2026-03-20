{
  pkgs,
  lib,
  config,
  ...
}:

let
  pythonVersion = lib.fileContents ./.python-version;
  database_name = "verdict";
  postgres_host = "127.0.0.1";
  postgres_user = "postgres";
  postgres_password = "postgres";
in
{
  packages = with pkgs; [
    pgcli
  ];

  env = {
    DATABASE_NAME = if config.devenv.isTesting then "${database_name}_test" else database_name;
    DATABASE_PORT = toString config.processes.postgres.ports.main.value;

    ENVIRONMENT = if config.devenv.isTesting then "test" else "development";
    VERDICT_URL = "http://localhost:${toString config.processes.verdict-app.ports.http.value}";
  };

  languages.python = {
    enable = true;
    version = pythonVersion;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  services.postgres = {
    enable = true;
    package = pkgs.postgresql_16;

    listen_addresses = lib.mkForce postgres_host;
    port = 5432;

    initialScript = ''
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${postgres_user}') THEN
        CREATE ROLE ${postgres_user} SUPERUSER LOGIN;
        END IF;
      END
      $$;
    '';

    initialDatabases = [
      { name = database_name; }
      { name = "${database_name}_test"; }
    ];

    settings = {
      log_connections = true;
      log_statement = "all";
      logging_collector = true;
      log_disconnections = true;
      log_destination = lib.mkForce "stderr";

      shared_buffers = "256MB";
      effective_cache_size = "1GB";
      maintenance_work_mem = "64MB";
      checkpoint_completion_target = 0.9;
      wal_buffers = "16MB";
      default_statistics_target = 100;
      random_page_cost = 1.1;
      work_mem = "4MB";
      min_wal_size = "1GB";
      max_wal_size = "4GB";
    };
  };

  processes.verdict-app = {
    ports.http.allocate = 8000;
    exec = "uv run uvicorn app.main:app --host 0.0.0.0 --port ${toString config.processes.verdict-app.ports.http.value}";
    ready.http.get = {
      host = "localhost";
      port = config.processes.verdict-app.ports.http.value;
      path = "/";
    };
  };

  git-hooks.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
  };

  enterShell = ''
    echo ""
    echo "🚀 $GREET"
    echo ""
    echo "Python: ${pythonVersion}"
    echo "PostgreSQL: $(postgres --version | head -n1)"
    echo "uv: $(uv --version)"
    echo ""
    echo "Run 'devenv up' to start the development server"
    echo ""
  '';

  tasks."verdict-app:gen-env" =
    let
      environment = if config.devenv.isTesting then "test" else "development";
      db_name = if config.devenv.isTesting then "${database_name}_test" else database_name;
      db_port = toString config.processes.postgres.ports.main.value;
    in
    {
      exec = ''
        cat > .env.${environment} <<EOF
        ENVIRONMENT=${environment}
        DATABASE_NAME=${db_name}
        DATABASE_HOST=${postgres_host}
        DATABASE_PORT=${db_port}
        DATABASE_USER=${postgres_user}
        DATABASE_PASSWORD=${postgres_password}
        DATABASE_URL=postgresql://${postgres_user}:${postgres_password}@${postgres_host}:${db_port}/${db_name}
        ASSET_INVENTORY_URL=http://localhost:${toString config.processes.asset-inventory-mock.ports.http.value}/assets
        CMDB_URL=http://localhost:${toString config.processes.cmdb-mock.ports.http.value}/systems
        IAM_URL=http://localhost:${toString config.processes.iam-mock.ports.http.value}/users
        CONFIG_BASEDIR=../config
        VERDICT_URL=http://localhost:${toString config.processes.verdict-app.ports.http.value}
        EOF
      '';
      before = [ "devenv:processes:verdict-app" ];
    };

  tasks."verdict-app:db-migrate" = lib.mkIf (!config.devenv.isTesting) {
    exec = "just db-migrate";
    after = [ "verdict-app:gen-env" ];
    before = [ "devenv:processes:verdict-app" ];
  };

  tasks."verdict-app:db-setup" = lib.mkIf config.devenv.isTesting {
    exec = ''
      echo "db-setup: resetting test database"
      just db-reset
      echo "db-setup: running migrations"
      just db-migrate
      echo "db-setup: done"
    '';
    after = [ "verdict-app:gen-env" ];
    before = [ "devenv:processes:verdict-app" ];
  };

  enterTest = ''
    just check

    DATABASE_NAME_TEST=${database_name}_test just test --junit-xml=test-results/unit.xml

    DATABASE_NAME_TEST=${database_name}_test just test-e2e --junit-xml=test-results/e2e.xml
  '';
}
