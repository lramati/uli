__author__ = 'yaeln'
import os
import json
import codecs
import re
import string
from collections import defaultdict

from nltk.metrics import *

# postgres://nijyhwbbisppog:92650cb3080427a26d7d1111444864a9dec99d8fdd96482070907dcb8d9f763b@ec2-54-228-252-67.eu-west-1.compute.amazonaws.com:5432/db9mo7o2hvb2a0
# heroku pg:psql postgresql-metric-68589 --app yiddish
#regex = re.compile('[%s]' % re.escape(string.punctuation))

root_path = "/Volumes/ExtMac/uli/"

library_path=root_path+"/library//"
data_path=root_path
test_path=root_path
error_log=root_path+"/error_log"
books_file = root_path+"/books.csv"

library = {}
libraryISBN = {}
libraryTITLE = {}
conflicts = defaultdict(list)

booksFile = codecs.open(books_file, 'wb', encoding="utf-8")

bookCounter = 0   ##this will use to identify the books that are considered unique
enrtiesCounter = 0
#each line in marc file is serial_num\tcode\tlang\tcontent


def getCode(elt):
    # print("code is " + elt.split(' ')[0])
    return elt.split(' ')[0]


def getValue(elt):
    return ' '.join(elt.split(' ')[4:]).replace("\\","")


def getTitle(elt):
    title = ' '.join(elt.split()[2:]).rstrip(' .,;\'\"[]:').split('/$$c')
    return title


def getTitle(elt):
    title = ' '.join(elt.split()[2:]).rstrip(' .,;\'\"[]:')
    #print title
    return title


def isbnOfBookInLib(title, lib):
    books = lib.values()
    for book in books:
        if book['title'] == title:
            return(book['isbn'])


def compareFeatures(f1, f2):
    # relaxed features, case , no nikud pisuk
    #print f1
    #f1=''.join([letter.lower() for letter in f1 if letter.isalnum() or letter == ' '])
    f1=''.join([letter.lower() for letter in f1 if letter.isalnum()]) # or letter == ' '])
    #print f1
    #f2=''.join([letter.lower() for letter in f2 if letter.isalnum() or letter == ' '])
    f2=''.join([letter.lower() for letter in f2 if letter.isalnum()]) #or letter == ' '])
    #print f2
    return (f1 == f2)


def mergeBooks(book1,book2):

    for feature,value in book1.items():
        if type(value) is list:
            if feature is 'subjects':
                book1[feature].extend(book2[feature])
            else:
                if value and book2[feature]:
                    book1[feature]=list(set(value).union(set(book2[feature])))
                else:
                    book1[feature].extend(book2[feature])

        #elif value != book2[feature]:
        elif not compareFeatures(value, book2[feature]):
            if not value:
                book1[feature] = book2[feature]
            elif not book2[feature]:
                continue
            else:
                if not feature == 'litForm':
                    book1['conflicts'].append([feature, value, book2[feature]])
                    conflicts[(book1['title'], book1['isbn'])].append([feature, value, book2[feature]])

    return(book1)


def makebook():
    return ({"isbn": "",
             "year": "",
             "altYear": "",
             "location": "",
             "lang": "",
             "litForm": "",
             "serial": [],
             "title": "",
             "oclc": "",
             "fulltitle": "",
             "altTitle": "",
             "volume": [],
             "volName": "",
             "subtitle": [],
             "format": "",
             "serialNum": [],
             "editors": [],
             "subjects": [],
             "authors": [],
             "titleAdditions": [],
             "authorDates": [],
             "language": "",
             "sourceLanguage":"",
             "publisher":[],
             "publisherAddress":[],
             "date":[],
             "edition":"",
             "series" : [],
             "pages":[],
             "addendum":[],
             "size":[],
             "comments":[],
             "dewey":"",
             "trans_eds_ills":[],
             "uid" : [],
             "link": [],
             "conflicts": []})


