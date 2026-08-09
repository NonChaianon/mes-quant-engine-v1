# Local artifacts

`cache/` is for a read-only local copy of canonical Drive inputs. `runs/` is for new repository
outputs. Both directories are ignored by Git.

Do not copy DBN/Parquet files into ordinary Git. Do not put API keys, IBKR credentials, or account
identifiers here. New runs must use a new directory and must never overwrite frozen Colab evidence.

