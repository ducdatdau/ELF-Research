import struct

# Read ULEB128 number from file and return integer number.
def read_uleb128(f):
    result = 0
    shift = 0
    while True:
        b = f.read(1)
        if not b:
            break
        byte = b[0]
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result

# Read a string from file
def read_cstring(f):
    chars = []
    while True:
        b = f.read(1)
        if not b or b == b'\x00':
            break
        chars.append(b)
    return b''.join(chars).decode('utf-8', errors='replace')

# Getting info from section .debug_info
def parse_debug_info_section(f, offset, size):
    print("\n=== Parsing .debug_info section ===")
    f.seek(offset)
    # DWARF Debug Info header in 1 Compile Unit (CU):
    #   - unit_length:   4 bytes
    #   - version:       2 bytes
    #   - debug_abbrev_offset: 4 bytes
    #   - address_size:  1 byte
    header_data = f.read(4 + 2 + 4 + 1)
    if len(header_data) < 11:
        print("Không đủ dữ liệu để đọc header của .debug_info")
        return
    unit_length, version, abbrev_offset, addr_size = struct.unpack("<IHIb", header_data)
    print("CU unit_length      :", unit_length)
    print("CU version          :", version)
    print("CU debug_abbrev_off :", abbrev_offset)
    print("CU address_size     :", addr_size)
    
    abbrev_code = read_uleb128(f)
    print("First DIE abbreviation code (ULEB128):", abbrev_code)

# Read section .debug_line header
def parse_debug_line_section(f, offset, size):
    print("\n=== Parsing .debug_line section ===")
    f.seek(offset)
    # .debug_line header: 
    #   - total_length:      4 bytes
    #   - version:           2 bytes
    #   - header_length:     4 bytes
    #   - min_inst_length:   1 byte
    #   - default_is_stmt:   1 byte
    #   - line_base:         1 byte (signed)
    #   - line_range:        1 byte
    #   - opcode_base:       1 byte
    header_data = f.read(15)
    if len(header_data) < 15:
        print("Không đủ dữ liệu để đọc header của .debug_line")
        return
    total_length, version, header_length, min_inst_length, default_is_stmt, line_base, line_range, opcode_base = struct.unpack("<IHIBBbBB", header_data)
    print("total_length    :", total_length)
    print("version         :", version)
    print("header_length   :", header_length)
    print("min_inst_length :", min_inst_length)
    print("default_is_stmt :", default_is_stmt)
    print("line_base       :", line_base)
    print("line_range      :", line_range)
    print("opcode_base     :", opcode_base)
    
