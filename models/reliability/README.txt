Notes on Reliability Modeling:

   General Notes:

     1.	Failure rates are characterized in units of failures per billion hours (FITs),
	and so I have tried to represent all periodicities in FITs and all times in
	hours.``

     2.	Failure events are considered to be Poisson, and given a failure rate 'f' 
	the probability of 'n' failures during time 't' is

		P(n,f,t) = (f * t)^n * exp( -f * t ) / n!

     3.	Non-Recoverable Errors (NREs) are troublesome in several ways:

	   (a)	they include both reported non-correctable errors and 
		undetected returns of incorrect data ... which are very
		different.

	   (b)	The regularly quoted rates (ranging from 10^-13 - 10^-15) are
		probably not, in fact, reasonably characterized in that way.
		My understanding is that NRE's result when enough single bit
		errors accumulate to become uncorrectable (or undetectable).
		Detected errors cause the data to be re-written ... correcting
		the error.  This is why scrubbing is so highly touted.
		
		The quoted statistics probably came from SMART data, but in
		reality the rate is probably proportional, not to the number
		of bits read, but to the mean un-read age, which is highly
		usage specific. 

	   (c)	It is not clear how to model their consequences.  I don't know
		that there are any good choices, so I provide the user with a
		few options:
		   ignore them ... NRE's never happen
			which might be true on scrubbed volumes
		   consider them to cause a recovery to fail
			which might be true for many RAID controllers
		   consider them to result in a few corrupted bytes
			which is surely true for undetected errors, and may be
			true for detected errors with some RAID controllers
		   consider half to fail, half to be corruption
			a semi-arbitrary but commonly used modeling assumption

    Comments on Annual Durability

    	I have understood "durability", as defined by Amazon, to be the 
	probability (per object) that no data loss (or corruption) will 
	occur during a specified period.

	The most directly computed durability number is for a drive
	(or, for RADOS, a placement group).

	   For whole-drive recovery failures, the annual durability of an
	   (arbitrary) object is exactly equal to the annual durability
	   of the drive on which it resides.

 	   For placement-group recovery failures, the annual durability of
	   an (arbitrary) object is roughly equal to the annual durability
	   of the placement group, divided by two (assuming that, on average,
	   half of the objects in the placement group will have been recovered).

	   For striped objects, this base durability must be raised to the
	   power of the number of volumes across which it is striped.

	   For whole-site failures, the annual durability of an (arbitrary)
 	   object is equal to the annual durability of the site.

	For data corruption events, we should take the per-byte corruption
	probability and multiply it by the number of bytes.


    Comments on Disk Reliability modeling

	The probability of some failure during time 't' is computed as one minus
	the probability of zero failures during time 't'.

	The probability of a failure on any of 'd' disk drives during time 't'
	is computed by multiplying the single-drive FIT rate by 'd'.


    Comments on RAID Reliability modeing

	The recovery time is modeled as the sum of:

	   (a)	the drive replacement time
	
	   (b)	the rebuild time, which is computed as the useful size of the
		disk divided by the specified recovery rate (which applies
		to the target drive, not to the individual source drives)
		

	Given:

	    a redundancy 'C' (number of copies or parity volumes - 1)

	    a target set 'T' (number of volumes required to recover)
		one for mirroring
		number of data volumes for RAID-5 or RAID-6
	    
	    a drive replacment time of Trplc

	    a drive recovery time of Trecov = useful capacity / recovery rate
		
	The probability of RAID failure during time 't' is modeled as the product of

	   (a)	the probability of a single drive failure during time 't'

	   (b)	the probability that one of 'T' drives will fail during time
		(Treplc + Trecov), raised to the power C

	If a RAID recovery fails, it is assumed that one entire disk is lost.
	
	NRE's during recovery are treated as described in general note 3.


    Comments on RADOS Reliability modeling

	The recovery time is modeled as the sum of:

	    (a)	the OSD markout period

	    (b) the rebuild time, which is computed as the useful size of the
		disk, multiplied by the fullness factor, divided by the product 
		of the specified recovery rate and the specified declustering factor.

	    Note that the declustering factor is the lesser of the number
	    of surviving OSDs and the number of PGs per OSD.

	    Note that the recovery rate must be the actual recovery rate
	    (per node, including throttling) and not merely the large object 
	    write rate.

	Given:

	    a redundancy 'C' (number of copies - 1)

	    a declustering factor 'D' (number of volumes required to recover)
	    
	    a drive markout time of Tmark

	    a drive recovery time of Trecov = capacity / recovery rate
		
	The probability of RADOS failure during time 't' is modeled as the product of

	   (a)	the probability of a single drive failure during time 't'

	   (b)	the probability that one of 'D' drives will fail during time
		(Treplc + Trecov), raised to the power C

	If a RADOS recovery fails, it is assumed we loose one half (because
	the failure will happen half way through the recovery) of a disk
	divided by the declustering factor.
	    
	If an NRE is modeled as a failure, the amount of data lost is
	assumed to be the smaller of a placement group or an object.


    Comments on site-and multi-site reliability modeling

	I do not know how Amazon has modeled site reliability, but
	the two Werner Vogels quotes on the subject are:

	    the S3 service is “design[ed]” for “99.999999999% durability”

	    Amazon S3 is designed to sustain the concurrent loss of data 
	    in two facilities
	
	The second quote would seem to suggest three copies.  It is
	not clear whether or not the eleven-nines design modeling
	includes regional disasters, but such numbers are easily 
	obtained by three sites if regional disasters are ignored.
	My take is that it is not possible to discuss more than 
	four nines of annual durability without factoring in
	facility and regional disasters (which are probably 2-5 
	nines events).

	I characterize sites by a FIT rate, which can be based on the
	expected periodicity of the regional disaster (e.g. a 100 year
	flood or a 1000 year earthquake).   Perhaps the model should
	allow different sites to have different FIT rates ... although
	I fear that this might add worthless precision to numbers that
	are highly speculative.

	It is tempting to think that four geo-sites is plenty, but after
	a 200 year hurricane hits Atlanta, you will only have three.  Thus
	the time to re-replicate to a new site (e.g. 10 days to obtain 1,000
	drives, rack them up, re-replicate, ship them to a new data center
	and bring those replicas back on line).  I have used the ratio of 
	MTTF/(MTTF+MTTR) is then the long term availability for each replica.
	If no MTTR is specified, I simply use the annual site durability.

	When modeling multi-site replicated data, I broke out several independent
	terms: 

	    a.	The probability that the primary site will be destroyed before 
		a newly created object can be replicated to other sites.  

		This might seem a very unlikely event because the window is
		so small, but (in a system with asynchronous replication) it 
		turns out to be the tall pole in the tent ...  because no 
		number of copies (local or remote) can help.  The expected
		data loss is low, but durability doesn't distinguish the loss
		of a byte from the loss of a petabyte.

	    b.	The probability that a primary site will lose all of its copies

		b1. the probability of one copy failing during the period of
		    interest (e.g. one year) and all others failing during the
 		    local recovery period ... which has already been computed
		    above in the RADOS model.

		b2. the probability that the primary site will fail during
		    the preriod of interest (e.g. one year)

		These two terms turn out to be of comparable magnitude.

	    c.	The probability that a secondary site will be unable to make up
		for failure b is the sum of:
		
		c1.  the probability the secondary site will lose all of its
		     copies during the time required for a remote recovery
		     (less than b1 because the period is much smaller)

		c2.  the probability the secondary site will have already been
 		     taken down by the time it is needed for recovery
		     (this is essentially the annual site durability)

		c3.  the probability the secondary site will be destroyed 
		     during the remote recovery (a very small number)

	the probability of data loss in a system with N such data centers is modeled as:
	
		a + ((b1+b2) * (c1+c2+c3)^(N-1))
