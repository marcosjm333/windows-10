# Compatibility

Generated from `data/compatibility.json`.

| Subsystem | Status | Scope |
| --- | --- | --- |
| UEFI boot | PARTIAL | ExitBootServices transaction, pinned handoff and an owned kernel stack; no independent image loader. |
| CPU and exceptions | PARTIAL | GDT, IDT, TSS and IST; fatal exceptions only. AP startup, APIC and IRQ dispatch are pending. |
| Physical memory | PARTIAL | Sparse PFN database, references, generation checks and synchronized allocation; VMM, pools and paging are pending. |
| Diagnostics | PARTIAL | Bounded serial records and terminal crash context; dump persistence, unwinder and module list are pending. |
| Scheduler | DESIGN | Priority ready queues, wait ownership, affinity and preemption contract; implementation pending. |
| Dispatcher | DESIGN | Wait blocks, signal consumption, timeout arbitration and cancellation; implementation pending. |
| IRQL and interrupt routing | RESEARCH | IRQL must bind interrupt masks, local preemption and APIC priority. No emulated IRQL variable. |
| DPC / APC | DESIGN | Per-CPU deferred work and thread-owned APC queues require the scheduler and interrupt model. |
| Object manager | DESIGN | Reference and handle ownership, namespace, security hooks and deferred destruction. |
| PE and driver loading | RESEARCH | Untrusted PE32+ validation, dependency transactions, unwind registration and rollback. |
| I/O manager | DESIGN | Single IRP completion owner, cancellation arbitration, stack locations and device references. |
| Plug and Play | DESIGN | Device tree, PDO/FDO/filter lifetimes and removal state machine. |
| Power | RESEARCH | Power state coordination, device quiescence and PnP interaction. |
| Security and integrity | RESEARCH | Tokens, SIDs, ACLs and trust-preserving image admission. |
| Registry | DESIGN | Typed values, key lifetimes, handles, security checks and ordered notifications. |
| Processes and threads | DESIGN | Address-space ownership, kernel stacks, handle tables, rundown and thread lifecycle. |
| IPC | RESEARCH | Endpoint ownership, messages, cancellation and quotas. |
| HAL | RESEARCH | ACPI discovery, timers, interrupt controllers and DMA/MMIO contracts. |

## NT API contracts

### KeWaitForSingleObject

```c
NTSTATUS KeWaitForSingleObject(PVOID Object, KWAIT_REASON WaitReason, KPROCESSOR_MODE WaitMode, BOOLEAN Alertable, PLARGE_INTEGER Timeout);
```

Status: DESIGN. IRQL: <= APC_LEVEL for a blocking wait; <= DISPATCH_LEVEL only for zero timeout.

Conditional; supports finite or infinite waits, alerts and APC interactions.

No export exists. Requires dispatcher, scheduler, timers and APC semantics.

[Contract source](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-kewaitforsingleobject).

### IoCallDriver

```c
#define IoCallDriver(DeviceObject, Irp) IofCallDriver(DeviceObject, Irp)
```

Status: RESEARCH. IRQL: <= DISPATCH_LEVEL

Dispatch can complete synchronously or return pending; contract research required.

WDK macro, not an independently established binary export. IofCallDriver is the underlying routine.

[Contract source](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-iocalldriver).

### KeRaiseIrql

```c
VOID KeRaiseIrql(KIRQL NewIrql, PKIRQL OldIrql);
```

Status: RESEARCH. IRQL: NewIrql must be >= current IRQL; architecture binding pending.

Does not wait.

WDK macro contract. No internal or binary implementation is provided.

[Contract source](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-keraiseirql).

Drivers tested: 0. Proprietary binary inventory: 0.
