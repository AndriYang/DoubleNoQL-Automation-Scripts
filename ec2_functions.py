import os

# AWS EC2 create key-pair
def create_key_pair(ec2, name):
    response = ec2.create_key_pair(
        KeyName=name
    )
    key = response['KeyMaterial']
    f= open(name+".pem","w")
    f.write(key)
    f.close
    os.system('chmod 400 %s.pem' %name)
    print('Key Pair %s Created' %name)
    return response

# AWS EC2 delete key-pair
def delete_key_pair(ec2, name):
    ec2.delete_key_pair(KeyName=name)
    os.remove(name+'.pem')
    print('Key Pair %s Deleted' %name)

# AWS EC2 create security group
def create_security_group(ec2, name, description, ip_permissions):
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    response = ec2.create_security_group(GroupName=name,
                                         Description=description,
                                         VpcId=vpc_id)
    security_group_id = response['GroupId']
    print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

    data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=ip_permissions)
    print('Ingress Successfully Set %s' %data)
    return security_group_id

# AWS EC2 remove security group permissions
def remove_security_group_permissions(ec2, security_group_id, ip_permissions):
    data = ec2.revoke_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=ip_permissions)
    print('Ingress Successfully removed %s' %data)
    return security_group_id

# AWS EC2 set security group permissions
def set_security_group_permissions(ec2, security_group_id, ip_permissions):
    data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=ip_permissions)
    print('Ingress Successfully Set %s' %data)
    return security_group_id

# AWS EC2 delete security group
def delete_security_group(ec2, security_group_id):
    response = ec2.delete_security_group(GroupId=security_group_id)
    print('Security Group %s Deleted' %security_group_id)
    return response

# AWS EC2 create instances
def create_instances(ec2, image, maxCount, instanceType, key, groupID):
    instances = ec2.run_instances(
        ImageId=image,
        MinCount=1,
        MaxCount=maxCount,
        InstanceType=instanceType,
        KeyName=key,
        SecurityGroupIds=[groupID]
    )
    instance_list = []
    for i in instances['Instances']:
        instance_list.append(i['InstanceId'])
    
    print('Instances Created %s' %instance_list)
    return instance_list

# AWS EC2 list instances
def list_ec2_instances(ec2):
    instances = {}
    res = ec2.describe_instances()
    for r in res['Reservations']:
        for ins in r['Instances']:
            if ins['State']['Name'] == 'running' or ins['State']['Name'] == 'pending':
                instances[ins['InstanceId']] = ins['PublicIpAddress']
    print('List of active Instances %s' %instances)
    return instances

# AWS EC2 terminate instances
def terminate_instances(ec2, instances):
    response = ec2.terminate_instances(
        InstanceIds=instances
    )
    print('Instances Deleted %s' %instances)
    return response