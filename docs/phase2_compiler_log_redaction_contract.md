# Phase-2 compiler-log redaction contract

The unchanged raw MetaEditor log is retained outside Git in its isolated Windows evidence directory. Compiler acceptance is bound to that raw artifact by its SHA-256 and byte size in the typed compiler record.

Git contains only a deterministic UTF-16 derivative. Policy `nora.compiler_log_path_redaction_v1` replaces each recognized Windows user-root token (`<drive>:\Users\<user>`) with `<WINDOWS_USER_PATH>`. It does not change the remainder of a path, executable or source names, diagnostics, line numbers, compiler results, warnings, errors, hashes, timestamps, or completion evidence.

Import requires the unchanged external raw log. The importer verifies its size and hash, regenerates the derivative, requires byte equality with the submitted derivative, verifies the derivative size and hash, rejects remaining absolute user-root tokens, and binds the compiler-output and execution-packet identities to the raw-log hash. Missing raw evidence or any non-path change fails closed.
