# retail-weather-pipeline

## dbt Schema Routing
dbt's +schema config appends to the profile dataset by default, not replaces it.
Fix: custom generate_schema_name macro in dbt/macros/ that returns the target_schema
directly when a custom schema is specified.

profiles.yml dataset: raw (acts as fallback only)
+schema: staging → lands in staging
+schema: marts   → lands in marts
