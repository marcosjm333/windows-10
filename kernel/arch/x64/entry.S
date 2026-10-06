.text
.globl nw_enter_kernel
nw_enter_kernel:
    cli
    cld
    movq %rdx, %rsp
    andq $-16, %rsp
    xorq %rbp, %rbp
    subq $32, %rsp
    call nw_kernel_entry
    ud2

.globl nw_load_gdt
nw_load_gdt:
    lgdt (%rcx)
    movw $16, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %ss
    pushq $8
    leaq 1f(%rip), %rax
    pushq %rax
    lretq
1:
    movw $24, %ax
    ltr %ax
    retq

.macro NW_ISR n, error=0
.globl nw_isr_\n
nw_isr_\n:
.if !\error
    pushq $0
.endif
    pushq $\n
    jmp nw_isr_common
.endm
NW_ISR 0
NW_ISR 1
NW_ISR 2
NW_ISR 3
NW_ISR 4
NW_ISR 5
NW_ISR 6
NW_ISR 7
NW_ISR 8, 1
NW_ISR 9
NW_ISR 10, 1
NW_ISR 11, 1
NW_ISR 12, 1
NW_ISR 13, 1
NW_ISR 14, 1
NW_ISR 15
NW_ISR 16
NW_ISR 17, 1
NW_ISR 18
NW_ISR 19
NW_ISR 20
NW_ISR 21, 1
NW_ISR 22
NW_ISR 23
NW_ISR 24
NW_ISR 25
NW_ISR 26
NW_ISR 27
NW_ISR 28
NW_ISR 29, 1
NW_ISR 30, 1
NW_ISR 31
.globl nw_isr_unexpected
nw_isr_unexpected:
    pushq $0
    pushq $255
nw_isr_common:
    cld
    pushq %rax
    pushq %rcx
    pushq %rdx
    pushq %rbx
    pushq %rbp
    pushq %rsi
    pushq %rdi
    pushq %r8
    pushq %r9
    pushq %r10
    pushq %r11
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    movq %rsp, %rcx
    andq $-16, %rsp
    subq $32, %rsp
    call nw_exception
    ud2
.section .rdata,"dr"
.globl nw_isr_table
nw_isr_table:
.irp n,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    .quad nw_isr_\n
.endr
