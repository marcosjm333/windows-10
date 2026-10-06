.text
.globl nw_abi_probe
#ifdef _WIN32
.seh_proc nw_abi_probe
#endif
nw_abi_probe:
#ifdef _WIN32
    .seh_endprologue
#endif
    movq %rsp, %rax
    andq $15, %rax
    cmpq $8, %rax
    jne 1f
    movq %rcx, 8(%rsp)
    movq %rdx, 16(%rsp)
    movq %r8, 24(%rsp)
    movq %r9, 32(%rsp)
    leaq (%rcx,%rdx,2), %rax
    leaq (%r8,%r8,2), %r10
    addq %r10, %rax
    leaq (%rax,%r9,4), %rax
    movq 40(%rsp), %r10
    leaq (%r10,%r10,4), %r10
    addq %r10, %rax
    movq 48(%rsp), %r10
    imulq $6, %r10, %r10
    addq %r10, %rax
    retq
1:
    xorq %rax, %rax
    retq
#ifdef _WIN32
.seh_endproc
#endif

.text
.globl nw_abi_preserved
#ifdef _WIN32
.seh_proc nw_abi_preserved
#endif
nw_abi_preserved:
    pushq %rbp
#ifdef _WIN32
    .seh_pushreg %rbp
#endif
    pushq %rbx
#ifdef _WIN32
    .seh_pushreg %rbx
#endif
    pushq %rdi
#ifdef _WIN32
    .seh_pushreg %rdi
#endif
    pushq %rsi
#ifdef _WIN32
    .seh_pushreg %rsi
#endif
    pushq %r12
#ifdef _WIN32
    .seh_pushreg %r12
#endif
    pushq %r13
#ifdef _WIN32
    .seh_pushreg %r13
#endif
    pushq %r14
#ifdef _WIN32
    .seh_pushreg %r14
#endif
    pushq %r15
#ifdef _WIN32
    .seh_pushreg %r15
#endif
    subq $56, %rsp
#ifdef _WIN32
    .seh_stackalloc 56
    .seh_endprologue
#endif
    movq $0x1111, %rbp
    movq $0x2222, %rbx
    movq $0x3333, %rdi
    movq $0x4444, %rsi
    movq $0x5555, %r12
    movq $0x6666, %r13
    movq $0x7777, %r14
    movq $0x8888, %r15
    movq $1, %rcx
    movq $2, %rdx
    movq $3, %r8
    movq $4, %r9
    movq $5, 32(%rsp)
    movq $6, 40(%rsp)
    call nw_abi_callee
    cmpq $91, %rax
    jne 2f
    cmpq $0x1111, %rbp
    jne 2f
    cmpq $0x2222, %rbx
    jne 2f
    cmpq $0x3333, %rdi
    jne 2f
    cmpq $0x4444, %rsi
    jne 2f
    cmpq $0x5555, %r12
    jne 2f
    cmpq $0x6666, %r13
    jne 2f
    cmpq $0x7777, %r14
    jne 2f
    cmpq $0x8888, %r15
    jne 2f
    movq $1, %rax
    jmp 3f
2:
    xorq %rax, %rax
3:
    addq $56, %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rsi
    popq %rdi
    popq %rbx
    popq %rbp
    retq
#ifdef _WIN32
.seh_endproc
#else
.section .note.GNU-stack,"",@progbits
#endif
