# Phase 2W percentile non-finite input policy

The admitted Phase-2W percentile fixture has a finite nullable `sma3` source.
`NaN`, positive infinity, and negative infinity are rejected by the canonical
task input reader before the percentile transform is evaluated.  The relevant
reader path is `engine/labengine/src/main.rs`: the Float64 column reader calls
`is_finite()` for every present required or optional value and reports the row
as non-finite when it fails.

`transform_percentile` in `engine/labengine/src/indicators.rs` therefore owns
only nullable-window behavior: output is null until a complete non-null window
is available, and a null source/window member produces null.  It is not the
repository layer that normalizes or admits non-finite values.

The Phase-2W generator mirrors this boundary: its fixed source vector accepts
only finite values or null and fails before publishing any artifact package.
This does not change the accepted finite fixture or its percentile semantics.