def bookInstance(book):
    bookInst= makebook()
    fulltitle = ""
    for elt in book:
        #elt = elt.replace(">>","").replace("<<",'')
        code = getCode(elt)
        if code == 'FMT':
            bookInst['format']= getValue(elt).strip()

        elif code == '008':
            code008 = getValue(elt)
            bookInst['year'] = code008[7:11] #pub year
            if code008[11:15] != "^^^^":
                bookInst['altYear'] = code008[11:15]
            bookInst['location'] = code008[15:18].strip("^")
            bookInst['lang'] = code008[35:38]
            if len(code008)>33:

                bookInst['litForm'] = code008[33]
            #if len(code008)>33:
            #    litForm = code008[33]
            #    print litForm
            #    if litForm == '0':
            #        bookInst['litForm'] = "nonfiction"
            #    elif litForm == '1':
            #        print "fiction"
            #        bookInst['litForm'] = "fiction"
            #    else:
            #        bookInst['litForm'] = "other"
        elif code.startswith('041'): ##language
            language = getValue(elt)[3:].split('$$')
            if len(language) > 1:
                bookInst['sourceLanguage'] = language[1][1:]
                bookInst['language'] = language[0]
            else:
                bookInst['language'] = language[0]

        elif code == '001':
            bookInst['serialNum'].append(getValue(elt))
        elif code == '035':
            bookInst['oclc'] = elt.split(' ')[-1].rstrip(" \t,.;()/\'\"-:").split(")")[-1]
        elif code == '084':  # dewey
            bookInst['dewey']=getValue(elt)[3:]
        elif code == '1001':
            authorInfo = ' '.join(elt.split(' ')[3:]).split('$$d')
            authors = authorInfo[0][3:].rstrip(" \t,.;()/\'\"-:").replace(",", "").split("$$")[0]

            bookInst['authors'].append(authors)
            if len(authorInfo) > 1:
                bookInst['authorDates'].append(authorInfo[1].rstrip(" \t,.;()/\'\"-:"))
        elif code.startswith('245'):  # 24501 or code == '24500':
            title = getTitle(elt.replace(">>", "").replace("<<", '')).split('$$')[1:]
            if len(title)>0:
                ttitle = title[0]
            else:
                ttitle = str(title)
            subtitle = ""
            #print title[0],
            for elet in title:
                #print elet
                beginner = elet[0]
                #print beginner
                if beginner == 'a':
                    ttitle = elet[1:].rstrip(" \t,.;([])/\'\"-:")

                    bookInst['title'] = ttitle
                    #print ttitle

                elif beginner == 'b':
                    subtitle = elet[1:].rstrip(" \t,.;([])/\'\"-:")
                    bookInst['subtitle'].append(subtitle)
                    #print subtitle
                elif beginner == 'n':
                    bookInst['volume'] = elet[1:].rstrip(" /\t,.;([])\'\"-:")
                elif beginner == 'p':
                    bookInst['volName'] = elet[1:].rstrip(" /\t,.;([])\'\"-:")
                elif beginner == 'c':
                    bookInst['titleAdditions'].append(elet[1:].rstrip(" /\t,.;([])\'\"-:"))



            bookInst['fulltitle'] = ttitle + " " + subtitle


        elif code.startswith('246'):  # 24633:
            bookInst['altTitle'] = getValue(elt.replace(">>","").replace("<<",'')).rstrip(" \t,.;()\'\"-:")

        elif code.startswith("6"):#code == '650' or 651 or code=='695' or code=='6000' or '60014'':
            subject = ' '.join(elt.replace(">>","").replace("<<",'').split(' ')[3:]).rstrip('.,/;:[]').split('$$')[1:]
            processed_subject = ""

            for s in subject:
                first = s[0]
                rest = s[1:]

                if first == 'a':
                    processed_subject = rest
                elif first == 'x': #sub
                    processed_subject = processed_subject + " **sub: " + rest
                elif first == 'y':
                    processed_subject = processed_subject + " **period: " + rest
                elif first == 'd':
                    processed_subject = processed_subject + " **date: " + rest
                elif first == 'z':
                    processed_subject = processed_subject + " **location: " + rest
                elif first == ('b' or 'c'):
                    processed_subject += " " + rest
                else:
                    processed_subject = processed_subject + " **" + first + ": " + rest

            if processed_subject:
                bookInst['subjects'].append(processed_subject)

        elif code == '020':
            bookInst['isbn'] = getValue(elt).split(' ')[0][3:].split("$$")[0] #some foriegn language books has $#c
        elif code == '992':

            bookInst['link'].append(getValue(elt)[3:].split("$$")[0])
        elif code == "260":
            publisher = getValue(elt.replace(">>","").replace("<<",'')).rstrip(' ,.;-/:[]').rsplit('$$')[1:]
            bookInst['publisherAddress'].extend([address[1:].rstrip(",][/ .:") for address in publisher if address.startswith('a')])
            bookInst['publisher'].extend([pub[1:].rstrip(",][ .:") for pub in publisher if pub.startswith('b')])
            bookInst['date'].extend([date[1:].rstrip(", ][.:") for date in publisher if date.startswith('c')])
        elif code == "300":
            physical = getValue(elt).rstrip(' ,.;-/:[]').rsplit('$$')[1:]
            bookInst['pages'].extend([address[1:].rstrip(",][/ .:;") for address in physical if address.startswith('a')])
            bookInst['addendum'].extend([pub[1:].rstrip(",][ ;.:") for pub in physical if pub.startswith('b')])
            bookInst['size'].extend([date[1:].rstrip(", ][.:;") for date in physical if date.startswith('c')])
        elif code.startswith("5"):
            bookInst['comments'].append(code + " " + getValue(elt).rstrip(' ,.;-/:[]')[3:])
        elif code.startswith("7"):
            bookInst['trans_eds_ills'].append(" ".join([p[1:] for p in elt.replace(">>","").replace("<<",'').split('$$')[1:]]))
        elif code.startswith("4") or code == "830": #series info
            #print elt
            bookInst['series'].append(' '.join(elt.replace(">>","").replace("<<",'').split('$$')[1:]).replace("\\","")[1:])
        elif code.startswith("250"):  # edition
            bookInst['edition'] = getValue(elt)[3:].strip()


    return(bookInst)


