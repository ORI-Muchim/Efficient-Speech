def process_file(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    processed_lines = ['|'.join(line.strip().split('|')[:3]) + '\n' for line in lines]

    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.writelines(processed_lines)


input_file_path = 'val.txt'
output_file_path = 'train2.txt'
process_file(input_file_path, output_file_path)
