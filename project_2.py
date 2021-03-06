#/usr/bin/python
#Joseph Davies
from pynode.main import *
import ast
import sys
import time
from ADTs import *


#CLI flags
defaults = False
animation_speed = 1.0
time_factor = 1.0
#evaluate CLI flags
i = 0
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-defaults":
		defaults = True
		print("using defaults data collumns")
	if arg.startswith("-animation_speed="):
		animation_speed = float(arg[17:])
		time_factor = animation_speed
		#take the reciprocal
		animation_speed = 1 / animation_speed
		print("set animation speed to {0}x".format(time_factor))
	i += 1
del i

node_1 = None
node_2 = None
active_edge = None

is_running  = False

#references to nodes
node_clear = None
node_start = None
node_time = None

#list of sensors and nodes
sensor_nodes = list()
break_nodes = list()

#simulation variables
start_time = 0
simulation_time = 0
wave_propogation_pqueue = priority_queue()
time_node_value = -1

#reset all selected nodes
def reset():
	global node_1, node_2, active_edge
	if node_1 in sensor_nodes:
		node_1.set_color(Color(150, 50, 150))
	elif node_1 in break_nodes:
		node_1.set_color(Color(50, 100, 200))
	else:
		node_1.set_color(Color.DARK_GREY)
	if node_2 in sensor_nodes:
		node_2.set_color(Color(150, 50, 150))
	elif node_2 in break_nodes:
		node_2.set_color(Color(50, 100, 200))
	else:
		node_2.set_color(Color.DARK_GREY)
	if active_edge is not None:
		active_edge.set_color(Color.LIGHT_GREY)
	node_1 = None
	node_2 = None
	active_edge = None

#convert a number to a float if it can otherwise return None
def is_float(posible_int):
	output = None
	try:
		output = float(posible_int)
	except:
		output = None
	return output

#function to get the users input	
def prompt(request_length = False, request_time = False):
	first = None
	second = None
	third = None
	#ask the user weather they want to add a break or a sensor
	while True:
		print("What would you like to do:")
		input_1 = input("Add a break (b), add a sensor (s), cancel (c): ").lower().rstrip()
		if input_1 == "b":
			first = input_1
			break
		elif input_1 == "s":
			first = input_1
			break
		elif input_1 == "c":
			return (None, None, None)
		else:
			print("Invalid Input")
	
	#ask the user how far from the first node they clicked they want to new node to be
	if request_length:
		while True:
			input_2 = is_float(input("How far along the pipe do you want to add it in meters: ").lower().rstrip())
			if input_2 != None:
				second = input_2
				break
			else:
				print("Invalid Input")
	
	#ask the user when they want a break to occur
	if request_time and first == "b":
		while True:
			input_3 = is_float(input("At what time does the break happen: ").lower().rstrip())
			if input_3 != None:
				third = input_3
				break
			else:
				print("Invalid Input")
		
	return (first, second, third)