def makeDirForLetter(letter):
    dir = os.path.join(library_path,letter + "_dir")
    if not os.path.exists(dir):
        os.makedirs(dir)
    return(dir)


def first_letter(name):

    return name[0:2]


def writeBook(bookInst, uniqueID):
    letter = first_letter(uniqueID.strip())
    dir=makeDirForLetter(letter)
    try:
        with codecs.open(os.path.join(dir, uniqueID), 'w', encoding='utf-8') as f:
            f.write(json.dumps(bookInst, indent=4, ensure_ascii=False, encoding="utf-8"))
    except:
        with codecs.open(error_log, 'a', encoding='utf-8') as e:
            e.write("Book " + bookInst['title'] + " uniqueID " + uniqueID + "\n")


def readBook(uniqueID):
    dir = os.path.join(library_path, first_letter(uniqueID)+"_dir")
    book=makebook()
    try:
        with codecs.open(os.path.join(dir, uniqueID), 'r', encoding='utf-8') as f:
            book=json.load(f)
    except:
        with codecs.open(error_log, 'a', encoding='utf-8') as e:
            e.write("Book  uniqueID " + uniqueID + "\n")
    return(book)


def inLibrary(isbn,title,subtitle,oclc,author):
    return


def removePunct(text):
    for ch in [",", ",", "(", ")", "/",  "]", "[", "*", "+", "%", ">", "<", "=", "&", "?", "!", ":", ";", "\"", "\'"]:
        if ch in text:
            text = text.replace(ch, "")
    return text


