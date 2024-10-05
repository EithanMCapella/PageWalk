# PageWalk
A simplified PageWalk algorithm using the Extended Page Tables concept.

The application will take the following inputs from the command line:
CR3 Register => Will contain the base address of the Guest OS Page Tables
EPT PTR => Will contain the based address of the Hypervisor Page Page Tables
EPT Tables => CSV file that will contain all table entries, that will include Guest OS and Host OS.  The heading of each column is the address of the table.
Guest OS Virtual Address to be translated to a physical address.
The input file will be a comma-separated (csv) file with the following format

Sample run of the program:
python ./mypagewalk.py 0x535385a4871e43d1 0x6520e289eea2a5c8 tables.csv 0x0000EF0123456789
Expected Output: 0x1a49a56db789
