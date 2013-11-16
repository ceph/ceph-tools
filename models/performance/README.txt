PURPOSE, FORM, AND SCOPE OF THIS MODEL

This is not a discrete event simulation that attempts to simulate the behavior
of a system.  Rather it is a latency, bandwidth, and resource consumption model
that attempts to estimate the time required to perform common operations, and
the associated load that puts on critical resources.

Its purposes are:

	to enable us to simulate the likely impact of proposed changes

	to enable us to better understand our performance by forcing us
	represent our assumptions in an executable model, with we can
	compare with actual measurements

	to enable us to estimate the performance of a system built with
	a specific number of specific components, and thus do a better 
	job of configuration plannign for customers

	to enable us to compare the actual behavior of a customer system
	with the expected system, and thus more easily recongize 
	discrepancies

Fundmental Premises:

	You can add up the time, CPU, and disk/network resources required 
	for each operation, and compute the total cost from the sum of the
	pieces.

	Parallel operations can be modeled by summing the resource consumption
	and taking the length of the longest path.

	We will model the steady-state behavior of a system that is serving
	only requests of a single type (at the maximum possible rate).  We
	can estaimate the performance of mixed work-loads by taking linear
	combinations of the individual components (each with its respective
	throughputs, latencies, and resource consumptions).

Hazzards:

	When we model some operation, we must be very clear exactly what the benchmark
	in question will do ... because we want to model the same transactions we will
	be measuring.

	This can be a problem when the benchmark does not use the component in the
	same way that higher level components use it.  It is best if we can find
	or create a benchmark that does use the component in the same way it will
	be used in real service.

Form of the model:

	This is a hierarchy of simulations.

	We start with some very basic objects (disk, CPU, NIC) which are instantiated
	with speed and type parameters.  

	Higher level simulations (e.g. file systems and servers) are passed lower level
	simulations as parameters, and use them to compute their own costs.

	Each simulation has a number of methods to simulate the performance and costs
	of common operations.  They take parameters appropriate to the operations being
	simulated (e.g. block size, request depth).  

	Lower Level simulations simply return a time (in micro seconds)

	Higher level simulations return a tupple containing:

		the average per-request completion time (including all queueing delays)

		the maximum achievable throughput (in operations per second).  
		If multiple requests are processed in parallel, this may be much greater
		than 1/completion-time.

		a dictionary containing the names of resources (e.g. 'cpu', 'hba',
		'nic', 'fs') and the load (1.0 = one fully saturated unit) it would
		impose on that resource to deliver the maximum achievable bandwidth.

		Note that if there are multiple cores or NICs available, that the load
		can reasonably be greater than one.  But it should never be greater than
		the available resources.

Low Level (primitive) Simulations

    Disk
	seekTime(cyls, read)
	xferTime(bytes, read)
	avgRead(bsize, filesize, seq, depth)
	avgWrite(bsize, filesize, seq, depth)


    NIC/HBA
	read_time(bytes)  ... elapsed time
	read_cpu(bytes)   ... CPU time
	write_time(bytes) ... elapsed time
	write_cpu(bytes)  ... CPU time
	queue_length(rho, max_depth)

    CPU
	mem_read(bytes)   ... elapsed time for memory access
	mem_write(bytes)  ... elapsed time for memory access
	process(bytes)	  ... elapsed time for CPU/bus access
	thread_us()	  ... thread switch
	proc_us()	  ... process switch
	dma_us()	  ... DMA start and interrupt
	queue_length(rho, max_depth)

Higher Level Simulations

    FS
	read(bsize, file_size, seq, depth, direct)
	write(bsize, file_size, seq, depth, direct, sync))
	stat()
	open()
	create(sync)
	delete(sync)
	getattr()
	setattr(sync)

   FileStore
	read(bsize, objsize, depth, nobj)
	write(bsize, objsize, depth, nobj)
	create()
	delete()

   Rados
	read(bsize, objsize, nobj, depth, clients)
	write(bsize, objsize, nobj, depth, clients, copies)
	create(depth)
	delete(depth)