def on_click(node):
	global node_1, node_2, active_edge, is_running
	print("Clicked on node \"{}\"".format(node.id()))
	
	#start node
	if node is node_start and not is_running:
		is_running = True
		simulate()
		return
	
	#disable user input if the application is running
	if not is_running:
		#clear selection node
		if node is node_clear:
			reset()
			return
		
		#if both nodes have been selected and you select a third reset the selection
		if node_1 is not None and node_2 is not None:
			reset()
		
		#if node 1 has not been selected select it
		if node_1 is None:
			node_1 = node
			node_1.set_color(Color.YELLOW)
		#if node 1 has been selected and node 2 has not been selected select node 2
		elif node_2 is None:
			node_2 = node
			node_2.set_color(Color.GREEN)
		
		#if the two selected nodes are different highlight the edge between them
		if node_1 is not None and node_2 is not None and node_1 is not node_2:
			try:
				active_edge = graph.edges_between(node_1, node_2)[0]
				active_edge.set_color(Color.BLUE)
			except Exception as e:
				print("Cannot find edge between selected nodes")
				print(e)
				return
		
		#if both nodes have been selected ask the user what to do
		if node_1 is not None and node_2 is not None:
			#ask the user for what they want to do
			#if the two nodes are different ask for the edge between them
			if active_edge is not None:
				new_thing_type, new_thing_length, new_thing_time = prompt(True, True)
			#if the two nodes are the same then don't ask the for the edge
			else:
				new_thing_type, new_thing_length, new_thing_time = prompt(False, True)
			
			#if nothing is got from the user then just reset
			if new_thing_type is None and new_thing_length is None:
				reset()
				return
			
			#if a length is specified aka the new node is between nodes
			if new_thing_length != None:
				#break
				if new_thing_type == "b":
					#add the node
					new_node = graph.add_node("Break: " + str(len(break_nodes) + 1))
					new_node.set_color(Color(50, 100, 200))
					new_node.set_attribute("time", new_thing_time)
					#calculat new edge lengths and ingore fp rounding errors
					length_1 = round(new_thing_length, 1)
					length_2 = round(active_edge.weight() - new_thing_length, 1)
					#add the edges
					new_edge_1 = graph.add_edge(node_1, new_node)
					new_edge_1.set_weight(length_1)
					new_edge_1.set_attribute("length", length_1)
					new_edge_1.set_attribute("inner radius", active_edge.attribute("inner radius"))
					new_edge_1.set_attribute("speed", active_edge.attribute("speed"))
					new_edge_2 = graph.add_edge(new_node, node_2)
					new_edge_2.set_weight(length_2)
					new_edge_2.set_attribute("length", length_2)
					new_edge_2.set_attribute("inner radius", active_edge.attribute("inner radius"))
					new_edge_2.set_attribute("speed", active_edge.attribute("speed"))
					#remove the old edge
					graph.remove_edge(active_edge)
					active_edge = None
					#record the break node
					break_nodes.append(new_node)
				#sensor
				elif new_thing_type == "s":
					#add the node
					new_node = graph.add_node("Sensor: " + str(len(sensor_nodes) + 1))
					new_node.set_color(Color(150, 50, 150))
					#calculat new edge lengths and ingore fp rounding errors
					length_1 = round(new_thing_length, 1)
					length_2 = round(active_edge.weight() - new_thing_length, 1)
					#add the edges
					new_edge_1 = graph.add_edge(node_1, new_node)
					new_edge_1.set_weight(length_1)
					new_edge_1.set_attribute("length", length_1)
					new_edge_1.set_attribute("inner radius", active_edge.attribute("inner radius"))
					new_edge_1.set_attribute("speed", active_edge.attribute("speed"))
					new_edge_2 = graph.add_edge(new_node, node_2)
					new_edge_2.set_weight(length_2)
					new_edge_2.set_attribute("length", length_2)
					new_edge_2.set_attribute("inner radius", active_edge.attribute("inner radius"))
					new_edge_2.set_attribute("speed", active_edge.attribute("speed"))
					#remove the old edge
					graph.remove_edge(active_edge)
					active_edge = None
					#record the break node
					sensor_nodes.append(new_node)
			#if no length is specified aka the break is being placed over another node
			else:
				#break
				if new_thing_type == "b":
					#record all the surrounging nodes and edge weights
					things_to_reconect_to = list()
					for edge in node_1.incident_edges():
						things_to_reconect_to.append((edge.other_node(node_1), edge.weight(), edge.attribute("speed"), edge.attribute("inner radius")))
					#remove the current node
					graph.remove_node(node_1)
					#add the new node
					new_node = graph.add_node("Break: " + str(len(break_nodes) + 1))
					new_node.set_color(Color(50, 100, 200))
					new_node.set_attribute("time", new_thing_time)
					#reconnect node to it's surroundings
					for thing in things_to_reconect_to:
						node_to_conect_to, weight, wave_speed, pipe_i_radius = thing
						new_edge = graph.add_edge(new_node, node_to_conect_to)
						new_edge.set_weight(weight)
						new_edge.set_attribute("length", weight)
						new_edge.set_attribute("inner radius", pipe_i_radius)
						new_edge.set_attribute("speed", wave_speed)
					#record the break node
					break_nodes.append(new_node)
				elif new_thing_type == "s":
					#record all the surrounging nodes and edge weights
					things_to_reconect_to = list()
					for edge in node_1.incident_edges():
						things_to_reconect_to.append((edge.other_node(node_1), edge.weight(), edge.attribute("speed"), edge.attribute("inner radius")))
					#remove the current node
					graph.remove_node(node_1)
					#add the new node
					new_node = graph.add_node("Sensor: " + str(len(sensor_nodes) + 1))
					new_node.set_color(Color(150, 50, 150))
					#reconnect node to it's surroundings
					for thing in things_to_reconect_to:
						node_to_conect_to, weight, wave_speed, pipe_i_radius = thing
						new_edge = graph.add_edge(new_node, node_to_conect_to)
						new_edge.set_weight(weight)
						new_edge.set_attribute("length", weight)
						new_edge.set_attribute("inner radius", pipe_i_radius)
						new_edge.set_attribute("speed", wave_speed)
					#record the sensor node
					sensor_nodes.append(new_node)


