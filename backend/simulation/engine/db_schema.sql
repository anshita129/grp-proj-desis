-- Simulation schema for simulation.engine module (PostgreSQL-oriented).
-- Keeps simulation state separate from live trading tables.

CREATE SCHEMA IF NOT EXISTS simulation;
CREATE SCHEMA IF NOT EXISTS historical;

-- 1) Scenario metadata
CREATE TABLE IF NOT EXISTS simulation.scenarios (
  scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  start_date timestamptz NOT NULL,
  end_date timestamptz NOT NULL,
  timezone TEXT DEFAULT 'UTC',
  config jsonb NOT NULL,
  seed bigint,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  status TEXT DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS scenarios_user_id_idx ON simulation.scenarios(user_id);
CREATE INDEX IF NOT EXISTS scenarios_status_idx ON simulation.scenarios(status);
CREATE INDEX IF NOT EXISTS scenarios_time_range_idx ON simulation.scenarios(start_date, end_date);

-- 2) Historical OHLCV (partitioned by date)
CREATE TABLE IF NOT EXISTS historical.market_data (
  symbol TEXT NOT NULL,
  ts timestamptz NOT NULL,
  open numeric(18,6) NOT NULL,
  high numeric(18,6) NOT NULL,
  low numeric(18,6) NOT NULL,
  close numeric(18,6) NOT NULL,
  volume numeric(20,6),
  exchange TEXT,
  source TEXT,
  extra jsonb,
  PRIMARY KEY (symbol, ts)
) PARTITION BY RANGE (ts);
-- Example yearly partition (add more via automation)
-- CREATE TABLE historical.market_data_2024 PARTITION OF historical.market_data
--   FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE INDEX IF NOT EXISTS market_data_symbol_ts_desc_idx ON historical.market_data (symbol, ts DESC);
CREATE INDEX IF NOT EXISTS market_data_ts_brin_idx ON historical.market_data USING BRIN (ts);

-- 3) Simulation wallets
CREATE TABLE IF NOT EXISTS simulation.simulation_wallets (
  wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  user_id UUID,
  currency TEXT NOT NULL DEFAULT 'USD',
  balance_initial numeric(20,6) NOT NULL,
  balance_current numeric(20,6) NOT NULL,
  reserved numeric(20,6) DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS simulation_wallets_scenario_idx ON simulation.simulation_wallets(scenario_id);
CREATE INDEX IF NOT EXISTS simulation_wallets_user_idx ON simulation.simulation_wallets(user_id);

-- 4) Simulation trades (partitioned by executed_at)
CREATE TABLE IF NOT EXISTS simulation.simulation_trades (
  trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  wallet_id UUID REFERENCES simulation.simulation_wallets(wallet_id) ON DELETE SET NULL,
  executed_at timestamptz NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('buy','sell')),
  price numeric(18,6) NOT NULL,
  quantity numeric(20,6) NOT NULL,
  commission numeric(18,6) DEFAULT 0,
  execution_model TEXT,
  meta jsonb,
  created_at timestamptz DEFAULT now()
) PARTITION BY RANGE (executed_at);
-- Example monthly partition (add via automation)
-- CREATE TABLE simulation.simulation_trades_2024m01 PARTITION OF simulation.simulation_trades
--   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE INDEX IF NOT EXISTS trades_scenario_ts_idx ON simulation.simulation_trades (scenario_id, executed_at DESC);
CREATE INDEX IF NOT EXISTS trades_scenario_symbol_ts_idx ON simulation.simulation_trades (scenario_id, symbol, executed_at DESC);
CREATE INDEX IF NOT EXISTS trades_scenario_wallet_idx ON simulation.simulation_trades (scenario_id, wallet_id);

-- 5) Holdings (current state per scenario/wallet/symbol)
CREATE TABLE IF NOT EXISTS simulation.simulation_holdings (
  holding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  wallet_id UUID NOT NULL REFERENCES simulation.simulation_wallets(wallet_id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  quantity numeric(20,6) NOT NULL,
  avg_price numeric(18,6) NOT NULL,
  cost_basis numeric(22,6) NOT NULL,
  last_trade_at timestamptz,
  last_updated timestamptz DEFAULT now(),
  meta jsonb,
  UNIQUE (scenario_id, wallet_id, symbol)
);
CREATE INDEX IF NOT EXISTS holdings_scenario_symbol_idx ON simulation.simulation_holdings (scenario_id, symbol);
CREATE INDEX IF NOT EXISTS holdings_scenario_wallet_idx ON simulation.simulation_holdings (scenario_id, wallet_id);

-- 6) Holdings snapshots (checkpointing)
CREATE TABLE IF NOT EXISTS simulation.holdings_snapshots (
  scenario_id UUID NOT NULL REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  snapshot_time timestamptz NOT NULL,
  wallet_id UUID NOT NULL,
  symbol TEXT NOT NULL,
  quantity numeric(20,6) NOT NULL,
  price numeric(18,6) NOT NULL,
  nav numeric(22,6) NOT NULL,
  meta jsonb,
  PRIMARY KEY (scenario_id, snapshot_time, wallet_id, symbol)
);
CREATE INDEX IF NOT EXISTS holdings_snapshots_scenario_time_idx ON simulation.holdings_snapshots (scenario_id, snapshot_time DESC);

-- 7) Valuation snapshots
CREATE TABLE IF NOT EXISTS simulation.valuation_snapshots (
  scenario_id UUID NOT NULL REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  snapshot_time timestamptz NOT NULL,
  wallet_id UUID,
  nav numeric(24,6) NOT NULL,
  pnl numeric(24,6) DEFAULT 0,
  unrealized_pnl numeric(24,6) DEFAULT 0,
  realized_pnl numeric(24,6) DEFAULT 0,
  metrics jsonb,
  PRIMARY KEY (scenario_id, snapshot_time, wallet_id)
);
CREATE INDEX IF NOT EXISTS valuation_snapshots_scenario_time_idx ON simulation.valuation_snapshots (scenario_id, snapshot_time DESC);

-- 8) Simulation users (optional)
CREATE TABLE IF NOT EXISTS simulation.simulation_users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT,
  display_name TEXT,
  email TEXT,
  meta jsonb
);

-- 9) Audit logs
CREATE TABLE IF NOT EXISTS simulation.audit_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID REFERENCES simulation.scenarios(scenario_id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  actor TEXT,
  action TEXT,
  payload jsonb
);
CREATE INDEX IF NOT EXISTS audit_logs_scenario_idx ON simulation.audit_logs (scenario_id, created_at DESC);
