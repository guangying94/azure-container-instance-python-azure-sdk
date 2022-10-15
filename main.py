import os
import time
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, 
                                                 Container,
                                                 ContainerGroupIdentity,
                                                 ContainerGroupSubnetId,
                                                 ContainerPort,
                                                 ContainerGroupNetworkProtocol, 
                                                 ImageRegistryCredential,
                                                 ResourceRequests,
                                                 ResourceRequirements,
                                                 Port,
                                                 IpAddress,
                                                 ContainerGroupRestartPolicy, 
                                                 ResourceIdentityType,
                                                 OperatingSystemTypes, 
                                                 UserAssignedIdentities)


# acquire a credential object
# authenticate to Azure using service principle, to connect to Azure resource management for deployment
# Azure credential will use environment variable, uncomment the following and replace with yhe right info
#os.environ["AZURE_TENANT_ID"] = "<Azure Tenant ID>"
#os.environ["AZURE_CLIENT_ID"] = "<Azure Client ID>"
#os.environ["AZURE_CLIENT_SECRET"] = "<Azure Client secret>"
sp_cred = DefaultAzureCredential()

# Define parameters accordingly
subscription_id = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
resource_group_name = '<rg-name>'
container_group_name = '<container-group-name>'
container_registry = '<your-container-registry-name>.azurecr.io' 
container_image = '<your-container-registry-name>.azurecr.io/<image-name>:<image-tag>'
user_assigned_mi_resource_id = '/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myUAMI'
subnet_resource_id = '/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myRG/providers/Microsoft.Network/virtualNetworks/myVNET/subnets/mySubnet'
rg_location = '<azure-location>'
container_port = 5000
request_memoryInGB = 1
request_cpu = 1
container_os = 'Linux'


def create_aci(aci_client):
    # Define Container Image Properties
    # Update accordingly if multiple containers, or init container is needed in Container Group
    container_resource_requests = ResourceRequests(memory_in_gb=request_memoryInGB,cpu=request_cpu)
    container_resource_requirements = ResourceRequirements(requests=container_resource_requests)
    container = Container(name=container_group_name,
                        image=container_image,
                        resources=container_resource_requirements,
                        ports=[ContainerPort(port=container_port)])

    # Define Container Group, with ACR credential and ACI credential, which is UAMI
    container_group_subnet_id = ContainerGroupSubnetId(id=subnet_resource_id)
    container_group_restart_policy = ContainerGroupRestartPolicy.Always
    ports = [Port(protocol=ContainerGroupNetworkProtocol.tcp, port=container_port)]
    group_ip_address = IpAddress(ports=ports,type="Private")
    ## Define container registry credential, using user-assigned managed identity to authenticate
    container_image_registry = ImageRegistryCredential(server=container_registry,identity=user_assigned_mi_resource_id)
    ## Assign user-assigned mmanaged identity to container group, so that container group can use this managed identity to authenticate to ACR
    user_assigned_identity = UserAssignedIdentities(client_id=user_assigned_mi_resource_id)
    container_group_identity = ContainerGroupIdentity(type=ResourceIdentityType('UserAssigned'),user_assigned_identities={user_assigned_mi_resource_id: user_assigned_identity})

    ## Define specification for container group
    group = ContainerGroup(location=rg_location,
                        containers=[container],
                        os_type=OperatingSystemTypes.linux,
                        subnet_ids=[container_group_subnet_id],
                        restart_policy=container_group_restart_policy,
                        image_registry_credentials=[container_image_registry],
                        ip_address=group_ip_address,
                        identity=container_group_identity)

    # Actual creation of ACI
    aci_client.container_groups.begin_create_or_update(resource_group_name,
                                                    container_group_name,
                                                    group)

def list_aci(aci_client):
    items = aci_client.container_groups.list()
    for item in items:
        print(item.name)

if __name__ == "__main__":
    print('Initiated ACI Client to create ACI')
    aci_client = ContainerInstanceManagementClient(sp_cred,subscription_id,'https://management.azure.com')
    print('Creating ACI....')
    create_aci(aci_client)
    print('Wait for ACI creation... It will take some time...')
    time.sleep(120)
    print('Listing out all Azure Container Instance...')
    list_aci(aci_client)