def simulate():
	global start_time, wave_propogation_pqueue
	print("starting simulation")
	
	#put the breaks into a priority queue of when they will trigger
	#set the node they came from to 0 because they are sources
	for node in break_nodes:
		wave_propogation_pqueue.enqueue((node, None), node.attribute("time"))
	
	start_time = time.time()
	print("start time", start_time)
	print("====================================================")
	should_continue = True
	while should_continue:
		should_continue = simulation_itteration()

def simulation_itteration():
	global simulation_time, node_time, time_node_value
	simulation_time = time.time() - start_time
	simulation_time *= time_factor
	
	t_node_val = round(simulation_time, 1)
	if t_node_val != time_node_value:
		node_time.set_value("t={0}".format(t_node_val))
		time_node_value = t_node_val
	
	#if there is nothing left in the queue signal to stop itterating
	if wave_propogation_pqueue.length() == 0: return False
	
	hit_time = wave_propogation_pqueue.front_priority()
	if simulation_time > hit_time:
		node, node_from = wave_propogation_pqueue.dequeue()
		
		if node in sensor_nodes:
			print("hit {0} at {1}".format(node.id(), simulation_time))
		
		#n_to = node.id()
		#n_from = node_from.id() if node_from is not None else "No node"
		#print("{0} -> {1}".format(n_from, n_to))
		#print("@ {0}".format(hit_time))
		#print("----------------------------------------------------")
		
		for edge in node.incident_edges():
			other_node = edge.other_node(node)
			if other_node is node_from: continue
			
			#time in seconds for the wave to move along the pipe
			wave_time = edge.attribute("length") / edge.attribute("speed")
			#convert to miliseconds
			wave_time_ms = wave_time * 1000
			#multiply by animation time
			wave_time_ms *= animation_speed
			edge.traverse(node, Color.RED, True, wave_time_ms)
			
			thing_to_enqueue = (other_node, node)
			wave_propogation_pqueue.enqueue(thing_to_enqueue, hit_time + wave_time)
			
	#continue to the next itteration
	return True
		
nodes = dict()
#if the node does not exist make it and return a reference to a node. if the node does exist return a reference to it 
def get_node(name):
	if name in nodes:
		return nodes[name]
	else:
		node = graph.add_node(name)
		nodes[name] = node

#if the edge does not exist make it and return it if it does exist return it
#if the egde involves nodes that do not exist make them
def get_edge(node_1, node_2):
	if graph.adjacent(get_node(node_1), get_node(node_2)):
		return graph.edges_between(get_node(node_1), get_node(node_2))[0]
	else:
		edge = graph.add_edge(get_node(node_1), get_node(node_2))
		return edge

def run():
	global node_clear, node_start, node_time
	
	#user interface nodes
	node_clear = graph.add_node("Clear")
	node_clear.set_color(Color.RED)
	node_clear.set_position(50, 480)
	
	node_start = graph.add_node("Start")
	node_start.set_color(Color.RED)
	node_start.set_position(100, 480)
	
	node_time = graph.add_node("t=0")
	node_time.set_color(Color.BLACK)
	node_time.set_position(150, 480)
	
	length_index = 2
	diameter_index = 3
	thickness_index = 7
	speed_index = 10
	
	#if the user does not specify the -defaults flag then ask then what columns to get the data from
	if not defaults:
		length_index = input("What collumn is the lengin in: ")
		diameter_index = input("What collumn is the diameter in: ")
		thickness_index = input("What collumn is the thicnkess in: ")
		speed_index = input("What collumn is the speed in: ")
	
	#construt the graph
	with open("pipes.csv", 'r') as csv_file:
		first = True
		for line in csv_file:
			#if it is the first line ignore it as it is the header
			if first:
				first = False
				continue
			#split the data into columns
			data = line.rstrip().lstrip().replace("\t","").split(',')
			#where posible evaluate literals
			i = 0
			while i < len(data):
				try:
					data[i] = ast.literal_eval(data[i])
					i += 1
				except:
					i += 1
			
			
			for element in data:
				#get the edge between the two nodes in the line
				#if the edge does not exist create it
				#if either of the nodes do not exist create them
				e = get_edge(data[0], data[1])
				
				#set the values of the edge
				e.set_weight(data[length_index])
				e.set_attribute("length", data[length_index])
				e.set_attribute("inner radius", (data[diameter_index] - 2 * data[thickness_index]) / 2)
				e.set_attribute("speed", data[speed_index])
	
	register_click_listener(on_click)
begin_pynode(run)
