BUGLIST
 	Server Doesn't Accept KeyboardInterrupt -> no timeout to allow OS to handle interrupts -> added settimeout and except socket.timeout to allow 			KeyboardInterrupt to be processed
	Odd Message Alignment -> Fixed by creating client.py
	Client Crashing When Using Binary Mode -> No Code to handle binary mode in client.py -> added --binary arg and associated code
	Stalling After Renaming User -> caused by holding the thread lock for too long ->
		only used client lock when checking dictionary for old nickname
	PM Never Finding Target -> caused by improper argument handling-> added another split 		to properly separate both arguments
	
	
