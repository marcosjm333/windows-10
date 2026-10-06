# Foundation invariants

1. No firmware call occurs after successful ExitBootServices.
2. No allocation or logging occurs between final map retrieval and exit attempt.
3. Exit retries use the existing buffer and stop after four attempts.
4. Only sorted, nonoverlapping, aligned, overflow-checked map entries are published.
5. Only conventional write-back memory without runtime/protected/nonvolatile
   attributes becomes free. All LoaderData, runtime, ACPI and MMIO remain reserved.
6. PFN storage outlives every database user. Initialization is exclusive and
   publishes nothing on failure. Input/output metadata must not overlap.
7. A live frame has a nonzero generation and a positive reference count.
8. Release consumes one owned reference; retaining requires an already owned
   live reference. Count zero permits reuse only with a new generation.
9. Generation exhaustion retires the frame. Reference overflow changes no state.
10. The PFN lock protects metadata, cursor and free count with acquire/release
    ordering. Fewer than 2^32 tickets may be outstanding; callers must make
    scheduling progress. Interrupt/NMI/preemption reentry is forbidden.
11. The free count equals the number of unreferenced, nonretired entries.
12. Kernel exception entry clears DF, preserves GPRs, aligns the stack and reserves
    Microsoft shadow space before calling C. Exceptions terminate; no recovery
    or IRET semantics are promised yet.
13. Crash capture elects one writer. It never takes PFN or serial waiting locks.
14. No kernel API returns success for an operation that has not been implemented.

Check 10 permits host concurrency and the current nonpreemptible BSP phase. It
does not validate a future scheduler/interrupt integration. Guard pages, page-table
ownership and TLB acknowledgement invariants belong to M1 and are not satisfied
by the current identity mapping.
