Notes on Reliability Modeling:

   General Notes:

     1.	Failure rates are characterized in units of failures per billion hours (FITs).

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
		of bits read, but to the mean unread age, which is highly
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

    4.	I have understood "durability" to be the probability (e.g. per petabyte)
	that no data loss will occur during a specified period.

	It has been computed as the probability of no data loss (over the specified
	period) per drive, raised to the power of the number of drives per petabyte.
	Although perhaps a more accurate modeling would be to compute a FIT rate
	per (replicated) drive, and then compute the probability of zero failures
	at N times that FIT rate.


    Comments on Disk Reliability modeling

	The probability of some failure during time 't' is computed as one minus
	the probability of zero failures during time 't'.

	The probability of a failure on any of 'd' disk drives during time 't'
	is computed by multiplying the single-drive FIT rate by 'd'.


    Comments on RAID Reliability modeing

	The recovery time is modeled as the sum of:

	   (a)	the drive replacement time
	
	   (b)	the rebuild time, which is computed as the useful size of the
		disk divided by the specified recovery rate

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


    Comments on RAID Reliability modeing

	The recovery time is modeled as the sum of:

	   (a)	the drive replacement time
	
	   (b)	the rebuild time, which is computed as the useful size of the
		disk divided by the specified recovery rate

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
		disk, divided by the product of the specified recovery rate
		and the specified declustering factor.

	    This is actually an over-estimate, because RADOS only recovers 
	    space that has actually been used.  Thus the capacity should be
	    multiplied by a fullness factor.

	    Note that the declustering factor is the lesser of the number
	    of surviving OSDs and the number of PGs per OSD.

	    Note that the recovery rate should be the actual recovery rate
	    (including throttling) and not merely the large object write
	    rate.

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
	    
	If an NRE is considered to be a failure, the amount of data lost is
	assumed to be the smaller of a placement group or an object.


    Comments on site-and multi-site reliability modeling

	I characterize sites by a FIT rate, which can be based on the
	expected periodicity of the regional disaster (e.g. a 100 year
	flood or a 1000 year earthquake).   Perhaps the model should
	allow different sites to have different FIT rates ... although
	I fear that this might add worthless precision to otherwise
	approximate numbers.

	It is tempting to think that four geo-sites is plenty, but after
	a 200 year hurricane hits Atlanta, you will only have three.  Thus
	the time to re-replicate to a new site (e.g. 10 days to obtain 1,000
	drives, rack them up, re-replicate, ship them to a new data center
	and bring those replicas back on line).  The ratio of MTTF/(MTTF+MTTR)
	is then the long term availability for each replica.

	When modeling multi-site replicated data, I broke out several independent
	terms: 

	    a.	The probability that the primary site will be destroyed before 
		a newly created object can be replicated to other sites.  This 
		is a very small number, but when we are talking ten or more nines, 
		there are no negligible terms. 

	    b.	The probability that a primary site will lose all of its copies

		b1. the probability of one copy failing during the period of
		    interest (e.g. one year) and all others failing during the
 		    local recovery period ... which has already been computed
		    above in the RADOS model.

		b2. the probability that the primary site will fail during
		    the preriod of interest (e.g. one year)

	    c.	The probability that a secondary site will be unable to make up
		for failure b is the sum of:
		
		c1.  the probability the secondary site will lose all of its
		     copies during the time required for a remote recovery

		c2.  the probability the secondary site will have already been
 		     destroyed by the time the recovery is needed.

		c3.  the probability the secondary site will be destroyed 
		     during the remote recovery

	the probability of data loss in a system with N such data centers is modeled as:
	
		a + ((b1+b2) * (c1+c2+c3)^(N-1))  

	but I fear that term (a) is wrong, as this seems a single event probability
