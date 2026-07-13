# MetaEditor CLI success policy

The nora.metaeditor_cli_success_v1 policy accepts build 5.0.0.5836 raw exit 1
only with exact compiler/version, bound source hashes, complete source-identifying
log, zero warnings/errors, and a target-path EX5 removed before invocation then
freshly produced and hashed. Any missing or contradictory check fails closed.
The staged inventory identity hashes allowlisted paths only; every path content
hash is independently bound in the batch identity.
