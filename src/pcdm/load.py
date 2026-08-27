"""Load landing files into DuckDB as external/landing tables for dbt sources."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb


def _batch_id() -> str:
    return uuid.uuid4().hex[:16]


def load_landing(*, scale: str, root: Path, warehouse: Path) -> None:
    landing = root / "datasets" / scale / "landing"
    if not landing.exists():
        raise FileNotFoundError(f"Landing path not found: {landing}. Run generate first.")

    warehouse.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(warehouse))
    sql = (root / "scripts" / "database.sql").read_text(encoding="utf-8")
    con.execute(sql)

    batch = _batch_id()
    loaded_at = datetime.now(timezone.utc).isoformat()

    # Register a manifest of files
    con.execute(
        """
        CREATE OR REPLACE TABLE landing.file_manifest AS
        SELECT * FROM (SELECT
            CAST(NULL AS VARCHAR) AS source_system,
            CAST(NULL AS VARCHAR) AS relative_path,
            CAST(NULL AS VARCHAR) AS absolute_path,
            CAST(NULL AS VARCHAR) AS batch_id,
            CAST(NULL AS VARCHAR) AS loaded_at,
            CAST(NULL AS VARCHAR) AS row_hash,
            CAST(NULL AS BIGINT) AS byte_length
        ) WHERE 1=0
        """
    )

    rows = []
    for path in sorted(landing.rglob("*")):
        if not path.is_file():
            continue
        if "quarantine" in path.parts:
            continue
        rel = str(path.relative_to(landing)).replace("\\", "/")
        source_system = rel.split("/", 1)[0] if "/" in rel else "unknown"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append((source_system, rel, str(path), batch, loaded_at, digest, path.stat().st_size))

    if rows:
        con.executemany(
            "INSERT INTO landing.file_manifest VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )

    # Create views / tables for key CSV/pipe sources used by dbt
    _register_rx_demand(con, landing, batch, loaded_at)
    _register_csv_sources(con, landing, batch, loaded_at)
    _register_edi_flat(con, landing, batch, loaded_at)
    _run_mdm_into_duckdb(con, landing.parent / "ground_truth")

    con.execute(
        """
        CREATE OR REPLACE TABLE dq.run_history AS
        SELECT * FROM dq.run_history
        UNION ALL BY NAME
        SELECT
            ? AS run_id,
            CAST(? AS TIMESTAMP) AS started_at,
            CAST(? AS TIMESTAMP) AS ended_at,
            ? AS scale,
            CAST(NULL AS INTEGER) AS seed,
            'LOAD_OK' AS status,
            'landing load' AS notes
        """,
        [batch, loaded_at, loaded_at, scale],
    )
    con.close()


def _add_meta_sql(batch: str, loaded_at: str, source_file_expr: str = "filename") -> str:
    return f"""
        '{batch}' AS _batch_id,
        CAST('{loaded_at}' AS TIMESTAMP) AS _loaded_at,
        {source_file_expr} AS _source_file,
        'OK' AS _record_status,
        CAST(NULL AS VARCHAR) AS _reject_reason
    """


def _register_rx_demand(con: duckdb.DuckDBPyConnection, landing: Path, batch: str, loaded_at: str) -> None:
    pattern = str(landing / "rx_demand" / "*.txt").replace("\\", "/")
    files = list((landing / "rx_demand").glob("*.txt")) if (landing / "rx_demand").exists() else []
    if not files:
        con.execute(
            """
            CREATE OR REPLACE TABLE landing.rx_demand AS
            SELECT
                CAST(NULL AS VARCHAR) AS data_supplier_id,
                CAST(NULL AS VARCHAR) AS period_type,
                CAST(NULL AS DATE) AS period_end_date,
                CAST(NULL AS INTEGER) AS restatement_version,
                CAST(NULL AS DATE) AS delivery_date,
                CAST(NULL AS VARCHAR) AS prescriber_id,
                CAST(NULL AS VARCHAR) AS me_number,
                CAST(NULL AS VARCHAR) AS npi,
                CAST(NULL AS VARCHAR) AS dea_number,
                CAST(NULL AS VARCHAR) AS product_id,
                CAST(NULL AS VARCHAR) AS ndc9,
                CAST(NULL AS VARCHAR) AS market_id,
                CAST(NULL AS VARCHAR) AS geo_type,
                CAST(NULL AS VARCHAR) AS geo_id,
                CAST(NULL AS VARCHAR) AS pay_type,
                CAST(NULL AS VARCHAR) AS plan_id,
                CAST(NULL AS DECIMAL(18,4)) AS trx_count,
                CAST(NULL AS DECIMAL(18,4)) AS nrx_count,
                CAST(NULL AS DECIMAL(18,4)) AS rrx_count,
                CAST(NULL AS DECIMAL(18,4)) AS trx_units,
                CAST(NULL AS DECIMAL(18,4)) AS nrx_units,
                CAST(NULL AS DECIMAL(18,2)) AS trx_dollars,
                CAST(NULL AS DECIMAL(10,6)) AS projection_factor,
                CAST(NULL AS VARCHAR) AS sample_flag,
                CAST(NULL AS VARCHAR) AS suppression_flag,
                CAST(NULL AS VARCHAR) AS _batch_id,
                CAST(NULL AS TIMESTAMP) AS _loaded_at,
                CAST(NULL AS VARCHAR) AS _source_file,
                CAST(NULL AS VARCHAR) AS _record_status,
                CAST(NULL AS VARCHAR) AS _reject_reason,
                CAST(NULL AS VARCHAR) AS _row_hash
            WHERE 1=0
            """
        )
        return

    con.execute(
        f"""
        CREATE OR REPLACE TABLE landing.rx_demand AS
        SELECT
            data_supplier_id, period_type,
            CAST(period_end_date AS DATE) AS period_end_date,
            CAST(restatement_version AS INTEGER) AS restatement_version,
            CAST(delivery_date AS DATE) AS delivery_date,
            prescriber_id, me_number, npi, dea_number, product_id, ndc9, market_id,
            geo_type, geo_id, pay_type, plan_id,
            CAST(trx_count AS DECIMAL(18,4)) AS trx_count,
            CAST(nrx_count AS DECIMAL(18,4)) AS nrx_count,
            CAST(rrx_count AS DECIMAL(18,4)) AS rrx_count,
            CAST(trx_units AS DECIMAL(18,4)) AS trx_units,
            CAST(nrx_units AS DECIMAL(18,4)) AS nrx_units,
            CAST(trx_dollars AS DECIMAL(18,2)) AS trx_dollars,
            CAST(projection_factor AS DECIMAL(10,6)) AS projection_factor,
            sample_flag, suppression_flag,
            '{batch}' AS _batch_id,
            CAST('{loaded_at}' AS TIMESTAMP) AS _loaded_at,
            filename AS _source_file,
            'OK' AS _record_status,
            CAST(NULL AS VARCHAR) AS _reject_reason,
            md5(CONCAT_WS('|',
                COALESCE(prescriber_id,''), COALESCE(product_id,''), COALESCE(market_id,''),
                COALESCE(geo_id,''), COALESCE(pay_type,''), COALESCE(CAST(period_end_date AS VARCHAR),''),
                COALESCE(CAST(restatement_version AS VARCHAR),'')
            )) AS _row_hash
        FROM read_csv('{pattern}', delim='|', header=true, filename=true, auto_detect=true, ignore_errors=false)
        """
    )


def _register_csv_sources(con: duckdb.DuckDBPyConnection, landing: Path, batch: str, loaded_at: str) -> None:
    mapping = {
        "hcp_master": "hcp_master/*.csv",
        "hco_master": "hco_master/*.csv",
        "hcp_hco_affiliation": "hcp_hco_affiliation/*.csv",
        "plan_formulary": "plan_formulary/*.csv",
        "crm_call": "crm_calls/*.csv",
        "crm_sample": "crm_samples/*.csv",
        "roster": "roster/*.csv",
        "alignment_zip": "alignment/zip/*.csv",
        "alignment_account": "alignment/account/*.csv",
        "alignment_prescriber": "alignment/prescriber/*.csv",
        "targets": "targets_goals/*.csv",
        "sp_referral": "specialty/sp_referral/*.csv",
        "sp_enrollment": "specialty/sp_enrollment/*.csv",
        "sp_benefit_verification": "specialty/sp_benefit_verification/*.csv",
        "sp_prior_auth": "specialty/sp_prior_auth/*.csv",
        "sp_status_history": "specialty/sp_status_history/*.csv",
        "sp_dispense": "specialty/sp_dispense/*.csv",
        "sp_copay": "specialty/sp_copay/*.csv",
        "sp_inventory": "specialty/sp_inventory/*.csv",
        "sp_discontinuation": "specialty/sp_discontinuation/*.csv",
        "product_master": "reference/product_master.csv",
        "dea_hin_xref": "reference/dea_hin_xref.csv",
        "calendar": "reference/calendar.csv",
        "territories": "reference/territories.csv",
        "ground_truth_hcp": "../ground_truth/hcp_entities.csv",
    }

    for table, rel in mapping.items():
        path = landing / rel if not rel.startswith("..") else (landing / rel).resolve()
        # support globs
        if "*" in rel:
            base = landing / rel.split("*")[0].rstrip("/\\")
            pattern = str(landing / rel).replace("\\", "/")
            has = base.exists() and any(base.glob("*" + rel.split("*", 1)[-1]))
            if not has:
                con.execute(
                    f"CREATE OR REPLACE TABLE landing.{table} AS SELECT CAST(NULL AS VARCHAR) AS _placeholder WHERE 1=0"
                )
                continue
            con.execute(
                f"""
                CREATE OR REPLACE TABLE landing.{table} AS
                SELECT *, '{batch}' AS _batch_id, CAST('{loaded_at}' AS TIMESTAMP) AS _loaded_at,
                       filename AS _source_file, 'OK' AS _record_status,
                       CAST(NULL AS VARCHAR) AS _reject_reason
                FROM read_csv('{pattern}', header=true, filename=true, auto_detect=true, ignore_errors=true)
                """
            )
        else:
            file_path = landing / rel if not rel.startswith("..") else (landing.parent / "ground_truth" / Path(rel).name)
            # fix ground truth path
            if table == "ground_truth_hcp":
                file_path = landing.parent / "ground_truth" / "hcp_entities.csv"
            if not file_path.exists():
                con.execute(
                    f"CREATE OR REPLACE TABLE landing.{table} AS SELECT CAST(NULL AS VARCHAR) AS _placeholder WHERE 1=0"
                )
                continue
            fp = str(file_path).replace("\\", "/")
            con.execute(
                f"""
                CREATE OR REPLACE TABLE landing.{table} AS
                SELECT *, '{batch}' AS _batch_id, CAST('{loaded_at}' AS TIMESTAMP) AS _loaded_at,
                       '{fp}' AS _source_file, 'OK' AS _record_status,
                       CAST(NULL AS VARCHAR) AS _reject_reason
                FROM read_csv('{fp}', header=true, auto_detect=true, ignore_errors=true)
                """
            )


def _run_mdm_into_duckdb(con: duckdb.DuckDBPyConnection, gt: Path) -> None:
    variants = gt / "hcp_source_variants.csv"
    if not variants.exists():
        return
    import pandas as pd

    from pcdm.mdm import evaluate_mdm, run_mdm

    src = pd.read_csv(variants)
    result = run_mdm(src)
    for name, df in result.items():
        con.register(f"_tmp_{name}", df)
        con.execute(f"CREATE OR REPLACE TABLE mdm.{name} AS SELECT * FROM _tmp_{name}")
        con.unregister(f"_tmp_{name}")
    td = pd.read_csv(gt / "true_duplicate_pairs.csv") if (gt / "true_duplicate_pairs.csv").exists() else pd.DataFrame()
    ff = pd.read_csv(gt / "false_friend_pairs.csv") if (gt / "false_friend_pairs.csv").exists() else pd.DataFrame()
    metrics = evaluate_mdm(result["xref"], td, ff)
    con.execute(
        """
        CREATE OR REPLACE TABLE mdm.match_evaluation AS
        SELECT
            CAST(? AS DOUBLE) AS precision,
            CAST(? AS DOUBLE) AS recall,
            CAST(? AS DOUBLE) AS f1,
            CAST(? AS BOOLEAN) AS false_friends_separated
        """,
        [metrics["precision"], metrics["recall"], metrics["f1"], metrics["false_friends_separated"]],
    )
    # Raw tables consumed by dbt models (avoid name collision with dbt outputs)
    con.execute("CREATE OR REPLACE TABLE mdm.hcp_golden_raw AS SELECT * FROM mdm.golden")
    con.execute("CREATE OR REPLACE TABLE mdm.hcp_xref_raw AS SELECT * FROM mdm.xref")


def _register_edi_flat(con: duckdb.DuckDBPyConnection, landing: Path, batch: str, loaded_at: str) -> None:
    flat_dir = landing / "edi867_flat"
    if not flat_dir.exists() or not list(flat_dir.glob("*.csv")):
        con.execute(
            """
            CREATE OR REPLACE TABLE landing.edi867_line AS
            SELECT CAST(NULL AS VARCHAR) AS interchange_control_number WHERE 1=0
            """
        )
        return
    pattern = str(flat_dir / "*.csv").replace("\\", "/")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE landing.edi867_line AS
        SELECT *, '{batch}' AS _batch_id, CAST('{loaded_at}' AS TIMESTAMP) AS _loaded_at,
               filename AS _source_file, 'OK' AS _record_status,
               CAST(NULL AS VARCHAR) AS _reject_reason
        FROM read_csv('{pattern}', header=true, filename=true, auto_detect=true, ignore_errors=true)
        """
    )
