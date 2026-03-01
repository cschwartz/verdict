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
  postgres_port = 5432;
  postgres_user = "postgres";
  postgres_password = "postgres";
in
{
  packages = with pkgs; [
    pgcli
  ];

  # Override mock-services path for the cross-project import.
  env.MOCK_SERVICES_DIR = lib.mkForce "${config.devenv.root}/../mock-services";

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

    listen_addresses = postgres_host;
    port = postgres_port;

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
    exec = "uv run uvicorn app.main:app --host 0.0.0.0 --port 8000";
    process-compose = {
      disabled = true;
      readiness_probe = {
        http_get = {
          host = "localhost";
          port = 8000;
          path = "/";
        };
        initial_delay_seconds = 2;
        period_seconds = 2;
      };
    };
  };

  git-hooks.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
  };

  scripts.gen-env-sample.exec = ''
    cat > .env.sample <<EOF
    DATABASE_NAME=${database_name}
    DATABASE_NAME_TEST=${database_name}_test
    DATABASE_HOST=${postgres_host}
    DATABASE_PORT=${toString postgres_port}
    DATABASE_USER=${postgres_user}
    DATABASE_PASSWORD=${postgres_password}
    DATABASE_URL=postgresql://${postgres_user}:${postgres_password}@${postgres_host}:${toString postgres_port}/${database_name}
    ASSET_INVENTORY_URL=http://localhost:4010/assets
    EOF
    echo "Generated .env.sample"
  '';

  enterShell = ''
    echo ""
    echo "🚀 $GREET"
    echo ""
    echo "Python: ${pythonVersion}"
    echo "PostgreSQL: $(postgres --version | head -n1)"
    echo "uv: $(uv --version)"
    echo ""
    echo "Database: $DATABASE_URL"
    echo ""
    gen-env-sample
    echo ""
    echo "Run 'just setup' to initialize the environment"
    echo "Run 'just dev' to start the development server"
    echo "Run 'just db-info' to see database configuration"
    echo ""
  '';

  enterTest = ''
    until pg_isready -h ${postgres_host} -p ${toString postgres_port} -q; do
      sleep 0.1
    done
    gen-env-sample
    cp .env.sample .env
    just db-migrate
    just db-test-reset
    DATABASE_NAME=${database_name}_test just db-migrate
    just check
    DATABASE_NAME=${database_name}_test uv run pytest --disable-plugin-autoload -p asyncio -m 'not e2e'

    # Cleanup background processes on any exit
    MOCK_PID=
    APP_PID=
    cleanup() {
      kill $APP_PID $MOCK_PID 2>/dev/null || true
      wait $APP_PID $MOCK_PID 2>/dev/null || true
    }
    trap cleanup EXIT INT TERM

    # Start mock service
    echo "Starting mock asset inventory..."
    (cd $MOCK_SERVICES_DIR && exec uv run uvicorn asset_inventory.app:app --host 0.0.0.0 --port 4010) &
    MOCK_PID=$!

    retries=0
    until curl -sf http://localhost:4010/assets > /dev/null 2>&1; do
      retries=$((retries + 1))
      if [ $retries -ge 30 ]; then
        echo "ERROR: Mock service failed to start"
        exit 1
      fi
      sleep 1
    done
    echo "Mock service ready"

    # Start verdict app against test DB
    echo "Starting verdict app..."
    (DATABASE_NAME=${database_name}_test ASSET_INVENTORY_URL=http://localhost:4010/assets \
      exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000) &
    APP_PID=$!

    retries=0
    until curl -sf http://localhost:8000/ > /dev/null 2>&1; do
      retries=$((retries + 1))
      if [ $retries -ge 30 ]; then
        echo "ERROR: Verdict app failed to start"
        exit 1
      fi
      sleep 1
    done
    echo "Verdict app ready"

    # Reset test DB and run E2E tests
    just db-test-reset
    DATABASE_NAME=${database_name}_test just db-migrate
    just test-e2e
  '';
}
