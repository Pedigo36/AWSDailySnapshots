#Snapshot creation and tagging script
#Create a role, add the following permissions: write logs, ec2:describe (all describes) ec2:Createsnapshot,deletesnapshot,create tags, # modifysnapshotattribute,resetsnapshotattribute
#Use this role for Lambda when you add the code

#Start Python
import boto3
import collections
import datetime


ec = boto3.client('ec2')

#Information found in Description on each snapshot
CreatDate="Lamda created this backup on-%s" % datetime.date.today()

def lambda_handler(event, context):
    reservations = ec.describe_instances(
        Filters=[
#Keyname and value
            {'Name': 'tag-key', 'Values': ['BackupFrequency']},
            {'Name': 'tag-value', 'Values': ['Daily', 'daily']},
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print "Found %d instances that need backing up" % len(instances)

    to_tag = collections.defaultdict(list)

#Allows you to set retention per ec2 by adding a tag name Retention with number of days for the value (7,14,etc)
    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
#Retention Period default       
            retention_days = 90

        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            print "Found EBS volume %s on instance %s" % (
                vol_id, instance['InstanceId'])

#Code to Create snapshot and add the create date from earlier as the description this is where you would add a name
            snap = ec.create_snapshot(
                VolumeId=vol_id, Description=CreatDate,
            )

            to_tag[retention_days].append(snap['SnapshotId'])

            print "Retaining snapshot %s of volume %s from instance %s for %d days" % (
                snap['SnapshotId'],
                vol_id,
                instance['InstanceId'],
                retention_days,
            )

#retention period calculation and tag addition This would be a great place for someone to add the ability to delete tags "older than" #the delete date, instead of just on the delete date.
    for retention_days in to_tag.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        print "Will delete %d snapshots on %s" % (len(to_tag[retention_days]), delete_fmt)
        ec.create_tags(
            Resources=to_tag[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
            ]
        )
