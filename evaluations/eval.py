import csv

# Define the path to the CSV file
csv_file_path = "/Users/dingchaozhang/Documents/Work/thrackle/chatbotHealthCare/chatbot-real-world-backend/evaluations/llamaindextestset.csv"

# Open the CSV file and read the second row
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
    csv_reader = csv.reader(csvfile)
    next(csv_reader)  # Skip the first row
    second_row = next(csv_reader)  # Read the second row

# Print the second row
print("Second row of the CSV file:")
print(second_row)