def closeEnoughTitles(title, list_of_titles):

    for title1 in list_of_titles:
        if edit_distance(title, title1) < 3:
            return title1
    return False


def addBookToLib(bookInst):  # book is a dictionary
    global booksFile
    global enrtiesCounter
    differentBook = False
    bookISBN = bookInst['isbn']


    bookTitle = re.sub("\s\s+", " ", removePunct(bookInst['title'].replace("-", " ")))


    bookYear = bookInst['year']

    bookLocation = bookInst['location']
    if bookLocation.startswith("xx") or bookLocation.startswith("uu") or bookLocation.startswith("||"):
        bookLocation = "is"

    bookSubtitle = bookInst['subtitle']
    if bookSubtitle:
        bookSubtitle = bookSubtitle[0]
    else:
        bookSubtitle = ""

    bookOCLC = bookInst['oclc']

    if bookInst['authors']:
        bookAuthors=bookInst['authors'][0].replace(",", "").strip()
    else:
        bookAuthors=""

    details = "&&".join([bookTitle, bookSubtitle, bookYear, bookLocation, bookAuthors, bookOCLC, bookISBN])
    uniqueIdentifier = "**".join([bookTitle, bookYear, bookLocation])

    #close_enough_title = closeEnoughTitles(bookTitle, library.keys())
    #print close_enough_title
    #if close_enough_title:


    if bookTitle in library.keys():
        for book in library[bookTitle]:
        #for book in library[close_enough_title]:
          #while not differentBook:
            if book == uniqueIdentifier:

                libBook = readBook(book)

                if bookISBN and libBook['isbn'] == bookISBN:
                    libBook = mergeBooks(libBook, bookInst)
                    writeBook(libBook, book)
                    booksFile.write(details+"&&"+book+"\n")
                    return


                if bookOCLC and libBook['oclc'] == bookOCLC:
                        libBook = mergeBooks(libBook, bookInst)
                        writeBook(libBook,book)
                        booksFile.write(details+"&&"+book+"\n")
                        return
                libSub = libBook['subtitle']
                if libSub:
                    libSub = libSub[0]
                else:
                    libSub = ""

                minString = min(len(bookSubtitle), len(libSub))
                if minString > 0:


                    #print str(minString), " ", bookSubtitle, " ", libSub
                    if edit_distance(bookSubtitle[:minString], libSub[:minString]) < 5:
                            libBook = mergeBooks(libBook, bookInst)
                            #print ".", bookTitle,
                            writeBook(libBook,book)
                            booksFile.write(details+"&&"+book+"\n")
                            return
                    else:
                        #print "+", bookTitle
                        differentBook = True

                if not differentBook:
                    if libBook['authors'] and  edit_distance(libBook['authors'][0].replace(",", "").strip(), bookAuthors) < 4:
                        #print libBook['authors'][0], " ", bookAuthors
                        libBook = mergeBooks(libBook, bookInst)
                        writeBook(libBook,book)
                        booksFile.write(details+"&&"+book+"\n")
                        return

                    if libBook['titleAdditions'] and bookInst['titleAdditions'] and edit_distance(libBook['titleAdditions'][0].strip(), bookInst['titleAdditions'][0].strip()) < 8:
                        libBook = mergeBooks(libBook, bookInst)
                        writeBook(libBook,book)
                        booksFile.write(details+"&&"+book+"\n")
                        return

                    if not bookAuthors or not libBook['authors']:
                        libBook = mergeBooks(libBook, bookInst)
                        writeBook(libBook,book)
                        booksFile.write(details+"&&"+book+"\n")
                        return
                    if not bookInst['titleAdditions'] or libBook['titleAdditions']:
                        libBook = mergeBooks(libBook, bookInst)
                        writeBook(libBook,book)
                        booksFile.write(details+"&&"+book+"\n")
                        return

                differentBook = True
        if differentBook:
                #print 'yet a different book'

                newRecord = uniqueIdentifier + str(len(library[bookTitle]))
                library[bookTitle].append(newRecord)
                writeBook(bookInst, newRecord)
                booksFile.write(details+"&&"+newRecord+"\n")
                enrtiesCounter += 1



    else:
        enrtiesCounter += 1
        library[bookTitle] = [uniqueIdentifier]
        writeBook(bookInst, uniqueIdentifier)
        booksFile.write(details+"&&"+uniqueIdentifier+"\n")


