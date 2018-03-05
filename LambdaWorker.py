#Start Python
6	import boto3
7	import collections
8	import datetime
9	
10	
11	ec = boto3.client('ec2')
12	
13	#Information found in Description on each snapshot
14	CreatDate="Lamda created this backup on-%s" % datetime.date.today()
15	
16	def lambda_handler(event, context):
17	    reservations = ec.describe_instances(
18	        Filters=[
19	#Keyname and value
20	            {'Name': 'tag-key', 'Values': ['BackupFrequency']},
21	            {'Name': 'tag-value', 'Values': ['Daily', 'daily']},
22	        ]
23	    ).get(
24	        'Reservations', []
25	    )
26	
27	    instances = sum(
28	        [
29	            [i for i in r['Instances']]
30	            for r in reservations
31	        ], [])
32	
33	    print "Found %d instances that need backing up" % len(instances)
34	
35	    to_tag = collections.defaultdict(list)
36	
37	#Allows you to set retention per ec2 by adding a tag name Retention with number of days for the value (7,14,etc)
38	    for instance in instances:
39	        try:
40	            retention_days = [
41	                int(t.get('Value')) for t in instance['Tags']
42	                if t['Key'] == 'Retention'][0]
43	        except IndexError:
44	#Retention Period default       
45	            retention_days = 90
46	
47	        for dev in instance['BlockDeviceMappings']:
48	            if dev.get('Ebs', None) is None:
49	                continue
50	            vol_id = dev['Ebs']['VolumeId']
51	            print "Found EBS volume %s on instance %s" % (
52	                vol_id, instance['InstanceId'])
53	
54	#Code to Create snapshot and add the create date from earlier as the description this is where you would add a name
55	            snap = ec.create_snapshot(
56	                VolumeId=vol_id, Description=CreatDate,
57	            )
58	
59	            to_tag[retention_days].append(snap['SnapshotId'])
60	
61	            print "Retaining snapshot %s of volume %s from instance %s for %d days" % (
62	                snap['SnapshotId'],
63	                vol_id,
64	                instance['InstanceId'],
65	                retention_days,
66	            )
67	
68	#retention period calculation and tag addition This would be a great place for someone to add the ability to delete tags "older than" #the delete date, instead of just on the delete date.
69	    for retention_days in to_tag.keys():
70	        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
71	        delete_fmt = delete_date.strftime('%Y-%m-%d')
72	        print "Will delete %d snapshots on %s" % (len(to_tag[retention_days]), delete_fmt)
73	        ec.create_tags(
74	            Resources=to_tag[retention_days],
75	            Tags=[
76	                {'Key': 'DeleteOn', 'Value': delete_fmt},
77	            ]
78	        )
