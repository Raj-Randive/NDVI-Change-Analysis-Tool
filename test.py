def extract_year(filename):
    """Extracts the year from the filename in the format 'YYYY'."""
    # Split filename by underscores to isolate date sections
    parts = filename.split('_')
    
    # Look for sections that start with 'YYYY'
    for part in parts:
        if len(part) >= 4 and part[:4].isdigit():
            year = part[:4]  # Extract the first four digits
            return year
    return None

# Test the function
print(extract_year("2024-06-05-00_00_2024-06-05-23_59_Sentinel-2_L2A_B05_(Raw)"))
