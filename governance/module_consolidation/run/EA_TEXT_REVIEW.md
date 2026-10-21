# Additional EA evidence review

Source: `EAFIX_auth_docs/04_mt4_bridge_and_execution/0199900003260118_HUEY_P_EA_ExecutionEngine_8.txt`.
Review scope: header and operation inputs (lines 1–185), CSV writer (614–718),
and CSV reader (740–824). Other sections remain unreviewed. This source is not
fully scraped, not approved as current EA authority, and not archive eligible.

The header identifies enhanced version 7.10 while the attachment's title calls
it ExecutionEngine 8. Lines 63–72 default autonomous operation and DLL signals
on, CSV signals off. This does not establish the current execution-only B2
configuration. An approved deployed source/version and configuration are still
needed; changing those defaults would exceed documentation consolidation.

The advanced CSV signal writer emits ten columns (timestamp, symbol, signal
type, confidence, entry price, stop loss, take profit, source, category, comment).
Its response writer emits ten columns including execution status and ticket.
The separate CSV reader skips seven header fields and reads seven signal
fields (execution time, symbol, order type, lots, SL, TP, comment). These are
different paths; neither is proven to be the approved BrokerOrderEnvelope /
AdapterAck protocol. The reviewed sections do not establish its required
version, file sequence/hash, acknowledgement deadline, retry/exhaustion or
compatibility semantics.

Disposition: retain these observations as partial historical evidence. Do not
promote this text, or the replacement moving-average sample, to the current
execution-only authority. BLOCK-CURRENT-EA-AUTHORITY and the two bridge
contract/timeout blockers remain unresolved. Required next input: approved
current execution EA/interface and its exact wire and retry/acknowledgement
specification, or an approved intended execution-only specification containing
those facts. Full compilation and deployed conformance are separate checks.
