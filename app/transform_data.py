import csv
import json

def transform_data(filename_in, filename_out):
    with open(filename_in, newline='') as csvfile:
        csv_dict = []
        headers = []
        spamreader = csv.reader(csvfile, delimiter=';')
        for index, row in enumerate(spamreader):
            row_dict = {}
            if index == 0:
                headers = row
            else:
                for index, header in enumerate(headers):
                    row_dict[header] = row[index]
                csv_dict.append(row_dict)
    with open(filename_out, 'w') as file_out:
        json.dump(csv_dict, file_out)


def main():
    set="8"
    transform_data(f'data/champions-{set}.csv', f'data/champions-{set}.json')
    transform_data(f'data/synergies-{set}.csv', f'data/synergies-{set}.json')


if __name__ == '__main__':
    main()