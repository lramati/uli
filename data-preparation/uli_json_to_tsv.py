from os import listdir
from os.path import isfile, join
import json
import csv


def json_to_tsv(top_library_directory, output_file_name):

    # out = open(output_file_name, "w")
    csv_file = open(output_file_name, mode="w")
    headers_added = False

    dirs = listdir(top_library_directory)
    print(dirs)
    count = 0
    correct = 0
    for dir in dirs:
        try:
            subdir = join(top_library_directory,dir)
            for file in listdir(subdir):
                file_name = join(subdir,file)
                print(file_name)
                count += 1
                f = open(file_name)
                c = f.read()
                j = json.loads(c)

                if not headers_added:
                    fieldnames = list(j.keys())
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()
                    #for key in j.keys():
                        #out.write(f"{key}\t")
                    #out.write("\n")
                    headers_added = True

                csv_row = dict()
                for key in j.keys():
                    if type(j[key]) == str:
                        value = j[key]
                        #out.write(f"{j[key]}\t")
                    else:
                        value = '$'.join(j[key])
                        #out.write(f"{'$'.join(j[key])}\t")
                    csv_row[key] = value
                #out.write("\n")

                writer.writerow(csv_row)

                f.close()

                correct += 1
        except:
            pass
        print()

    #out.close()
    csv_file.close()

    print(f"{correct}/{count}")


if __name__ == '__main__':

    json_to_tsv("/Volumes/ExtMac/uli/library", "/Volumes/ExtMac/uli/lad.csv")
