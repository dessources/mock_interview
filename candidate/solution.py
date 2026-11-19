from __future__ import annotations



def count_dropped_bytes(logs: list[str]) -> dict[str, int]:
    drop_ips = {}
     
    for item in logs: 
        output = item.split()
        action = output[4].split("=")[1]
#         print (action)
       
        if action == "DROP":
            ip = output[1].split("=")[1]
            byte = output[5].split("=")[1]
            """
            dict = {
             
            }
            
            dict["192.168.1.1"] += 1200
            """
            if ip in drop_ips:
                drop_ips[ip] += int(byte) #drop_ips[ip] = int(byte) + drop_ips[ip]
            else:
                drop_ips[ip] = int(byte)  
    """
    Parse well-formed Azure NSG flow logs and return a dictionary mapping
    each source IP with at least one DROP event to its total dropped bytes.

    Args:
        logs: List of valid, well-formed log strings.

    Returns:
        Dict mapping src_ip -> total_dropped_bytes (for ACTION=DROP lines only).
    """
    # TODO: Write your Part 1 implementation here
    return drop_ips


# ============================================================================
# PART 2: Strict Telemetry Validation & Out-of-Order Field Parsing
# ============================================================================

def count_valid_dropped_bytes(logs: list[str]) -> dict[str, int]:
    """
    Strictly validate raw NSG flow logs (ignoring malformed IPs, ports,
    actions, negative values, duplicate/missing keys, and handling shuffled
    KEY=VALUE fields) and return {src_ip: total_dropped_bytes} for valid
    ACTION=DROP lines.
    """
    # TODO: Write your Part 2 implementation here
    valid_keys = ["SRC", "PORT", "ACTION", "DST", "BYTES"]
    drop_ips = {}
    for line in logs:
        
        tokens = line.split()
        print(tokens)
        if len(tokens) !=  6:
            continue #-skip
        
        if not tokens[0].isdecimal() or int(tokens[0]) < 0:
            continue
     
        props = {}
        for token in tokens:
            parts = token.split("=")
            if len(parts) == 2:
                props[parts[0]] = parts[1]
                

        if not all([True if key in props else False for key in valid_keys]):
            continue
        
        valid_ip_count = 0
        for key in ["SRC", "DST"]:
            octets = props[key].split(".")
      
            parts_ok = len(octets) == 4
            no_leading_0 = all([True if octet[0] != "0" or len(octet) == 1 else False for octet in octets])
            in_range = all([True if 0 <= int(octet) <= 255 else False for octet in octets ])
 

            if not parts_ok or not no_leading_0 or not in_range:
                break
            valid_ip_count +=1
       
        if valid_ip_count != 2:
            continue
       
        if not props["PORT"].isdecimal() or not (1 <= int(props["PORT"]) <= 65535):
            continue
            
        if props["ACTION"] not in ["ALLOW", "DROP"]:
            continue
        
        if not props["BYTES"].isdecimal() or int(props["BYTES"]) < 0:
            continue
        
        
        if props["ACTION"] == "DROP":
            ip = props["SRC"]
            byte = int(props["BYTES"])
          
            if ip in drop_ips:
                drop_ips[ip] += int(byte) #drop_ips[ip] = int(byte) + drop_ips[ip]
            else:
                drop_ips[ip] = int(byte)
    
    return drop_ips
       
  