if __name__ == '__main__':

    newRecord=True
    thisBook=[]
    currentBook = dict()
    #currentBook['FMT']='BK'
    allBooks = {}
    library ={}
    bookCounter = 0

    languages = dict()
    #
    #with codecs.open(os.path.join(data_path, "all.uli.marc"), 'rb', encoding="utf-8") as fh:
    #with codecs.open(os.path.join(test_path, "sample.marc"), 'rb', encoding="utf-8") as fh:
    with codecs.open(os.path.join(data_path, "doc.seqa"), 'rb',encoding="utf-8") as fh:

        booksFile = codecs.open(books_file, 'wb', encoding="utf-8")

        for line in fh: #must make a record from each field
            try:
                lineElts =line.split(' ')
                if newRecord:
                    bookSerial = lineElts[0]
                    #print(bookSerial)
                    thisBook.append(line[10:].rstrip('\n'))
                    newRecord=False

                elif bookSerial == lineElts[0]: #not a new book
                    thisBook.append(line[10:].rstrip('\n'))

                elif bookSerial is not lineElts[0]: #new book

                    bookSerial = lineElts[0]
                    newRecord=True
                    ##main work is done here:
                    book = bookInstance(thisBook)
                    #print book['language']
                    if book and book['format'] == 'BK': #update list of books
                        #if book['language'] == 'heb' and book['format'] == 'BK':
                        if book['lang'] not in languages:
                            languages[book['lang']] = 1
                        else:
                            languages[book['lang']] += 1
                        if book['lang']=='lad':
                            #print book['fulltitle']
                            addBookToLib(book)

                        bookCounter += 1
                        if bookCounter % 1000 == 0:
                            print str(bookCounter), " ",
                            print "("+str(enrtiesCounter) + ")" + " "

                    thisBook=[line[10:].rstrip('\n')]
                    #print '.',
            except Exception as err:
                print '---'
                print str(err)
                print line
                print '---'


    #data=json.dumps(allBooks, indent=4, ensure_ascii=False)
    #print "writing to file now"

    #output= codecs.open('//Users//yaeln//Dropbox//digital humanities//uli//books.json', 'w',encoding="utf-8")

    print languages

    isbnFile = root_path + 'booksISBN.json'
    titlesFile = root_path + 'booksTITLES.json'
    conflictsFile = root_path + 'booksConflicts.json'

    with codecs.open(isbnFile, 'w', encoding='utf-8') as f:
        f.write(json.dumps(library, indent=4, ensure_ascii=False, encoding="utf-8"))


    #with codecs.open(titlesFile, 'w', encoding='utf-8') as f:
    #    f.write(json.dumps(libraryTITLE, indent=4, ensure_ascii=False, encoding="utf-8"))

    with codecs.open(conflictsFile, 'w', encoding='utf-8') as f:

        f.write(json.dumps(conflicts.items(), indent=4, ensure_ascii=False, encoding="utf-8"))

    print "Overall processed ", str(bookCounter), " Books and ", enrtiesCounter, " unique titles."

    print languages

    #with io.open('//Users//yaeln//Dropbox//digital humanities//uli//books.json', 'w', encoding="utf8") as json_file:
    #   json.dump(allBooks, json_file, ensure_ascii=False, encoding="utf8")




