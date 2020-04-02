# Install
# Run as administrator and set this before installing and modules
Get-ExecutionPolicy
Set-ExecutionPolicy RemoteSigned
# Azure CLI
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\AzureCLI.msi
# Az Module
Install-Module Az
# PowerShell Install/Misc:
# Find PowerShell version
$PSVersionTable.PSVersion
# Allow scripts
powershell -nop -exec bypass
# Uninstall AzureRM
Uninstall-Module AzureRM
Uninstall-Module AzureRM -AllVersions -Force 
Get-InstalledModule | foreach{uninstall-module $_.name}
foreach ($module in (Get-Module -ListAvailable AzureRM*).Name | Get-Unique) {
    write-host "Removing Module $module"
    Uninstall-module $module
 }


# Log In
Connect-AzAccount --use-device-code # If multiple subscriptions
az login --use-device-code # If multiple subscriptions


# Get Subscriptions
Get-AzContext -ListAvailable
Get-AzSubscription

# Set Subscription (-id or -name)
Select-AzSubscription -SubscriptionId 


# Misc Commands:
# List Regions:
az account list-locations
# Get VGW Advertised Routes
Get-AzVirtualNetworkGatewayAdvertisedRoute -ResourceGroupName <RG Name> -VirtualNetworkGatewayName <VGW Name> -Peer <Peer IP>
# Get VGW Learned Routes
Get-AzVirtualNetworkGatewayLearnedRoute -ResourceGroupName <RG Name> -VirtualNetworkGatewayName <VGW Name>
# Get Effective Routes
Get-AzEffectiveRouteTable -ResourceGroupName <RG-NAME> -NetworkInterfaceName <VM NIC Name> | Format-Table
az network nic show-effective --resource-group <RG-NAME> -route-table --name <VM NIC Name>


# Enable/Configure Forced Tunneling
Set-AzureRmVirtualNetworkGatewayDefaultSite -GatewayDefaultSite $LocalGateway -VirtualNetworkGateway $VirtualGateway
az network vnet-gateway update -g <RG-NAME> -n <VGW-Name> --gateway-default-site <LNG-Name>



# Useful Stuff:
# Start/stop all VM's in a Resource-Group
get-azvm -ResourceGroupName <RG-NAME> | foreach {start-azurerm -Name $_.name -resourcegroupname <RG-NAME>}
get-azvm -ResourceGroupName <RG-NAME> | foreach {stop-azurerm -Name $_.name -resourcegroupname <RG-NAME> -confirm:$false -force}
# Create Resource-Group
New-AzResourceGroup -Name <resource-group-name> -Location <resource-group-location>
az group create --name <resource-group-name> --location <resource-group-location> 
# Deploy ARM Template
New-AzResourceGroupDeployment -ResourceGroupName <resource-group-name> -TemplateUri https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.json
az deployment group create --resource-group <my-resource-group> --template-uri https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.json





# Troubleshooting:
# Retrieve weird error details (wait a couple minutes)
az monitor activity-log list --correlation-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx




# Misc scripting
# Select only one column from each output
cmd | select blah
# List what options you can 'choose' from the output
cmd | get-member
# Find count of items in output of command
(get-azvm).count



# REST API
# Create Service Principal (For Authentication via REST)
$sp = New-AzADServicePrincipal -DisplayName ServicePrincipalName
az ad sp create-for-rbac -n "postmanaccess"


#AZURE SCHEMA JSON
https://github.com/Azure/azure-resource-manager-schemas






======================================================================================
REST API NOT READY
$sp = New-AzADServicePrincipal -DisplayName ServicePrincipalName
az ad sp create-for-rbac -n "postmanaccess"

https://login.microsoftonline.com/{{tenantid}}/oauth2/token



pm.test(pm.info.requestName, () -> {
    pm.response.to.not.be.error;
    pm.response.to.not.have.jsonbody('error');
});
pm.globals.set("bearerToken", pm.response.json().access_token);



set header -
key: authorization
value: Bearer {{bearerToken}}
======================================================================================