import re
import json

def read_datasets_from_file(file_path):
    print('FILE PATH: ', file_path)
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def format_datasets(raw_datasets, user_role, assistant_role, print_datasets=False):
    formatted_datasets = []
    datasets = re.split(r'\n(?=Dataset \d+:)', raw_datasets)
    if print_datasets:
        print('DATASETS: ', datasets)
    for dataset in datasets:
        if dataset.strip():
            formatted_dataset = format_conversation(dataset, user_role, assistant_role)
            if formatted_dataset:
                formatted_datasets.append(formatted_dataset)
    
    return formatted_datasets

def add_title(dataset, title, description):
    dataset.insert(0, {'title': title, 'description': description})
    return dataset

def dataset_to_conversation(dataset):
    # Original nested data
    nested_data = dataset

    # Flattening the nested structure into a single list
    flattened_list = []
    for pair in nested_data:
        for entry in pair:
         flattened_list.append({"role": entry["role"], "content": entry["content"]})

    # Output the flattened list
    response =json.dumps(flattened_list, indent=2)
    print (response)
    response  = json.loads(response)
    return response

def format_conversation(raw_conversation, user_role="User Input:", assistant_role="Assistant:"):
    #print('RAW CONVERSATION: ', raw_conversation)
    formatted_conversation = []
    sections = re.split(r'\n(?=Dataset|{}:|{}:)'.format(user_role, assistant_role), raw_conversation)
    
    user_content = ""
    assistant_content = ""
    
    for section in sections[1:]:  # Skip the dataset header
        section = section.strip()
        if section.startswith(user_role):
            if user_content:
                formatted_conversation.append({'role': 'user', 'content': user_content})
            user_content = section[len("User Input:"):].strip()
            assistant_content = ""
        elif section.startswith((assistant_role)):
            section_type = section.split(':', 1)[0]
            if assistant_content:
                formatted_conversation.append({'role': 'assistant', 'content': assistant_content})
            assistant_content = f"{section_type}:\n{section.split(':', 1)[1].strip()}"
    
    if user_content:
        formatted_conversation.append({'role': 'user', 'content': user_content})
    if assistant_content:
        formatted_conversation.append({'role': 'assistant', 'content': assistant_content})
    
    return formatted_conversation

# Example usage
if __name__ == "__main__":
    file_path = "datasets.txt"  # Replace with your actual file path
    raw_datasets = read_datasets_from_file(file_path)
    formatted_datasets = format_datasets(raw_datasets, "Assistant:")
    
    for i, dataset in enumerate(formatted_datasets, 1):
        print(f"Dataset {i}:")
        for message in dataset:
            print(f"Role: {message['role']}")
            print(f"Content: {message['content']}")
            print()
        print("---")
        print()