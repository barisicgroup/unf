id = 97
number = 15
position = 5175

px = 345

outfile = open("C:/Development/unf/version 0.1/virtualHelix3.txt", "w")

while number < 41:
	id = id + 1
	number = number + 1
	position = position + 345
	cell = '"%i": {"number": %i,"position": "%i.000000,29444.863729,30500.000000","type": -1,"left": -1,"right": -1},' % (id, number, position)
	outfile.write(cell)


outfile.close()