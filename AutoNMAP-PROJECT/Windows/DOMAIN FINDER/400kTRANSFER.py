def process_file(input_file_path, output_file_path):
    max_lines = 400000
    extracted_lines = []

    # Read lines from the original file and store them in a list
    with open(input_file_path, 'r') as file:
        for i, line in enumerate(file):
            extracted_lines.append(line)
            if i + 1 == max_lines:
                break

    remaining_lines = []
    # Continue reading the remaining lines
    with open(input_file_path, 'r') as file:
        remaining_lines = file.readlines()[max_lines:]

    # Write the extracted lines to the new file
    with open(output_file_path, 'w') as file:
        file.writelines(extracted_lines)

    # Write the remaining lines back to the original file
    with open(input_file_path, 'w') as file:
        file.writelines(remaining_lines)


# Example usage
input_file = r"C:\Programming\#PythonScripts\NMAP-SCAN\Transfer\2023-11-19_URLS.txt"
output_file = r"C:\Programming\#PythonScripts\NMAP-SCAN\Transfer\urlsKB.txt"
process_file(input_file, output_file)