with open("./sample_with_debug_flag", "rb") as f: 
    # READ ELF HEADER (first 64 bytes for 64-bit ELF)
    e_ident = f.read(16) 
    if e_ident[:4] != b"\x7fELF": 
        raise ValueError("Not an ELF file") 

    # Parse ELF class (32-bit or 64-bit)
    elf_class = e_ident[4]
    if elf_class == 1:
        elf_type = "ELF32"
        header_format = "<HHIIIIIHHHHHH"  # 32-bit ELF header structure
    elif elf_class == 2:
        elf_type = "ELF64"
        header_format = "<HHIQQQIHHHHHH"  # 64-bit ELF header structure
    else:
        raise ValueError("Unknown ELF class")
    
    elf_data = e_ident[5]
    if elf_data == 1:
        elf_data = "Little Edian"
    elif elf_data == 2:
        elf_data = "Big Edian"
    else:
        raise ValueError("Unknown ELF data")
    
    elf_version = e_ident[6]

    osabi_mapping = {
        0x00: "System V",
        0x01: "HP-UX",
        0x02: "NetBSD",
        0x03: "Linux",
        0x04: "GNU Hurd",
        0x06: "Solaris",
        0x07: "AIX",
        0x08: "IRIX",
        0x09: "FreeBSD",
        0x0A: "Tru64",
        0x0B: "Novell Modesto",
        0x0C: "OpenBSD",
        0x0D: "OpenVMS",
        0x0E: "NonStop Kernel",
        0x0F: "AROS",
        0x10: "FenixOS",
        0x11: "Nuxi CloudABI",
        0x12: "Stratus Technologies OpenVOS"
    }
    elf_osabi = e_ident[7] 
    osabi_name = osabi_mapping.get(elf_osabi)
        
    # Read the rest of the ELF header
    header_size = struct.calcsize(header_format)
    header = f.read(header_size)

    # Unpack ELF header
    fields = struct.unpack(header_format, header)

    print("ELF Header:")
    print("=" * 45)
    print(f"{'Class:':<35} {elf_type}")
    print(f"{'Data:':<35} {elf_data}")
    print(f"{'Version:':<35} {elf_version}")
    print(f"{'OS/ABI:':<35} {osabi_name}")

    header_info = {
        "Type:": fields[0],
        "Machine:": fields[1],
        "Version:": fields[2],
        "Entry point address:": fields[3],
        "Start of program headers:": fields[4],
        "Start of section headers:": fields[5],
        "Flags:": fields[6],
        "Size of this header:": fields[7],
        "Size of program headers:": fields[8],
        "Number of program headers:": fields[9],
        "Size of section headers:": fields[10],
        "Number of section headers:": fields[11],
        "Section header string table index:": fields[12],
    }

    # Print ELF Header information
    for key, value in header_info.items():
        print(f"{key:<35} {hex(value):<10}")

    # READ ELF SEGMENT
    ph_offset = fields[4]   # e_phoff: Start of program headers
    ph_entry_size = fields[8]  # e_phentsize: Size of each program header
    ph_num = fields[9]         # e_phnum: Number of program headers
    ph_entry_format = "<IIQQQQQQ"      # 64-bit Program Header

    print(f"\nProgram Headers (Offset: {ph_offset}, Entries: {ph_num}):")
    print(f"{'Type':<15} {'Offset':<10} {'VirtAddr':<18} {'PhysAddr':<18} {'FileSize':<10} {'MemSize':<10} {'Flags':<8} {'Align':<10}")
    print("=" * 100)

    for i in range(ph_num):
        entry_data = f.read(ph_entry_size)
        ph_fields = struct.unpack(ph_entry_format, entry_data)
        p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = ph_fields

        # Map p_type to readable names
        p_type_mapping = {
            0: "NULL",
            1: "LOAD",
            2: "DYNAMIC",
            3: "INTERP",
            4: "NOTE",
            5: "SHLIB",
            6: "PHDR",
            7: "TLS",
            0x6474e550: "GNU_EH_FRAME",
            0x6474e551: "GNU_STACK",
            0x6474e552: "GNU_RELRO"
        }
        p_type_name = p_type_mapping.get(p_type, "UNKNOWN")

        # Print program header details
        print(f"{p_type_name:<15} {hex(p_offset):<10} {hex(p_vaddr):<18} {hex(p_paddr):<18} {hex(p_filesz):<10} {hex(p_memsz):<10} {hex(p_flags):<8} {hex(p_align):<10}")
    
    # READ ELF SECTION 

    sh_offset = fields[5]       # e_shoff: Start of section headers
    sh_entry_size = fields[10]  # e_shentsize: Size of each section header
    sh_num = fields[11]         # e_shnum: Number of section headers
    sh_str_index = fields[12]   # e_shstrndx: Section header string table index

    if elf_class == 1:
        sh_format = "<IIIIIIIIII"   
    elif elf_class == 2:
        sh_format = "<IIQQQQIIQQ"   

    f.seek(sh_offset + sh_str_index * sh_entry_size)
    sh_str_hdr_data = f.read(sh_entry_size)
    sh_str_hdr = struct.unpack(sh_format, sh_str_hdr_data)

    shstrtab_offset = sh_str_hdr[4]
    shstrtab_size = sh_str_hdr[5]

    f.seek(shstrtab_offset)
    shstrtab = f.read(shstrtab_size)

    sections = {}
    f.seek(sh_offset)

    print(f"\nSection Headers (Offset: {sh_offset}, Entries: {sh_num}):")
    print("=" * 100)
    print(f"{'Index':<5} {'Name':<20} {'Type':<15} {'Address':<18} {'Offset':<10} {'Size':<10}")
    print("=" * 100)

    sht_mapping = {
        0: "NULL",
        1: "PROGBITS",
        2: "SYMTAB",
        3: "STRTAB",
        4: "RELA",
        5: "HASH",
        6: "DYNAMIC",
        7: "NOTE",
        8: "NOBITS",
        9: "REL",
        10: "SHLIB",
        11: "DYNSYM",
    }

    for i in range(sh_num):
        sh_data = f.read(sh_entry_size)
        sh_fields = struct.unpack(sh_format, sh_data)
        sh_name_offset = sh_fields[0]  
        sh_type = sh_fields[1]
        sh_addr = sh_fields[3]
        sh_off = sh_fields[4]
        sh_size = sh_fields[5]

        end = shstrtab.find(b'\x00', sh_name_offset)
        if end != -1:
            section_name = shstrtab[sh_name_offset:end].decode("utf-8", errors="replace")
        else:
            section_name = ""

        sh_type_name = sht_mapping.get(sh_type, hex(sh_type))
        
        print(f"{i:<5} {section_name:<20} {sh_type_name:<15} {hex(sh_addr):<18} {hex(sh_off):<10} {hex(sh_size):<10}")
        sections[section_name] = (sh_off, sh_size)
    
    if ".debug_info" in sections:
        off, size = sections[".debug_info"]
        parse_debug_info_section(f, off, size)
    else:
        print("\nKhông tìm thấy section .debug_info")
    
    if ".debug_line" in sections:
        off, size = sections[".debug_line"]
        parse_debug_line_section(f, off, size)
    else:
        print("\nKhông tìm thấy section .debug_line")