import pandas as pd

def organize_data():
    unique_classes = {'Title': [], 'Mnemonic': [], 'Number': []}  # Initialize dictionary with lists
    class_df = pd.read_csv('searchData_all.csv')
    class_data = class_df.loc[:, ['Mnemonic', 'Number', 'Title']]
    
    # Iterate through rows
    for _, row in class_data.iterrows():  # Use `row` directly
        if row['Title'] not in unique_classes['Title']:
            unique_classes['Title'].append(row['Title'])  # Add unique Title
            unique_classes['Mnemonic'].append(row['Mnemonic'])  # Add corresponding Mnemonic
            unique_classes['Number'].append(row['Number'])  # Add corresponding Number

    # Print the resulting dictionary
    unique_classes_df = pd.DataFrame(unique_classes)
    unique_classes_df.to_json('unique_classes.json', orient='records')

organize_data()


# TODO
# Organize class data
# import to frontend
# Update assistant to return json
# Improve UI
