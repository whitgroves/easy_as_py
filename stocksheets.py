# This a script to pull a file from the NSE website for Indian stock values.
# The data will be processed and exported into an excel file with today's top 
# movers and heavily traded stocks.
import urllib.request as urlreq
import os
from datetime import date
import zipfile
import csv
import xlsxwriter

# The original example used a hard-coded date, but this will determine the 
# current date programmatically and configure it for the host's naming scheme.
year = str(date.today().year)
month = date.today().strftime('%b').upper()
day = str(date.today().day)
baseFileName = 'cm{0}{1}{2}bhav'.format(day, month, year)
fileUrl = 'https://www.nseindia.com/content/historical/EQUITIES/'
fileUrl += '{0}/{1}/{2}.csv.zip'.format(year, month, baseFileName)

# dataPath denotes the local folder to extract the zip file into.
# If this path doesn't exist yet, a new folder will be created with that name.
dataPath = 'stockdata'
if not os.path.isdir(dataPath):
	os.makedirs(dataPath)

# zipPath is the file where the downloaded .zip will be stored.
zipPath = '{0}\\{1}.csv.zip'.format(dataPath, baseFileName)

# NSE uses script blockers to prevent this type of scraping. This can be 
# bypassed by spoofing a browser header with the request.
header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
          'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Charset':'ISO-8859-1;utf-8;q=0.7,*;q=0.3',
          'Accept-Encoding':'none',
          'Accept-Language':'en-US,en;q=0.8',
          'Connection':'keep-alive'}
webRequest = urlreq.Request(fileUrl, headers=header)

# The following is wrapped in a try block in case we get an HTTPError.
try:
	page = urlreq.urlopen(webRequest)
	content = page.read()
	output = open(zipPath, 'wb')
	output.write(bytearray(content))
	output.close()
except urlreq.HTTPError as e:
	print(e.fp.read())
	print('There was an error in downloading the zip file at',fileUrl)

if os.path.exists(zipPath):
	print('Found zip file, processing...')
	extractedFiles = [] # An array is used in case multiple files are found.
	fh = open(zipPath, 'rb')
	zipHandler = zipfile.ZipFile(fh)
	for filename in zipHandler.namelist():
		zipHandler.extract(filename, dataPath)
		extractedPath = dataPath + '\\' + filename
		extractedFiles.append(extractedPath)
		print('Extracted', filename, 'from zipfile to', extractedPath)
	print('Extracted',str(len(extractedFiles)),'file(s) from zip archive.')

# There should only be one extracted file, but just in case, loop through.
for fileName in extractedFiles:
	lineNum = 0
	stockData = []
	# with is used so the file will be automatically closed after parsing.
	with open(fileName, 'r') as csvfile:
		# quotechar is specified in case of internal lists, which are enclosed
		# with double quotes (")
		lineReader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in lineReader:
			lineNum += 1
			# The first row is the header, and should be skipped.
			if lineNum == 1:
				print('File opened. Parsing lines...')
				continue
			# We're looking for specific columns based on their values:
			# 0 - Stock ticker
			# 5 - Last closing price
			# 7 - Yesterday's close
			# 9 - Traded value in Rupees
			symbol = row[0]
			close = row[5]
			prevClose = row[7]
			tradedQty = row[9]
			pctChange = float(close)/float(prevClose) - 1
			stockInfo = [symbol, pctChange, float(tradedQty)]
			stockData.append(stockInfo)
			print(symbol, '{:,.1f}'.format(float(tradedQty)/1e6),'M INR',
				'{:,.1f}'.format(pctChange * 100),'%')
		print('Done parsing contents, closing file...')
	print('Processed info for',str(lineNum),'stocks in',fileName)
	
# Sort the data by percent change and traded quantity.
# The sorted keyword can organize an iterable based on a key.
stockDataSortedByPct = sorted(stockData, key=lambda x:x[1], reverse=True)
stockDataSortedByQty = sorted(stockData, key=lambda x:x[2], reverse=True)

excelPath = '{0}\\{1}.xlsx'.format(dataPath, baseFileName)
workbook = xlsxwriter.Workbook(excelPath)
pctWorksheet = workbook.add_worksheet('Top 5 (By Percent Traded)')
qtyWorksheet = workbook.add_worksheet('Top 5 (By Quantity Traded)')
worksheets = { pctWorksheet : stockDataSortedByPct,
				qtyWorksheet : stockDataSortedByQty }

for worksheet in worksheets.keys():
	# The first row consists of column headers for the data.
	worksheet.write_row('A1', ['Top Traded Stocks'])
	worksheet.write_row('A2', ['Stock', '% Change', 'Value Traded (INR)'])
	
	# Only the top 5 need to be extraced (for simplicity)
	for lineNum in range(5):
		lineToWrite = worksheets[worksheet][lineNum]
		worksheet.write_row('A' + str(lineNum + 3), lineToWrite)
	
workbook.close()