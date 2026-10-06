# Concurrency tests

Status is maintained in the central compatibility database.

Native C workers check unique live PFN ownership independently of database locking. Kernel SMP remains untested.

Implementation requires the contracts, ownership, locking, failure matrix and tests
in the project engineering process. See the central architecture and compatibility
documents for dependencies. This directory does not provide success-returning stubs.
