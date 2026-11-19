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
    for line in logs: 
        tokens = line.split()
        if len(tokens) !=  6:
            continue #-skip
        if not tokens[0].isdecimal() or int(tokens[0]) < 0:
            continue 
        
            # a and b
            # -> not a or not b
          
        
            
    
        print (tokens)
       
    pass
