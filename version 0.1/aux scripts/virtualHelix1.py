
id = 18
number = 18
position = 6210

px = 345

outfile = open("C:/Development/unf/version 0.1/virtualHelices1.txt", "w")

while id <= 41:
	id = id + 1
	number = id
	position = position + 345
	cell = '"%i": {"number": %i,"position": "%i.000000,27712.812921,29500.000000","type": -1,"left": -1,"right": -1},' % (id, number, position)
	outfile.write(cell)


outfile.close()